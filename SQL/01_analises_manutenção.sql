/* =============================================================================
SISTEMA DE GESTÃO DE MANUTENÇÃO E CONFIABILIDADE (STAR SCHEMA)
=============================================================================
Este script executa e cria as seleções que serão utilizados pelo Power BI.
Desenvolvido para análise de performance de ativos industriais (SQLite).
=============================================================================
*/
 
/* =============================================================================
1 - MAPEAMENTO DO INVENTÁRIO DE ATIVOS
Visão completa da frota instalada na planta: composição por tipo de equipamento,
nível de criticidade operacional e distribuição por setor produtivo.
=============================================================================
*/
 
-- 1. Distribuição de ativos por categoria (ex: bombas, motores, redutores)
SELECT 
    classe_ativo, 
    COUNT(classe_ativo) AS total_ativos
FROM DIM_ATIVOS da
GROUP BY classe_ativo 
ORDER BY total_ativos DESC;
 
-- 2. Distribuição de ativos por criticidade (A, B, C)
SELECT 
    criticidade, 
    COUNT(criticidade) AS total_ativos
FROM DIM_ATIVOS da
GROUP BY criticidade  
ORDER BY total_ativos DESC;
 
-- 3. Distribuição de ativos por setor operacional
SELECT 
    da.setor_desc, 
    COUNT(da.setor_desc) AS total_ativos
FROM DIM_ATIVOS da
GROUP BY da.setor_desc   
ORDER BY total_ativos DESC;
 
 
/* =============================================================================
2 - DIAGNÓSTICO DE FALHAS E IDENTIFICAÇÃO DE BAD ACTORS
Ranking de equipamentos mais problemáticos e análise de Pareto por modo de falha.
Subsidia a priorização de ações corretivas e revisão de planos de manutenção.
=============================================================================
*/
 
-- 1. Ranking de notificações por ativo (Visão Geral)
SELECT
    fn.tag,
    COUNT(fn.tag) AS total_notas
FROM FATOS_NOTAS fn 
GROUP BY fn.tag
ORDER BY total_notas DESC;
 
-- 2. Análise de Pareto por Modo de Falha
SELECT
    fn.modo_falha, 
    COUNT(fn.modo_falha) AS total_falhas,
    SUM(COUNT(fn.modo_falha)) OVER (
        ORDER BY COUNT(fn.modo_falha) DESC, fn.modo_falha ASC
    ) AS soma_acumulada,
    ROUND(
        100.0 * SUM(COUNT(fn.modo_falha)) OVER (ORDER BY COUNT(fn.modo_falha) DESC, fn.modo_falha ASC) / 
        SUM(COUNT(fn.modo_falha)) OVER (), 
    2) AS percentual_acumulado
FROM FATOS_NOTAS fn 
GROUP BY fn.modo_falha 
ORDER BY total_falhas DESC, fn.modo_falha ASC;
 
-- 3. Top 10 Ativos Problemáticos por Classe (Sem Empates)
WITH ResumoFalhas AS (
    SELECT 
        da.classe_ativo,
        da.tag,
        COUNT(fn.tag) AS total_falhas
    FROM DIM_ATIVOS da
    LEFT JOIN FATOS_NOTAS fn ON da.tag = fn.tag
    GROUP BY 1, 2
),
RankingFinal AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY classe_ativo 
            ORDER BY total_falhas DESC, tag ASC
        ) AS ranking_na_classe
    FROM ResumoFalhas
)
SELECT * FROM RankingFinal
WHERE ranking_na_classe <= 10
ORDER BY classe_ativo, ranking_na_classe;
 
 
/* =============================================================================
3 - INDICADORES DE CONFIABILIDADE — MTBF, MTTR E DISPONIBILIDADE
Cálculos acumulados no tempo para acompanhar a evolução da performance dos ativos.
Permite identificar tendências de degradação e medir o impacto das intervenções.
=============================================================================
*/
 


/* =============================================================================
3.1 - DISPONIBILIDADE TRIMESTRAL POR ATIVO
Versão preliminar — replica as CTEs de MTBF (3.1) e MTTR (3.3) em bloco único
antes de serem refatoradas para views reutilizáveis na seção de views base.
============================================================================= */

WITH Fechamentos_Trimestre AS (
    SELECT ano, trimestre, nome_trimestre, MAX(data) AS data_corte
    FROM DIM_CALENDARIO WHERE data >= '2022-01-01'
    GROUP BY ano, trimestre, nome_trimestre
),
Base_Ativos_Trimestre AS (
    SELECT DISTINCT da.tag, da.classe_ativo, da.setor_desc, da.criticidade,
        ft.ano, ft.trimestre, ft.nome_trimestre, ft.data_corte, '2022-01-01' AS data_inicio
    FROM DIM_ATIVOS da CROSS JOIN Fechamentos_Trimestre ft
),
-- MTBF (3.1)
MTBF AS (
    SELECT bat.tag, bat.ano, bat.trimestre,
        COUNT(fn.data_notificacao) AS total_falhas,
        julianday(bat.data_corte) - julianday(bat.data_inicio) AS dias_acumulados
    FROM Base_Ativos_Trimestre bat
    LEFT JOIN FATOS_NOTAS fn ON fn.tag = bat.tag
        AND fn.data_notificacao >= bat.data_inicio AND fn.data_notificacao <= bat.data_corte
    GROUP BY bat.tag, bat.ano, bat.trimestre, bat.data_corte, bat.data_inicio
),
-- MTTR (3.3)
Corretivas_Por_Trimestre AS (
    SELECT fo.tag, dc.ano, dc.trimestre,
        COUNT(fo.id_om) AS qtd_corretivas, SUM(fo.duracao_horas) AS soma_duracao
    FROM FATOS_ORDENS fo JOIN DIM_CALENDARIO dc ON fo.data_encerramento = dc.data
    WHERE fo.tipo_manutencao = 'Corretiva' AND fo.status = 'Encerrada' AND fo.duracao_horas IS NOT NULL
    GROUP BY fo.tag, dc.ano, dc.trimestre
),
MTTR AS (
    SELECT bat.tag, bat.ano, bat.trimestre,
        SUM(COALESCE(cpt.soma_duracao,   0)) OVER (PARTITION BY bat.tag ORDER BY bat.ano, bat.trimestre) AS soma_duracao_acumulada,
        SUM(COALESCE(cpt.qtd_corretivas, 0)) OVER (PARTITION BY bat.tag ORDER BY bat.ano, bat.trimestre) AS qtd_corretivas_acumuladas
    FROM Base_Ativos_Trimestre bat
    LEFT JOIN Corretivas_Por_Trimestre cpt ON bat.tag = cpt.tag AND bat.ano = cpt.ano AND bat.trimestre = cpt.trimestre
)

