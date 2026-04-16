# =============================================================================
# GERAÇÃO DE NOTIFICAÇÕES 2024 — CORRETIVAS + PREDITIVAS
# Fábrica fictícia de água mineral - Planta 1 (pl1)
# =============================================================================
# Em 2024 a planta implanta rotina de análise de vibração preditiva
# cobrindo Motores Elétricos, Bombas e Redutores.
#
# Lógica:
#   1. Gera falhas normalmente para todos os ativos (igual 2021-2023)
#      porém com qtd_falhas proporcional a 1 ano (não 3)
#   2. Para ativos cobertos pela preditiva (Motor, Bomba, Redutor):
#      - Para cada falha, sorteia se seria detectável por vibração
#        (baseado no modo de falha e prob. de detecção)
#      - Se detectável: falha vira notificação PREDITIVA (incipiente)
#        e a corretiva NÃO ocorre
#      - Se não detectável: corretiva ocorre normalmente
#   3. Gera também as rotas de inspeção preditiva periódicas
#      (passagens de rotina que não encontraram nada — também são registradas)
#
# Frequência da rota preditiva:
#   Criticidade A → 15 dias
#   Criticidade B → 30 dias
#   Criticidade C → 30 dias
#
# Detectabilidade por modo de falha (vibração):
#   Motor:   rolamento 80%, mecânica 75%, enrolamento 20%, outros 0%
#   Bomba:   rolamento 80%, desalinhamento 85%, cavitação 65%, bloqueio 25%, outros 0%
#   Redutor: engrenagem 70%, rolamento 80%, eixo 60%, outros 0%
#
# Inputs:  BASE-ATIVOS-LIMPO.csv
# Outputs: NOTIFICACOES-2024.csv
# =============================================================================

import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta

fake = Faker('pt_BR')
np.random.seed(2024)

DATA_INICIO  = datetime(2024, 1, 1)
DATA_FIM     = datetime(2024, 12, 31)
PERIODO_DIAS = (DATA_FIM - DATA_INICIO).days  # 365 dias

# =============================================================================
# 1. CARREGA ATIVOS
# =============================================================================

df_ativos = pd.read_csv('/home/claude/BASE-ATIVOS-LIMPO.csv')
print(f"Ativos carregados: {len(df_ativos)}")

# =============================================================================
# 2. PARÂMETROS DE FALHA (mesmos de antes, qtd_falhas ajustada pra 1 ano)
# =============================================================================
# qtd_falhas original era para 3 anos → divide por 3 para 1 ano
# Aumenta levemente pois desgaste acumula (fator 1.1)

