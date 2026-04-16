SISTEMA DE GESTÃO DE MANUTENÇÃO E CONFIABILIDADE (STAR SCHEMA)
=============================================================================
Este script cria a estrutura de banco de dados para análise de ativos industriais.
/* =============================================================================
Ordem de execução: 
1. DIM_CALENDARIO (Independente)
2. DIM_ATIVOS (Depende de Calendário)
3. FATOS_NOTAS (Depende de Ativos e Calendário)
4. FATOS_ORDENS (Depende de Ativos e Calendário)
=============================================================================
*/

-- 1. DIMENSÃO CALENDÁRIO
-- Tabela central para inteligência de tempo (Time Intelligence). 
-- Permite análises por safra, mês, semana e dia da semana.
CREATE TABLE DIM_CALENDARIO (
    data DATE PRIMARY KEY,
    ano INT NOT NULL,
    mes INT NOT NULL,
    nome_mes VARCHAR(20),
    trimestre INT,
    nome_trimestre VARCHAR(5), -- Ex: T1, T2
    semana INT,
    dia INT NOT NULL,
    dia_semana VARCHAR(20),
    eh_fim_semana BOOLEAN,
    ano_mes VARCHAR(7) -- Ex: 2024-03
);

-- 2. DIMENSÃO ATIVOS
-- Cadastro técnico dos equipamentos e componentes.
-- Utiliza a 'tag' como chave primária para ligação com as tabelas de fatos.
CREATE TABLE DIM_ATIVOS (
    tag VARCHAR(50) PRIMARY KEY,
    id_ativo INT,
    tag_pai VARCHAR(50), -- Define a hierarquia (ex: motor dentro de uma bomba)
    nivel_taxonomia INT,
    classe_ativo VARCHAR(50), -- Ex: Bomba, Motor, Sensor
    nome VARCHAR(100),
    setor VARCHAR(10),
    setor_desc VARCHAR(50),
    criticidade CHAR(1), -- A, B ou C
    data_instalacao DATE,
    planta VARCHAR(10),
    -- Foreign Key para garantir que a data de instalação seja válida no calendário
    FOREIGN KEY (data_instalacao) REFERENCES DIM_CALENDARIO(data)
);

-- 3. FATOS NOTAS (NOTIFICAÇÕES)
-- Registra anomalias, defeitos e solicitações de serviço.
-- Liga-se ao Ativo via TAG e ao Calendário via Data de Notificação.
CREATE TABLE FATOS_NOTAS (
    id_notificacao INT PRIMARY KEY,
    tag_ativo VARCHAR(50) NOT NULL,
    data_notificacao DATE NOT NULL,
    tipo_manutencao VARCHAR(20), -- Ex: Corretiva, Preventiva
    modo_falha VARCHAR(100), -- Ex: Falha de rolamento, Curto-circuito
    descricao TEXT,
    FOREIGN KEY (tag_ativo) REFERENCES DIM_ATIVOS(tag),
    FOREIGN KEY (data_notificacao) REFERENCES DIM_CALENDARIO(data)
);

-- 4. FATOS ORDENS (ORDENS DE MANUTENÇÃO - OM)
-- Tabela de execução e custos. Concentra os principais KPIs (MTTR, Custos, Lead Time).
CREATE TABLE FATOS_ORDENS (
    id_om INT PRIMARY KEY,
    tag_ativo VARCHAR(50) NOT NULL,
    tipo_manutencao VARCHAR(20),
    atividade VARCHAR(100), -- Descrição do serviço realizado
    equipe VARCHAR(50),     -- Ex: Mecânica, Elétrica
    tecnico_responsavel VARCHAR(100),
    
    -- Datas para análise de ciclo de vida da ordem
    data_notificacao DATE,
    data_abertura_om DATE NOT NULL,
    data_inicio_execucao DATE,
    data_encerramento DATE,
    
    duracao_horas DECIMAL(10,2), -- Tempo de reparo ou execução
    custo_real DECIMAL(10,2),    -- Custo total (materiais + mão de obra)
    status VARCHAR(20),          -- Ex: Encerrada, Aberta, Cancelada
    
    -- Restrições de Integridade
    FOREIGN KEY (tag_ativo) REFERENCES DIM_ATIVOS(tag),
    FOREIGN KEY (data_notificacao) REFERENCES DIM_CALENDARIO(data),
    FOREIGN KEY (data_abertura_om) REFERENCES DIM_CALENDARIO(data),
    FOREIGN KEY (data_inicio_execucao) REFERENCES DIM_CALENDARIO(data),
    FOREIGN KEY (data_encerramento) REFERENCES DIM_CALENDARIO(data)
    
    
);