SELECT
    bat.tag, bat.classe_ativo, bat.setor_desc, bat.criticidade,
    bat.ano, bat.trimestre, bat.nome_trimestre,
    ROUND(CASE WHEN mtbf.total_falhas = 0 THEN 0.0
               ELSE (mtbf.dias_acumulados / mtbf.total_falhas) * 24 END, 2) AS mtbf_acumulado_horas,
    ROUND(CASE WHEN mttr.qtd_corretivas_acumuladas = 0 THEN 0.0
               ELSE CAST(mttr.soma_duracao_acumulada AS FLOAT) / mttr.qtd_corretivas_acumuladas END, 2) AS mttr_acumulado_horas,
    ROUND(CASE
        WHEN mtbf.total_falhas = 0 OR mttr.qtd_corretivas_acumuladas = 0 THEN NULL
        ELSE 100.0 * (mtbf.dias_acumulados / mtbf.total_falhas * 24) /
                     (mtbf.dias_acumulados / mtbf.total_falhas * 24 +
                      CAST(mttr.soma_duracao_acumulada AS FLOAT) / mttr.qtd_corretivas_acumuladas)
    END, 2) AS disponibilidade_pct
FROM Base_Ativos_Trimestre bat
JOIN MTBF ON bat.tag = MTBF.tag AND bat.ano = MTBF.ano AND bat.trimestre = MTBF.trimestre
JOIN MTTR ON bat.tag = MTTR.tag AND bat.ano = MTTR.ano AND bat.trimestre = MTTR.trimestre
ORDER BY bat.tag, bat.ano, bat.trimestre;

/* =============================================================================
3.2 - DISPONIBILIDADE MENSAL POR CLASSE DE ATIVO
Versão preliminar — replica as CTEs de MTBF (3.2) e MTTR (3.4) em bloco único
antes de serem refatoradas para views reutilizáveis na seção de views base.
============================================================================= */

WITH Calendario_Mensal AS (
    SELECT ano, mes, nome_mes, ano_mes, COUNT(data) AS dias_no_mes
    FROM DIM_CALENDARIO WHERE data >= '2022-01-01'
    GROUP BY ano, mes, nome_mes, ano_mes
),
Base_Classes_Mes AS (
    SELECT da.classe_ativo,
        (SELECT COUNT(*) FROM DIM_ATIVOS WHERE classe_ativo = da.classe_ativo) AS qtd_ativos_na_classe,
        cm.ano, cm.mes, cm.nome_mes, cm.ano_mes, cm.dias_no_mes
    FROM (SELECT DISTINCT classe_ativo FROM DIM_ATIVOS) da CROSS JOIN Calendario_Mensal cm
),
Falhas_Por_Mes AS (
    SELECT da.classe_ativo, dc.ano_mes, COUNT(fn.id_notificacao) AS total_falhas_mes
    FROM FATOS_NOTAS fn
    JOIN DIM_ATIVOS da ON fn.tag = da.tag
    JOIN DIM_CALENDARIO dc ON fn.data_notificacao = dc.data
    GROUP BY da.classe_ativo, dc.ano_mes
),
Corretivas_Por_Mes AS (
    SELECT da.classe_ativo, dc.ano_mes,
        COUNT(fo.id_om) AS qtd_corretivas_mes, SUM(fo.duracao_horas) AS soma_duracao_mes
    FROM FATOS_ORDENS fo
    JOIN DIM_ATIVOS da ON fo.tag = da.tag
    JOIN DIM_CALENDARIO dc ON fo.data_encerramento = dc.data
    WHERE fo.tipo_manutencao = 'Corretiva' AND fo.status = 'Encerrada' AND fo.duracao_horas IS NOT NULL
    GROUP BY da.classe_ativo, dc.ano_mes
),
Acumulado AS (
    SELECT bcm.classe_ativo, bcm.ano, bcm.mes, bcm.nome_mes, bcm.ano_mes,
        SUM(bcm.dias_no_mes * bcm.qtd_ativos_na_classe) OVER (PARTITION BY bcm.classe_ativo ORDER BY bcm.ano, bcm.mes) AS tempo_disponivel_acumulado,
        SUM(COALESCE(fpm.total_falhas_mes,   0)) OVER (PARTITION BY bcm.classe_ativo ORDER BY bcm.ano, bcm.mes) AS total_falhas_acumuladas,
        SUM(COALESCE(cpm.soma_duracao_mes,   0)) OVER (PARTITION BY bcm.classe_ativo ORDER BY bcm.ano, bcm.mes) AS soma_duracao_acumulada,
        SUM(COALESCE(cpm.qtd_corretivas_mes, 0)) OVER (PARTITION BY bcm.classe_ativo ORDER BY bcm.ano, bcm.mes) AS qtd_corretivas_acumuladas
    FROM Base_Classes_Mes bcm
    LEFT JOIN Falhas_Por_Mes     fpm ON bcm.classe_ativo = fpm.classe_ativo AND bcm.ano_mes = fpm.ano_mes
    LEFT JOIN Corretivas_Por_Mes cpm ON bcm.classe_ativo = cpm.classe_ativo AND bcm.ano_mes = cpm.ano_mes
)