PARAMS_FALHA = {
    'Motor Elétrico': {
        'pf': 0.50, 'beta_inf': 1.8, 'beta_sup': 3.0,
        'qtd_falhas': round(77 / 3 * 1.1),  # ~28
        'modos': [
            ('Falha de rolamento',                 0.45),
            ('Falha de enrolamento / isolação',    0.25),
            ('Falha mecânica (eixo/acoplamento)',  0.12),
            ('Contaminação / umidade',             0.10),
            ('Superaquecimento',                   0.08),
        ]
    },
    'Sensor': {
        'pf': 0.20, 'beta_inf': 0.8, 'beta_sup': 1.2,
        'qtd_falhas': round(30 / 3 * 1.1),  # ~11
        'modos': [
            ('Deriva de sinal / perda de calibração', 0.35),
            ('Falha de conexão elétrica',             0.25),
            ('Dano físico (vibração/impacto)',        0.20),
            ('Falha de componente eletrônico',        0.12),
            ('Contaminação (poeira, umidade)',        0.08),
        ]
    },
    'Válvula': {
        'pf': 0.50, 'beta_inf': 1.5, 'beta_sup': 2.5,
        'qtd_falhas': round(35 / 3 * 1.1),  # ~13
        'modos': [
            ('Vazamento interno / externo',            0.38),
            ('Falha ao abrir/fechar sob demanda',      0.28),
            ('Falha de curso parcial',                 0.16),
            ('Corrosão / erosão',                      0.12),
            ('Travamento mecânico / atrito excessivo', 0.06),
        ]
    },
    'Bomba': {
        'pf': 0.80, 'beta_inf': 0.9, 'beta_sup': 1.5,
        'qtd_falhas': round(56 / 3 * 1.1),  # ~21
        'modos': [
            ('Falha de selo mecânico / vazamento',    0.40),
            ('Falha de rolamento',                    0.25),
            ('Dano ao impelidor (erosão/cavitação)',  0.15),
            ('Bloqueio / restrição de fluxo',         0.12),
            ('Desalinhamento de eixo / vibração',     0.08),
        ]
    },
    'Inversor de Frequência': {
        'pf': 0.10, 'beta_inf': 0.8, 'beta_sup': 1.2,
        'qtd_falhas': round(4 / 3 * 1.1),  # ~2
        'modos': [
            ('Falha do módulo IGBT',                         0.38),
            ('Degradação do capacitor (barramento DC)',      0.22),
            ('Superaquecimento / bloqueio do resfriamento',  0.18),
            ('Falha da placa de controle / firmware',        0.12),
            ('Falha do retificador de entrada',              0.10),
        ]
    },
    'Esteira': {
        'pf': 0.30, 'beta_inf': 1.5, 'beta_sup': 2.5,
        'qtd_falhas': round(6 / 3 * 1.1),  # ~2
        'modos': [
            ('Falha de caixa de redução (desgaste de dentes)', 0.35),
            ('Falha de rolamento (polias/acionamento)',         0.28),
            ('Desgaste / dano estrutural da correia',          0.20),
            ('Falha elétrica do motor',                        0.10),
            ('Dano em acoplamento / eixo',                     0.07),
        ]
    },
    'Compressor': {
        'pf': 0.20, 'beta_inf': 1.2, 'beta_sup': 2.5,
        'qtd_falhas': round(3 / 3 * 1.1),  # ~1
        'modos': [
            ('Falha de rolamento',                   0.35),
            ('Falha de válvula (sucção/descarga)',   0.25),
            ('Vazamento de vedação / gaxeta',        0.18),
            ('Dano ao rotor / impelidor',            0.12),
            ('Falha do sistema de resfriamento',     0.10),
        ]
    },
    'Redutor': {
        'pf': 0.50, 'beta_inf': 2.0, 'beta_sup': 3.5,
        'qtd_falhas': round(23 / 3 * 1.1),  # ~8
        'modos': [
            ('Fadiga / micropitting de dente de engrenagem', 0.40),
            ('Falha de rolamento',                           0.30),
            ('Falha de eixo',                                0.15),
            ('Vazamento de vedação / óleo',                  0.10),
            ('Dano ao cárter / carcaça',                     0.05),
        ]
    },
    'Robô': {
        'pf': 0.15, 'beta_inf': 1.0, 'beta_sup': 2.5,
        'qtd_falhas': 1,
        'modos': [
            ('Erro posicional (desgaste harmonic drive)', 0.35),
            ('Falha de servo motor / encoder',            0.25),
            ('Falha de sensor / fiação',                  0.20),
            ('Falha do controlador / software',           0.12),
            ('Dano mecânico (colisão, sobrecarga)',        0.08),
        ]
    },
    'Controlador': {
        'pf': 0.10, 'beta_inf': 0.8, 'beta_sup': 1.1,
        'qtd_falhas': 1,
        'modos': [
            ('Falha de placa de I/O',          0.30),
            ('Falha de fonte de alimentação',  0.25),
            ('Falha de comunicação / rede',    0.20),
            ('Falha de CPU / memória',         0.15),
            ('Superaquecimento',               0.10),
        ]
    },
    'Garra': {
        'pf': 0.10, 'beta_inf': 1.5, 'beta_sup': 2.5,
        'qtd_falhas': 1,
        'modos': [
            ('Desgaste dos dedos de contato',         0.35),
            ('Falha do atuador pneumático/elétrico',  0.28),
            ('Falha de sensor de presença/força',     0.20),
            ('Dano estrutural (queda, colisão)',       0.12),
            ('Falha de fiação / conector',            0.05),
        ]
    },
    'Paletizadora': {
        'pf': 0.10, 'beta_inf': 1.2, 'beta_sup': 2.0,
        'qtd_falhas': 1,
        'modos': [
            ('Falha de motor / redutor',                    0.33),
            ('Falha de sensor / fim de curso',              0.23),
            ('Desgaste mecânico (corrente, guia, fuso)',    0.20),
            ('Falha pneumática',                            0.14),
            ('Falha elétrica / fiação',                     0.10),
        ]
    },
    'Válvula de Segurança': {
        'pf': 0.15, 'beta_inf': 1.0, 'beta_sup': 1.8,
        'qtd_falhas': 1,
        'modos': [
            ('Falha ao abrir sob demanda (FTO)',                        0.35),
            ('Vazamento de sede / falha ao resentar após atuação',     0.28),
            ('Deriva de set point (relaxamento de mola)',               0.18),
            ('Abertura espúria / chattering',                          0.12),
            ('Dano mecânico a disco ou sede',                          0.07),
        ]
    },
    'Envolvedora': {
        'pf': 0.20, 'beta_inf': 1.2, 'beta_sup': 2.0,
        'qtd_falhas': 1,
        'modos': [
            ('Falha do sistema de selagem / resistência', 0.35),
            ('Desgaste mecânico (corrente, fuso, guia)',  0.28),
            ('Falha de motor / acionamento',              0.18),
            ('Falha de sensor / fim de curso',            0.12),
            ('Obstrução / rasgo de filme',                0.07),
        ]
    },
}

# =============================================================================
# 3. DETECTABILIDADE POR VIBRAÇÃO (preditiva)
# =============================================================================
# Prob. de detecção por modo de falha para cada classe coberta
# Classes cobertas: Motor Elétrico, Bomba, Redutor

DETECTABILIDADE = {
    'Motor Elétrico': {
        'Falha de rolamento':                0.80,
        'Falha mecânica (eixo/acoplamento)': 0.75,
        'Falha de enrolamento / isolação':   0.20,
        'Contaminação / umidade':            0.00,
        'Superaquecimento':                  0.00,
    },
    'Bomba': {
        'Falha de rolamento':                   0.80,
        'Desalinhamento de eixo / vibração':    0.85,
        'Dano ao impelidor (erosão/cavitação)': 0.65,
        'Bloqueio / restrição de fluxo':        0.25,
        'Falha de selo mecânico / vazamento':   0.00,
    },
    'Redutor': {
        'Fadiga / micropitting de dente de engrenagem': 0.70,
        'Falha de rolamento':                           0.80,
        'Falha de eixo':                                0.60,
        'Vazamento de vedação / óleo':                  0.00,
        'Dano ao cárter / carcaça':                     0.00,
    },
}

CLASSES_PREDITIVA = set(DETECTABILIDADE.keys())

# =============================================================================
# 4. DESCRIÇÕES POR MODO DE FALHA
# =============================================================================