SELECT
    classe_ativo,
    ano_mes,
    nome_mes,
    total_falhas_acumuladas,
    ROUND(CASE WHEN total_falhas_acumuladas = 0 THEN 0.0
               ELSE (CAST(tempo_disponivel_acumulado AS FLOAT) / total_falhas_acumuladas) * 24
          END, 2) AS mtbf_acumulado_horas,
    ROUND(CASE WHEN qtd_corretivas_acumuladas = 0 THEN 0.0
               ELSE CAST(soma_duracao_acumulada AS FLOAT) / qtd_corretivas_acumuladas
          END, 2) AS mttr_acumulado_horas,
    ROUND(CASE
        WHEN total_falhas_acumuladas = 0 OR qtd_corretivas_acumuladas = 0 THEN 100
        ELSE 100.0 * (CAST(tempo_disponivel_acumulado AS FLOAT) / total_falhas_acumuladas * 24) /
                     (CAST(tempo_disponivel_acumulado AS FLOAT) / total_falhas_acumuladas * 24 +
                      CAST(soma_duracao_acumulada AS FLOAT) / qtd_corretivas_acumuladas)
    END, 2) AS disponibilidade_pct
FROM Acumulado
ORDER BY classe_ativo, ano, mes;



/* =============================================================================
   SEÇÃO 3 — VERSÃO REFATORADA: VIEWS BASE + QUERIES FINAIS
   As queries 3.1, 3.2 e 3.5 abaixo são a versão definitiva para o Power BI.
   As CTEs repetidas foram extraídas para views, eliminando redundância e
   facilitando manutenção futura do modelo.

   ESTRUTURA:
     Views base  → blocos reutilizáveis entre as queries abaixo
     Query 3.1   → Indicadores trimestrais por ativo
     Query 3.2   → Indicadores mensais por classe de ativo
     Query 3.5   → Indicadores mensais por ativo
============================================================================= */


/* =============================================================================
   VIEWS BASE — BLOCOS REUTILIZÁVEIS PARA CÁLCULO DE MTBF, MTTR E DISPONIBILIDADE
   Centralizam os cálculos repetidos entre as três queries.
   Criar uma vez — as queries apenas referenciam.
============================================================================= */

/* -------------------------------------------------------------------
   Agrupa o calendário por mês, contando os dias de cada período.
   Ponto de partida para calcular tempo disponível acumulado.
------------------------------------------------------------------- */
CREATE VIEW IF NOT EXISTS V_CALENDARIO_MENSAL AS
SELECT ano, mes, nome_mes, ano_mes, COUNT(data) AS dias_no_mes
FROM DIM_CALENDARIO
WHERE data >= '2022-01-01'
GROUP BY ano, mes, nome_mes, ano_mes;

/* -------------------------------------------------------------------
   Conta falhas por ativo e por mês.
   Filtra apenas notas corretivas — MTBF mede tempo entre falhas,
   e só corretivas representam um evento de falha real do ativo.
------------------------------------------------------------------- */
CREATE VIEW IF NOT EXISTS V_FALHAS_MES_TAG AS
SELECT fn.tag, dc.ano_mes,
    COUNT(fn.id_notificacao) AS total_falhas_mes
FROM FATOS_NOTAS fn
JOIN DIM_CALENDARIO dc ON fn.data_notificacao = dc.data
WHERE fn.tipo_manutencao = 'Corretiva'
GROUP BY fn.tag, dc.ano_mes;

/* -------------------------------------------------------------------
   Conta falhas por classe de ativo e por mês.
   Mesmo critério da view acima — apenas notas corretivas.
------------------------------------------------------------------- */
CREATE VIEW IF NOT EXISTS V_FALHAS_MES_CLASSE AS
SELECT da.classe_ativo, dc.ano_mes,
    COUNT(fn.id_notificacao) AS total_falhas_mes
FROM FATOS_NOTAS fn
JOIN DIM_ATIVOS     da ON fn.tag              = da.tag
JOIN DIM_CALENDARIO dc ON fn.data_notificacao = dc.data
WHERE fn.tipo_manutencao = 'Corretiva'
GROUP BY da.classe_ativo, dc.ano_mes;

/* -------------------------------------------------------------------
   Soma horas e conta ordens corretivas encerradas por ativo e mês.
   Base do MTTR nas queries por ativo (3.1 e 3.5).
   Exclui ordens sem duração para não distorcer a média de reparo.
------------------------------------------------------------------- */
CREATE VIEW IF NOT EXISTS V_CORRETIVAS_MES_TAG AS
SELECT fo.tag, dc.ano_mes,
    COUNT(fo.id_om)       AS qtd_corretivas_mes,
    SUM(fo.duracao_horas) AS soma_duracao_mes
FROM FATOS_ORDENS fo
JOIN DIM_CALENDARIO dc ON fo.data_encerramento = dc.data
WHERE fo.tipo_manutencao = 'Corretiva'
  AND fo.status          = 'Encerrada'
  AND fo.duracao_horas  IS NOT NULL
GROUP BY fo.tag, dc.ano_mes;

/* -------------------------------------------------------------------
   Soma horas e conta ordens corretivas encerradas por classe e mês.
   Base do MTTR na query por classe (3.2).
------------------------------------------------------------------- */
CREATE VIEW IF NOT EXISTS V_CORRETIVAS_MES_CLASSE AS
SELECT da.classe_ativo, dc.ano_mes,
    COUNT(fo.id_om)       AS qtd_corretivas_mes,
    SUM(fo.duracao_horas) AS soma_duracao_mes
FROM FATOS_ORDENS fo
JOIN DIM_ATIVOS     da ON fo.tag              = da.tag
JOIN DIM_CALENDARIO dc ON fo.data_encerramento = dc.data
WHERE fo.tipo_manutencao = 'Corretiva'
  AND fo.status          = 'Encerrada'
  AND fo.duracao_horas  IS NOT NULL
GROUP BY da.classe_ativo, dc.ano_mes;


/* =============================================================================
   3.1 — CONFIABILIDADE TRIMESTRAL POR ATIVO (VERSÃO DEFINITIVA)
   Granularidade: um registro por ativo × trimestre.
   Todos os valores são acumulados desde jan/2022.
============================================================================= */

WITH

/* Pega a última data de cada trimestre — será o ponto de corte
   para contar falhas e calcular dias acumulados via julianday.   */
Fechamentos_Trimestre AS (
    SELECT ano, trimestre, nome_trimestre, MAX(data) AS data_corte
    FROM DIM_CALENDARIO WHERE data >= '2022-01-01'
    GROUP BY ano, trimestre, nome_trimestre
),

/* Produto cartesiano ativo × trimestre, garantindo linha para
   todo ativo em todo trimestre, mesmo sem eventos registrados.  */
Base AS (
    SELECT DISTINCT
        da.tag, da.classe_ativo, da.setor_desc, da.criticidade,
        ft.ano, ft.trimestre, ft.nome_trimestre,
        ft.data_corte, '2022-01-01' AS data_inicio
    FROM DIM_ATIVOS da CROSS JOIN Fechamentos_Trimestre ft
),

/* MTBF — acumula apenas falhas corretivas e dias desde data_inicio
   até data_corte de cada trimestre. julianday converte em dias.  */
MTBF AS (
    SELECT b.tag, b.ano, b.trimestre,
        COUNT(fn.data_notificacao)                           AS total_falhas,
        julianday(b.data_corte) - julianday(b.data_inicio)   AS dias_acumulados
    FROM Base b
    LEFT JOIN FATOS_NOTAS fn
           ON fn.tag = b.tag
          AND fn.data_notificacao BETWEEN b.data_inicio AND b.data_corte
          AND fn.tipo_manutencao = 'Corretiva'
    GROUP BY b.tag, b.ano, b.trimestre, b.data_corte, b.data_inicio
),

/* MTTR — acumula horas e ordens corretivas trimestralmente
   usando window function, da mesma forma que nas queries mensais. */
Corretivas_Trimestre AS (
    SELECT fo.tag, dc.ano, dc.trimestre,
        COUNT(fo.id_om)       AS qtd_corretivas,
        SUM(fo.duracao_horas) AS soma_duracao
    FROM FATOS_ORDENS fo
    JOIN DIM_CALENDARIO dc ON fo.data_encerramento = dc.data
    WHERE fo.tipo_manutencao = 'Corretiva'
      AND fo.status          = 'Encerrada'
      AND fo.duracao_horas  IS NOT NULL
    GROUP BY fo.tag, dc.ano, dc.trimestre
),
MTTR AS (
    SELECT b.tag, b.ano, b.trimestre,
        SUM(COALESCE(ct.soma_duracao,   0))
            OVER (PARTITION BY b.tag ORDER BY b.ano, b.trimestre) AS soma_duracao_acumulada,
        SUM(COALESCE(ct.qtd_corretivas, 0))
            OVER (PARTITION BY b.tag ORDER BY b.ano, b.trimestre) AS qtd_corretivas_acumuladas
    FROM Base b
    LEFT JOIN Corretivas_Trimestre ct
           ON b.tag = ct.tag AND b.ano = ct.ano AND b.trimestre = ct.trimestre
)

/*  MTBF  = (dias acumulados / nº falhas) × 24  → horas entre falhas
    MTTR  = horas acumuladas / nº ordens        → horas médias de reparo
    DISP  = MTBF / (MTBF + MTTR) × 100         → % tempo operacional   */
SELECT
    b.tag, b.classe_ativo, b.setor_desc, b.criticidade,
    b.ano, b.trimestre, b.nome_trimestre,
    ROUND(CASE WHEN mtbf.total_falhas = 0 THEN 0.0
               ELSE (mtbf.dias_acumulados / mtbf.total_falhas) * 24
          END, 2) AS mtbf_acumulado_horas,
    ROUND(CASE WHEN mttr.qtd_corretivas_acumuladas = 0 THEN 0.0
               ELSE CAST(mttr.soma_duracao_acumulada AS FLOAT) / mttr.qtd_corretivas_acumuladas
          END, 2) AS mttr_acumulado_horas,
    ROUND(CASE
        WHEN mtbf.total_falhas = 0
          OR mttr.qtd_corretivas_acumuladas = 0 THEN NULL
        ELSE 100.0 * (mtbf.dias_acumulados / mtbf.total_falhas * 24)
                   / (mtbf.dias_acumulados / mtbf.total_falhas * 24
                      + CAST(mttr.soma_duracao_acumulada AS FLOAT) / mttr.qtd_corretivas_acumuladas)
    END, 2) AS disponibilidade_pct