DESCRICOES_CORRETIVA = {
    'Falha de rolamento':                        ['rolamento com ruído anormal', 'vibração elevada no mancal', 'temperatura alta no rolamento', 'rolamento travado'],
    'Falha de enrolamento / isolação':            ['motor não parte - enrolamento queimado', 'fuga à terra no estator', 'curto no enrolamento'],
    'Falha mecânica (eixo/acoplamento)':          ['acoplamento partido', 'eixo com folga excessiva', 'vibração alta - verificar acoplamento'],
    'Contaminação / umidade':                     ['motor com entrada de água', 'contaminação interna por poeira', 'umidade no terminal de ligação'],
    'Superaquecimento':                           ['motor desarmando por temperatura', 'proteção térmica atuando', 'motor muito quente ao toque'],
    'Deriva de sinal / perda de calibração':      ['sinal fora do esperado', 'leitura incorreta - calibrar sensor', 'sensor com deriva de zero'],
    'Falha de conexão elétrica':                  ['sensor sem sinal - verificar fiação', 'cabo danificado no sensor'],
    'Dano físico (vibração/impacto)':             ['sensor danificado por impacto', 'sensor quebrado por vibração excessiva'],
    'Falha de componente eletrônico':             ['placa do sensor queimada', 'sensor sem resposta - componente interno'],
    'Contaminação (poeira, umidade)':             ['sensor com lente suja', 'umidade interna no sensor'],
    'Vazamento interno / externo':                ['válvula com vazamento externo', 'gotejamento no corpo da válvula'],
    'Falha ao abrir/fechar sob demanda':          ['válvula não abre ao comando', 'válvula travada na posição fechada'],
    'Falha de curso parcial':                     ['válvula não atinge posição 100%', 'curso limitado - verificar atuador'],
    'Corrosão / erosão':                          ['corpo da válvula com corrosão avançada', 'erosão na sede da válvula'],
    'Travamento mecânico / atrito excessivo':     ['válvula com esforço excessivo para operar', 'haste travada'],
    'Falha de selo mecânico / vazamento':         ['selo mecânico com vazamento', 'bomba perdendo produto pelo eixo'],
    'Dano ao impelidor (erosão/cavitação)':       ['cavitação na bomba', 'impelidor desgastado - perda de vazão'],
    'Bloqueio / restrição de fluxo':              ['bomba sem vazão - verificar filtro', 'sucção bloqueada'],
    'Desalinhamento de eixo / vibração':          ['vibração alta na bomba - verificar alinhamento'],
    'Falha do módulo IGBT':                       ['inversor desarmando - falha IGBT', 'módulo de potência queimado'],
    'Degradação do capacitor (barramento DC)':    ['inversor com alarme de barramento DC'],
    'Superaquecimento / bloqueio do resfriamento':['inversor desligando por temperatura'],
    'Falha da placa de controle / firmware':      ['inversor sem comunicação', 'parâmetros perdidos no inversor'],
    'Falha do retificador de entrada':            ['inversor sem tensão no barramento'],
    'Falha de caixa de redução (desgaste de dentes)': ['ruído na caixa de redução', 'desgaste nos dentes da engrenagem'],
    'Falha de rolamento (polias/acionamento)':    ['rolamento da polia com ruído'],
    'Desgaste / dano estrutural da correia':      ['correia com desgaste excessivo', 'correia partida'],
    'Falha elétrica do motor':                    ['motor da esteira sem partir'],
    'Dano em acoplamento / eixo':                 ['acoplamento da esteira danificado'],
    'Falha de rolamento':                         ['rolamento com ruído anormal', 'vibração elevada no mancal'],
    'Falha de válvula (sucção/descarga)':         ['válvula de sucção do compressor com folga'],
    'Vazamento de vedação / gaxeta':              ['gaxeta do compressor com vazamento'],
    'Dano ao rotor / impelidor':                  ['rotor com desgaste'],
    'Falha do sistema de resfriamento':           ['compressor desarmando por temperatura'],
    'Fadiga / micropitting de dente de engrenagem': ['ruído anormal no redutor', 'engrenagem com desgaste por fadiga'],
    'Falha de eixo':                              ['eixo do redutor com trinca', 'quebra de eixo no redutor'],
    'Vazamento de vedação / óleo':                ['vazamento de óleo no redutor'],
    'Dano ao cárter / carcaça':                   ['carcaça do redutor trincada'],
    'Erro posicional (desgaste harmonic drive)':  ['robô fora de posição'],
    'Falha de servo motor / encoder':             ['alarme de encoder no robô'],
    'Falha de sensor / fiação':                   ['sensor do robô sem sinal'],
    'Falha do controlador / software':            ['CLP do robô em falha'],
    'Dano mecânico (colisão, sobrecarga)':        ['robô colidiu com estrutura'],
    'Falha de placa de I/O':                      ['entrada digital sem resposta no CLP'],
    'Falha de fonte de alimentação':              ['CLP sem tensão de alimentação'],
    'Falha de comunicação / rede':                ['CLP sem comunicação com supervisório'],
    'Falha de CPU / memória':                     ['CLP em modo de falha - CPU'],
    'Desgaste dos dedos de contato':              ['garra com desgaste nos dedos'],
    'Falha do atuador pneumático/elétrico':       ['atuador da garra sem pressão'],
    'Falha de sensor de presença/força':          ['sensor de presença da garra sem sinal'],
    'Dano estrutural (queda, colisão)':           ['garra danificada por queda'],
    'Falha de fiação / conector':                 ['curto na fiação do painel'],
    'Falha de motor / redutor':                   ['motor da paletizadora sem partir'],
    'Falha de sensor / fim de curso':             ['fim de curso não acionando'],
    'Desgaste mecânico (corrente, guia, fuso)':   ['corrente da paletizadora com desgaste'],
    'Falha pneumática':                           ['cilindro pneumático sem pressão'],
    'Falha elétrica / fiação':                    ['curto na fiação do painel'],
    'Falha ao abrir sob demanda (FTO)':           ['válvula de segurança não abriu no teste'],
    'Vazamento de sede / falha ao resentar após atuação': ['válvula de segurança vazando após teste'],
    'Deriva de set point (relaxamento de mola)':  ['válvula aliviando abaixo da pressão de set'],
    'Abertura espúria / chattering':              ['válvula de segurança abrindo sem sobrepressão'],
    'Dano mecânico a disco ou sede':              ['partículas no fluido danificaram a sede'],
    'Falha do sistema de selagem / resistência':  ['resistência de selagem queimada'],
    'Desgaste mecânico (corrente, fuso, guia)':   ['fuso da envolvedora com desgaste'],
    'Falha de motor / acionamento':               ['motor da envolvedora sem partir'],
    'Obstrução / rasgo de filme':                 ['filme rasgando na envolvedora'],
}