FROM Base b
JOIN MTBF ON b.tag = MTBF.tag AND b.ano = MTBF.ano AND b.trimestre = MTBF.trimestre
JOIN MTTR ON b.tag = MTTR.tag AND b.ano = MTTR.ano AND b.trimestre = MTTR.trimestre
ORDER BY b.tag, b.ano, b.trimestre;


/* =============================================================================
   3.2 — CONFIABILIDADE MENSAL POR CLASSE DE ATIVO (VERSÃO DEFINITIVA)
   Granularidade: um registro por classe × mês.
   O tempo disponível considera todos os ativos da classe (qtd × dias).
============================================================================= */

WITH

/* Produto cartesiano classe × mês. qtd_ativos_na_classe multiplica
   os dias do mês para refletir o tempo total disponível da frota.  */
Base AS (
    SELECT
        da.classe_ativo,
        (SELECT COUNT(*) FROM DIM_ATIVOS
         WHERE classe_ativo = da.classe_ativo) AS qtd_ativos_na_classe,
        cm.ano, cm.mes, cm.nome_mes, cm.ano_mes, cm.dias_no_mes
    FROM (SELECT DISTINCT classe_ativo FROM DIM_ATIVOS) da
    CROSS JOIN V_CALENDARIO_MENSAL cm
),

/* Acumula todas as métricas mês a mês via window function.
   COALESCE zera meses sem eventos para não quebrar o acumulado. */
Acumulado AS (
    SELECT
        b.classe_ativo, b.ano, b.mes, b.nome_mes, b.ano_mes,
        SUM(b.dias_no_mes * b.qtd_ativos_na_classe)
            OVER (PARTITION BY b.classe_ativo ORDER BY b.ano, b.mes) AS tempo_disponivel_acumulado,
        SUM(COALESCE(f.total_falhas_mes,   0))
            OVER (PARTITION BY b.classe_ativo ORDER BY b.ano, b.mes) AS total_falhas_acumuladas,
        SUM(COALESCE(c.soma_duracao_mes,   0))
            OVER (PARTITION BY b.classe_ativo ORDER BY b.ano, b.mes) AS soma_duracao_acumulada,
        SUM(COALESCE(c.qtd_corretivas_mes, 0))
            OVER (PARTITION BY b.classe_ativo ORDER BY b.ano, b.mes) AS qtd_corretivas_acumuladas
    FROM Base b
    LEFT JOIN V_FALHAS_MES_CLASSE     f ON b.classe_ativo = f.classe_ativo AND b.ano_mes = f.ano_mes
    LEFT JOIN V_CORRETIVAS_MES_CLASSE c ON b.classe_ativo = c.classe_ativo AND b.ano_mes = c.ano_mes
)

/*  MTBF  = (tempo disponível acumulado / nº falhas) × 24
    MTTR  = horas acumuladas / nº ordens
    DISP  = MTBF / (MTBF + MTTR) × 100
    → 100% quando sem falhas ou sem reparos registrados no período. */
SELECT
    classe_ativo, ano_mes, nome_mes,
    total_falhas_acumuladas,
    ROUND(CASE WHEN total_falhas_acumuladas = 0 THEN 0.0
               ELSE (CAST(tempo_disponivel_acumulado AS FLOAT) / total_falhas_acumuladas) * 24
          END, 2) AS mtbf_acumulado_horas,
    ROUND(CASE WHEN qtd_corretivas_acumuladas = 0 THEN 0.0
               ELSE CAST(soma_duracao_acumulada AS FLOAT) / qtd_corretivas_acumuladas
          END, 2) AS mttr_acumulado_horas,
    ROUND(CASE
        WHEN total_falhas_acumuladas = 0
          OR qtd_corretivas_acumuladas = 0 THEN 100
        ELSE 100.0
             * (CAST(tempo_disponivel_acumulado AS FLOAT) / total_falhas_acumuladas * 24)
             / (CAST(tempo_disponivel_acumulado AS FLOAT) / total_falhas_acumuladas * 24
                + CAST(soma_duracao_acumulada AS FLOAT) / qtd_corretivas_acumuladas)
    END, 2) AS disponibilidade_pct
FROM Acumulado
ORDER BY classe_ativo, ano, mes;


/* =============================================================================
   3.5 — CONFIABILIDADE MENSAL POR ATIVO (VERSÃO DEFINITIVA)
   Granularidade: um registro por ativo × mês.
   Diferente da 3.2, o tempo disponível considera apenas o ativo (1 × dias).
============================================================================= */

WITH

/* Produto cartesiano ativo × mês. Garante linha para todo ativo
   em todo mês, mesmo sem falhas ou ordens no período.            */
Base AS (
    SELECT
        da.tag, da.classe_ativo, da.setor_desc, da.criticidade,
        cm.ano, cm.mes, cm.nome_mes, cm.ano_mes, cm.dias_no_mes
    FROM DIM_ATIVOS da CROSS JOIN V_CALENDARIO_MENSAL cm
),

/* Acumula todas as métricas mês a mês via window function.
   COALESCE zera meses sem eventos para não quebrar o acumulado. */