# Descrições para notificações preditivas — falha incipiente, não consumada
DESCRICOES_PREDITIVA = {
    'Falha de rolamento': [
        'análise de vibração indica energia elevada na frequência de falha de rolamento (BPFO)',
        'espectro com harmônicas de defeito de rolamento - inspeção recomendada',
        'vibração radial acima do limite - suspeita de falha incipiente em rolamento',
        'análise preditiva detectou elevação de energia em banda de defeito - rolamento',
    ],
    'Falha mecânica (eixo/acoplamento)': [
        'vibração com componente de desalinhamento angular elevada - verificar acoplamento',
        'espectro com harmônicas 2x RPM elevadas - suspeita de desalinhamento',
        'análise preditiva: desbalanceamento residual detectado acima do limite',
    ],
    'Falha de enrolamento / isolação': [
        'análise de vibração elétrica indica assimetria no campo magnético - verificar enrolamento',
        'espectro com harmônicas de frequência de linha elevadas - inspecionar isolação',
    ],
    'Desalinhamento de eixo / vibração': [
        'análise preditiva: vibração radial e axial elevadas - desalinhamento detectado',
        'espectro indica desalinhamento angular - alinhar conjunto motor-bomba',
        'vibração 2x RPM elevada - verificar alinhamento do eixo',
    ],
    'Dano ao impelidor (erosão/cavitação)': [
        'análise detectou frequências subharmônicas - suspeita de cavitação incipiente',
        'espectro com ruído de banda larga elevado - possível erosão de impelidor',
        'vibração em alta frequência com padrão de cavitação identificado',
    ],
    'Bloqueio / restrição de fluxo': [
        'vibração com padrão atípico - verificar condição de fluxo',
        'análise indica possível restrição - inspeção de linha recomendada',
    ],
    'Fadiga / micropitting de dente de engrenagem': [
        'análise detectou elevação em GMF (gear mesh frequency) - inspeção de engrenagem',
        'espectro com bandas laterais em GMF - desgaste incipiente de dente detectado',
        'energia elevada na frequência de malha de engrenagem - monitorar redutor',
    ],
    'Falha de eixo': [
        'análise detectou componente de 0.5x RPM - suspeita de trinca incipiente em eixo',
        'vibração com padrão de eixo dobrado - inspeção recomendada',
    ],
}