Acumulado AS (
    SELECT
        b.tag, b.classe_ativo, b.setor_desc, b.criticidade,
        b.ano, b.mes, b.nome_mes, b.ano_mes,
        SUM(b.dias_no_mes)
            OVER (PARTITION BY b.tag ORDER BY b.ano, b.mes) AS tempo_disponivel_acumulado,
        SUM(COALESCE(f.total_falhas_mes,   0))
            OVER (PARTITION BY b.tag ORDER BY b.ano, b.mes) AS total_falhas_acumuladas,
        SUM(COALESCE(c.soma_duracao_mes,   0))
            OVER (PARTITION BY b.tag ORDER BY b.ano, b.mes) AS soma_duracao_acumulada,
        SUM(COALESCE(c.qtd_corretivas_mes, 0))
            OVER (PARTITION BY b.tag ORDER BY b.ano, b.mes) AS qtd_corretivas_acumuladas
    FROM Base b
    LEFT JOIN V_FALHAS_MES_TAG     f ON b.tag = f.tag AND b.ano_mes = f.ano_mes
    LEFT JOIN V_CORRETIVAS_MES_TAG c ON b.tag = c.tag AND b.ano_mes = c.ano_mes
)

/*  MTBF  = (tempo disponível acumulado / nº falhas) × 24
    MTTR  = horas acumuladas / nº ordens
    DISP  = MTBF / (MTBF + MTTR) × 100
    → 100% quando sem falhas ou sem reparos registrados no período. */
SELECT
    tag, classe_ativo, setor_desc, criticidade,
    ano, mes, nome_mes, ano_mes,
    total_falhas_acumuladas,
    ROUND(soma_duracao_acumulada, 2)                                     AS soma_duracao_acumulada_horas,
    ROUND(CASE WHEN total_falhas_acumuladas = 0 THEN 0.0
               ELSE (CAST(tempo_disponivel_acumulado AS FLOAT) / total_falhas_acumuladas) * 24
          END, 2)                                                        AS mtbf_acumulado_horas,
    ROUND(CASE WHEN qtd_corretivas_acumuladas = 0 THEN 0.0
               ELSE CAST(soma_duracao_acumulada AS FLOAT) / qtd_corretivas_acumuladas
          END, 2)                                                        AS mttr_acumulado_horas,
    ROUND(CASE
        WHEN total_falhas_acumuladas = 0
          OR qtd_corretivas_acumuladas = 0 THEN 100
        ELSE 100.0
             * (CAST(tempo_disponivel_acumulado AS FLOAT) / total_falhas_acumuladas * 24)
             / (CAST(tempo_disponivel_acumulado AS FLOAT) / total_falhas_acumuladas * 24
                + CAST(soma_duracao_acumulada AS FLOAT) / qtd_corretivas_acumuladas)
    END, 2)                                                              AS disponibilidade_pct
FROM Acumulado
ORDER BY tag, ano, mes;

/* =============================================================================
4 - GESTÃO DE CUSTOS DE MANUTENÇÃO — REALIZADO VS ORÇADO
Acompanhamento do gasto mensal e acumulado por tipo de manutenção,
com comparativo direto ao orçamento anual para controle de desvios.
=============================================================================

/* =============================================================================
4.1 - CUSTO MENSAL E ACUMULADO POR CLASSE, SETOR E TIPO DE MANUTENÇÃO
      COM COMPARATIVO AO ORÇAMENTO ANUAL
============================================================================= */

WITH Calendario_Mensal AS (
    SELECT ano, mes, nome_mes, ano_mes
    FROM DIM_CALENDARIO WHERE data >= '2022-01-01'
    GROUP BY ano, mes, nome_mes, ano_mes
),

Base_Classes_Mes AS (
    SELECT DISTINCT da.classe_ativo, da.setor_desc,
        cm.ano, cm.mes, cm.nome_mes, cm.ano_mes
    FROM DIM_ATIVOS da CROSS JOIN Calendario_Mensal cm
),

Custos_Por_Mes AS (
    SELECT
        da.classe_ativo,
        da.setor_desc,
        fo.tipo_manutencao,
        dc.ano_mes,
        COUNT(fo.id_om)    AS qtd_ordens,
        SUM(fo.custo_real) AS custo_mes
    FROM FATOS_ORDENS fo
    JOIN DIM_ATIVOS     da ON fo.tag              = da.tag
    JOIN DIM_CALENDARIO dc ON fo.data_encerramento = dc.data
    WHERE fo.status = 'Encerrada' AND fo.custo_real IS NOT NULL
    GROUP BY da.classe_ativo, da.setor_desc, fo.tipo_manutencao, dc.ano_mes
),

Acumulado AS (
    SELECT
        bcm.classe_ativo, bcm.setor_desc,
        bcm.ano, bcm.mes, bcm.nome_mes, bcm.ano_mes,
        cpm.tipo_manutencao,
        COALESCE(cpm.qtd_ordens, 0) AS qtd_ordens_mes,
        COALESCE(cpm.custo_mes,  0) AS custo_mes,
        SUM(COALESCE(cpm.custo_mes, 0)) OVER (
            PARTITION BY bcm.classe_ativo, bcm.setor_desc, cpm.tipo_manutencao
            ORDER BY bcm.ano, bcm.mes
        ) AS custo_acumulado
    FROM Base_Classes_Mes bcm
    LEFT JOIN Custos_Por_Mes cpm
           ON bcm.classe_ativo = cpm.classe_ativo
          AND bcm.setor_desc   = cpm.setor_desc
          AND bcm.ano_mes      = cpm.ano_mes
)