def gerar_descricao(modo_falha, tipo):
    if tipo == 'Preditiva':
        opcoes = DESCRICOES_PREDITIVA.get(modo_falha)
        if opcoes:
            return np.random.choice(opcoes)
        return f'análise preditiva detectou anomalia - modo: {modo_falha.lower()}'
    else:
        opcoes = DESCRICOES_CORRETIVA.get(modo_falha)
        if opcoes:
            return np.random.choice(opcoes)
        return modo_falha.lower()

# =============================================================================
# 5. PARETO 30/70
# =============================================================================

def distribuir_falhas_pareto(ids_ativos, qtd_total):
    n = len(ids_ativos)
    if n == 0 or qtd_total == 0:
        return {}

    ids = list(ids_ativos)
    np.random.shuffle(ids)

    n_criticos    = max(1, round(n * 0.30))
    qtd_criticos  = round(qtd_total * 0.70)
    qtd_normais   = qtd_total - qtd_criticos
    criticos      = ids[:n_criticos]
    normais       = ids[n_criticos:]
    dist          = {}

    if qtd_criticos > 0 and criticos:
        pesos = np.random.dirichlet(np.ones(len(criticos)))
        for ativo, peso in zip(criticos, pesos):
            dist[ativo] = max(1, round(peso * qtd_criticos))

    if qtd_normais > 0 and normais:
        pesos = np.random.dirichlet(np.ones(len(normais)))
        for ativo, peso in zip(normais, pesos):
            n_f = round(peso * qtd_normais)
            if n_f > 0:
                dist[ativo] = dist.get(ativo, 0) + n_f

    total_atual = sum(dist.values())
    diff = qtd_total - total_atual
    if diff != 0 and dist:
        ativo_ajuste = max(dist, key=dist.get)
        dist[ativo_ajuste] += diff
        if dist[ativo_ajuste] <= 0:
            dist[ativo_ajuste] = 1

    return dist

# =============================================================================
# 6. GERAÇÃO DE DATA DE FALHA (Weibull — mesmo do script anterior)
# =============================================================================

CLASSES_INFANTIL = {
    'Sensor':               0.05,  # menos mortalidade infantil em 2024 (planta madura)
    'Motor Elétrico':       0.03,
    'Inversor de Frequência': 0.05,
    'Controlador':          0.05,
}

def gerar_data_falha_weibull(beta):
    t_mediana  = PERIODO_DIAS * 0.60
    eta        = t_mediana / (np.log(2) ** (1.0 / beta))
    tempo      = eta * np.random.weibull(beta)
    if tempo > PERIODO_DIAS:
        return None
    return int(tempo)

def gerar_data_falha_infantil():
    tempo = 30 * np.random.weibull(0.4)
    return int(min(tempo, 60))

def gerar_data_falha(beta, classe=''):
    prob_infantil = CLASSES_INFANTIL.get(classe, 0.0)
    if np.random.random() < prob_infantil:
        tempo_dias = gerar_data_falha_infantil()
    else:
        tempo_dias = gerar_data_falha_weibull(beta)
        if tempo_dias is None:
            return None
    return DATA_INICIO + timedelta(days=tempo_dias)

# =============================================================================
# 7. GERAÇÃO DAS NOTIFICAÇÕES
# =============================================================================

notificacoes = []
id_notif = 1

for classe, params in PARAMS_FALHA.items():

    ativos_classe = df_ativos[df_ativos['classe_ativo'] == classe]
    if len(ativos_classe) == 0:
        continue

    qtd_falhas  = max(1, int(round(params['qtd_falhas'])))
    modos       = params['modos']
    beta_inf    = params['beta_inf']
    beta_sup    = params['beta_sup']
    cobre_pred  = classe in CLASSES_PREDITIVA

    dist_falhas = distribuir_falhas_pareto(
        ativos_classe['id_ativo'].tolist(), qtd_falhas
    )

    for id_ativo, n_falhas in dist_falhas.items():

        ativo = ativos_classe[ativos_classe['id_ativo'] == id_ativo].iloc[0]

        for _ in range(n_falhas):

            beta = np.random.uniform(beta_inf, beta_sup)

            data_falha = None
            for _ in range(5):
                data_falha = gerar_data_falha(beta, classe)
                if data_falha is not None:
                    break
            if data_falha is None:
                continue

            # Sorteia modo de falha
            modos_desc  = [m[0] for m in modos]
            modos_probs = [m[1] for m in modos]
            modo_falha  = np.random.choice(modos_desc, p=modos_probs)

            # Verifica se preditiva intercepta
            tipo = 'Corretiva'
            if cobre_pred:
                detect_probs = DETECTABILIDADE.get(classe, {})
                prob_det     = detect_probs.get(modo_falha, 0.0)
                if np.random.random() < prob_det:
                    tipo = 'Preditiva'
                    # Preditiva detecta ANTES da falha: 15-45 dias antes
                    antecedencia = int(np.random.randint(15, 46))
                    data_falha   = data_falha - timedelta(days=antecedencia)
                    if data_falha < DATA_INICIO:
                        data_falha = DATA_INICIO + timedelta(days=int(np.random.randint(1, 30)))

            notificacoes.append({
                'id_notificacao':   id_notif,
                'id_ativo':         id_ativo,
                'tag_ativo':        ativo['tag'],
                'classe_ativo':     classe,
                'setor':            ativo['setor'],
                'setor_desc':       ativo['setor_desc'],
                'criticidade':      ativo['criticidade'],
                'data_notificacao': data_falha.strftime('%Y-%m-%d'),
                'tipo_manutencao':  tipo,
                'modo_falha':       modo_falha,
                'descricao':        gerar_descricao(modo_falha, tipo),
            })

            id_notif += 1

# =============================================================================
# 8. MONTA DATAFRAME E EXPORTA
# =============================================================================

df_notif = pd.DataFrame(notificacoes)
df_notif = df_notif.sort_values('data_notificacao').reset_index(drop=True)

print(f"\nTotal de notificações 2024: {len(df_notif)}")
print(f"\nPor tipo:")
print(df_notif['tipo_manutencao'].value_counts().to_string())
print(f"\nPor classe:")
print(df_notif['classe_ativo'].value_counts().to_string())
print(f"\nPreditivas por classe:")
pred = df_notif[df_notif['tipo_manutencao'] == 'Preditiva']
print(pred['classe_ativo'].value_counts().to_string())
print(f"\nDistribuição mensal:")
df_notif['mes'] = pd.to_datetime(df_notif['data_notificacao']).dt.to_period('M')
print(df_notif['mes'].value_counts().sort_index().to_string())

df_notif.drop(columns=['mes']).to_csv('/home/claude/NOTIFICACOES-2024.csv', index=False)
print("\nDataset exportado: NOTIFICACOES-2024.csv")