SELECT
    classe_ativo, setor_desc, tipo_manutencao,
    ano_mes, nome_mes, ano, mes,
    qtd_ordens_mes,
    ROUND(custo_mes,      2) AS custo_mes,
    ROUND(custo_acumulado, 2) AS custo_acumulado,
    CASE
        WHEN ano = 2022 AND tipo_manutencao = 'Corretiva'  THEN 130000.0
        WHEN ano = 2022 AND tipo_manutencao = 'Preventiva' THEN 105000.0
        WHEN ano = 2022 AND tipo_manutencao = 'Preditiva'  THEN 0.0
        WHEN ano = 2023 AND tipo_manutencao = 'Corretiva'  THEN 141000.0
        WHEN ano = 2023 AND tipo_manutencao = 'Preventiva' THEN 119000.0
        WHEN ano = 2023 AND tipo_manutencao = 'Preditiva'  THEN 0.0
        WHEN ano = 2024 AND tipo_manutencao = 'Corretiva'  THEN 280000.0
        WHEN ano = 2024 AND tipo_manutencao = 'Preventiva' THEN 116000.0
        WHEN ano = 2024 AND tipo_manutencao = 'Preditiva'  THEN 20000.0
    END AS custo_orcado_ano
FROM Acumulado
WHERE tipo_manutencao IS NOT NULL
ORDER BY classe_ativo, setor_desc, tipo_manutencao, ano, mes;

/* =============================================================================
4.3 - CUSTO MENSAL E ACUMULADO POR ATIVO (TAG)
      RASTREABILIDADE INDIVIDUAL DE GASTOS AO LONGO DO TEMPO
Gera uma linha por ativo em cada mês, permitindo identificar equipamentos
com custo crescente e subsidiar decisões de substituição ou reforma.
============================================================================= */

WITH Calendario_Mensal AS (
    -- Gera a lista de todos os meses desde o início da operação
    SELECT ano, mes, nome_mes, ano_mes
    FROM DIM_CALENDARIO 
    WHERE data >= '2022-01-01'
    GROUP BY ano, mes, nome_mes, ano_mes
),

Base_Ativos_Mes AS (
    -- Cross Join para garantir que todo Ativo tenha uma linha em todo mês
    SELECT 
        da.tag, 
        da.classe_ativo, 
        da.setor_desc,
        cm.ano, 
        cm.mes, 
        cm.nome_mes, 
        cm.ano_mes
    FROM DIM_ATIVOS da 
    CROSS JOIN Calendario_Mensal cm
),

Custos_Por_Mes_Ativo AS (
    -- Soma os custos reais por tag e por mês
    SELECT
        fo.tag,
        dc.ano_mes,
        SUM(fo.custo_real) AS custo_mes
    FROM FATOS_ORDENS fo
    JOIN DIM_CALENDARIO dc ON fo.data_encerramento = dc.data
    WHERE fo.status = 'Encerrada' 
      AND fo.custo_real IS NOT NULL
    GROUP BY fo.tag, dc.ano_mes
),

Calculo_Acumulado AS (
    -- Une a base completa com os custos e calcula a janela (Window Function)
    SELECT
        bam.tag,
        bam.classe_ativo,
        bam.setor_desc,
        bam.ano_mes,
        bam.nome_mes,
        COALESCE(cpm.custo_mes, 0) AS custo_mes,
        SUM(COALESCE(cpm.custo_mes, 0)) OVER (
            PARTITION BY bam.tag 
            ORDER BY bam.ano_mes
        ) AS custo_acumulado
    FROM Base_Ativos_Mes bam
    LEFT JOIN Custos_Por_Mes_Ativo cpm 
           ON bam.tag = cpm.tag 
          AND bam.ano_mes = cpm.ano_mes
)

SELECT
    tag,
    classe_ativo,
    setor_desc,
    ano_mes,
    nome_mes,
    ROUND(custo_mes, 2) AS custo_mes,
    ROUND(custo_acumulado, 2) AS custo_acumulado
FROM Calculo_Acumulado
ORDER BY tag, ano_mes;


/* =============================================================================
5 - GESTÃO OPERACIONAL — ORDENS DE MANUTENÇÃO, BACKLOG E PRODUTIVIDADE DAS EQUIPES
Monitora o fluxo de trabalho da manutenção: volume de ordens abertas e executadas,
acúmulo de backlog ao longo do tempo e capacidade de resposta de cada equipe.
=============================================================================

/* =============================================================================
5.1 - BACKLOG SEMANAL — HORAS PLANEJADAS VS EXECUTADAS POR EQUIPE
      SALDO ACUMULADO PARA IDENTIFICAR SOBRECARGA OU FOLGA OPERACIONAL
============================================================================= */

WITH

Semanas AS (
    SELECT DISTINCT
        ano, semana,
        ano || '-W' || printf('%02d', semana) AS ano_semana
    FROM DIM_CALENDARIO
    WHERE data >= '2022-01-01'
),

Planejadas AS (
    SELECT
        dc.ano, dc.semana,
        dc.ano || '-W' || printf('%02d', dc.semana) AS ano_semana,
        fo.tipo_manutencao,
        fo.equipe,
        COUNT(fo.id_om)        AS qtd_planejadas,
        SUM(fo.duracao_horas)  AS horas_planejadas
    FROM FATOS_ORDENS fo
    JOIN DIM_CALENDARIO dc ON fo.data_abertura_om = dc.data
    WHERE fo.data_abertura_om >= '2022-01-01'
      AND fo.duracao_horas IS NOT NULL
    GROUP BY dc.ano, dc.semana, fo.tipo_manutencao, fo.equipe
),

Executadas AS (
    SELECT
        dc.ano, dc.semana,
        dc.ano || '-W' || printf('%02d', dc.semana) AS ano_semana,
        fo.tipo_manutencao,
        fo.equipe,
        COUNT(fo.id_om)        AS qtd_executadas,
        SUM(fo.duracao_horas)  AS horas_executadas
    FROM FATOS_ORDENS fo
    JOIN DIM_CALENDARIO dc ON fo.data_inicio_execucao = dc.data
    WHERE fo.data_inicio_execucao >= '2022-01-01'
      AND fo.duracao_horas IS NOT NULL
    GROUP BY dc.ano, dc.semana, fo.tipo_manutencao, fo.equipe
),

Base AS (
    SELECT DISTINCT
        s.ano, s.semana, s.ano_semana,
        t.tipo_manutencao,
        e.equipe
    FROM Semanas s
    CROSS JOIN (SELECT DISTINCT tipo_manutencao FROM FATOS_ORDENS) t
    CROSS JOIN (SELECT DISTINCT equipe FROM FATOS_ORDENS) e
),

Juncao AS (
    SELECT
        b.ano, b.semana, b.ano_semana,
        b.tipo_manutencao,
        b.equipe,
        COALESCE(p.qtd_planejadas,  0) AS qtd_planejadas,
        COALESCE(e.qtd_executadas,  0) AS qtd_executadas,
        COALESCE(p.horas_planejadas, 0) AS horas_planejadas,
        COALESCE(e.horas_executadas, 0) AS horas_executadas
    FROM Base b
    LEFT JOIN Planejadas p
           ON b.ano_semana      = p.ano_semana
          AND b.tipo_manutencao = p.tipo_manutencao
          AND b.equipe          = p.equipe
    LEFT JOIN Executadas e
           ON b.ano_semana      = e.ano_semana
          AND b.tipo_manutencao = e.tipo_manutencao
          AND b.equipe          = e.equipe
)

SELECT
    ano, semana, ano_semana,
    tipo_manutencao,
    equipe,
    qtd_planejadas,
    qtd_executadas,
    ROUND(horas_planejadas, 2) AS horas_planejadas,
    ROUND(horas_executadas, 2) AS horas_executadas,
    ROUND(horas_planejadas - horas_executadas, 2) AS saldo_horas,
    ROUND(SUM(horas_planejadas - horas_executadas)
        OVER (PARTITION BY tipo_manutencao, equipe
              ORDER BY ano, semana), 2) AS backlog_horas_acumulado
FROM Juncao
ORDER BY equipe, tipo_manutencao, ano, semana;

/* =============================================================================
5.2 - PAINEL OPERACIONAL MENSAL — VOLUME DE ORDENS, BACKLOG E TEMPO DE RESOLUÇÃO
      VISÃO CONSOLIDADA POR EQUIPE E TIPO DE MANUTENÇÃO
============================================================================= */

WITH Base AS (
    SELECT
        fo.id_om,
        fo.tipo_manutencao,
        fo.equipe,
        fo.status,
        fo.data_abertura_om,
        fo.data_encerramento,
        dc_ab.ano_mes                      AS ano_mes_abertura,
        -- Último dia do mês de abertura
        date(fo.data_abertura_om, 'start of month', '+1 month', '-1 day') AS ultimo_dia_mes,
        
        -- Cálculo de dias para ordens ENCERRADAS
        CAST(julianday(fo.data_encerramento) - julianday(fo.data_abertura_om) AS INTEGER) AS dias_resolucao,
        
        -- Flag para fechadas no mesmo mês
        CASE 
            WHEN fo.status = 'Encerrada' 
             AND strftime('%Y-%m', fo.data_encerramento) = dc_ab.ano_mes 
            THEN 1 ELSE 0 
        END AS fechada_no_mes,

        -- CORREÇÃO DO BACKLOG:
        -- Se não fechou no mês, calculamos a idade até o último dia do mês.
        -- Adicionamos +1 para que ordens abertas no último dia contem como 1 dia de vida (evita o 0.0)
        CASE 
            WHEN (fo.status != 'Encerrada') 
              OR (strftime('%Y-%m', fo.data_encerramento) > dc_ab.ano_mes)
            THEN CAST(julianday(date(fo.data_abertura_om, 'start of month', '+1 month', '-1 day')) 
                 - julianday(fo.data_abertura_om) AS INTEGER) + 1
            ELSE NULL
        END AS idade_backlog_ajustada
    FROM FATOS_ORDENS fo
    JOIN DIM_CALENDARIO dc_ab ON fo.data_abertura_om = dc_ab.data
    WHERE fo.data_abertura_om >= '2022-01-01'
)

SELECT
    substr(ano_mes_abertura, 1, 4)         AS ano,
    CAST(substr(ano_mes_abertura, 6, 2) AS INT) AS mes,
    ano_mes_abertura                       AS ano_mes,
    tipo_manutencao,
    equipe,

    -- Volume
    COUNT(id_om)                           AS qtd_ordens_abertas,
    SUM(fechada_no_mes)                    AS qtd_fechadas_no_mes,
    COUNT(id_om) - SUM(fechada_no_mes)     AS qtd_backlog,

    -- Médias
    COALESCE(ROUND(AVG(CASE WHEN status = 'Encerrada' THEN dias_resolucao END), 1), 0) AS media_dias_resolucao,
    
    -- Agora a média de idade não será mais zero se houver backlog!
    COALESCE(ROUND(AVG(idade_backlog_ajustada), 1), 0) AS media_idade_backlog_dias

FROM Base
GROUP BY ano_mes_abertura, tipo_manutencao, equipe
ORDER BY ano_mes_abertura, tipo_manutencao, equipe;
