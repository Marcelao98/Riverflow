# =============================================================================
# GERAÇÃO DE ORDENS DE MANUTENÇÃO CORRETIVAS
# Fábrica fictícia de água mineral - Planta 1 (pl1)
# =============================================================================
# Cada notificação corretiva gera exatamente uma OM corretiva (relação 1:1).
#
# Lógica de tempo:
#   1. Notificação criada       → data_notificacao (do dataset anterior)
#   2. OM criada                → notificação + 0 a 2 dias
#   3. OM início de execução    → OM criada + delay por criticidade
#                                  A: 0-1 dia  (atendimento imediato)
#                                  B: 1-4 dias (agendado na semana)
#                                  C: 3-10 dias (entra no backlog)
#   4. OM encerrada             → início + MTTR sorteado por modo de falha
#
# Período de simulação: 01/01/2023 → 01/03/2026
# OMs não encerradas até 01/03/2026 ficam com status "Em Aberto" (backlog)
#
# Inputs:
#   - NOTIFICACOES-CORRETIVAS.csv
# Output:
#   - ORDENS-CORRETIVAS.csv
# =============================================================================

import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta

fake = Faker('pt_BR')
np.random.seed(42)

# Data de corte — OMs abertas após essa data ficam "Em Aberto"
DATA_CORTE = datetime(2026, 2, 10)

# =============================================================================
# 1. CARREGA NOTIFICAÇÕES
# =============================================================================

df_notif = pd.read_csv('/home/claude/NOTIFICACOES-CORRETIVAS.csv')
print(f"Notificações carregadas: {len(df_notif)}")

# =============================================================================
# 2. ESTENDE PERÍODO DE FALHAS ATÉ MARÇO/2026
# =============================================================================
# Falhas geradas originalmente até dez/2025 são redistribuídas
# para cobrir até mar/2026, simulando continuidade da operação.
# A proporção de falhas por mês se mantém uniforme no período extra.

def redistribuir_datas(df, data_fim_original='2025-12-31', data_fim_nova='2026-03-01'):
    """
    Redistribui aleatoriamente ~20% das notificações do último trimestre
    para o período jan-mar/2026, simulando continuidade da operação.
    """
    df = df.copy()
    df['data_notificacao'] = pd.to_datetime(df['data_notificacao'])

    # Pega notificações do último trimestre
    data_inicio_trim = pd.Timestamp('2025-10-01')
    mask = df['data_notificacao'] >= data_inicio_trim

    # Redistribui ~30% delas para jan-mar/2026
    idx_trim = df[mask].index.tolist()
    n_mover  = max(1, round(len(idx_trim) * 0.30))
    idx_mover = np.random.choice(idx_trim, size=n_mover, replace=False)

    data_nova_inicio = datetime(2026, 1, 1)
    data_nova_fim    = datetime(2026, 3, 1)
    delta = (data_nova_fim - data_nova_inicio).days

    for idx in idx_mover:
        nova_data = data_nova_inicio + timedelta(days=int(np.random.randint(0, delta)))
        df.at[idx, 'data_notificacao'] = nova_data

    df['data_notificacao'] = df['data_notificacao'].dt.strftime('%Y-%m-%d')
    return df

df_notif = redistribuir_datas(df_notif)
print(f"Período de falhas estendido até mar/2026")

# =============================================================================
# 3. PARÂMETROS DE MTTR E CUSTO POR MODO DE FALHA
# =============================================================================

PARAMS_OM = {
    'Falha de rolamento':                                 {'mttr_min': 4,  'mttr_max': 8,  'equipe': 'Mecânica',        'custo_min': 800,   'custo_max': 2500},
    'Falha de enrolamento / isolação':                    {'mttr_min': 16, 'mttr_max': 48, 'equipe': 'Elétrica',        'custo_min': 3000,  'custo_max': 9000},
    'Falha mecânica (eixo/acoplamento)':                  {'mttr_min': 6,  'mttr_max': 16, 'equipe': 'Mecânica',        'custo_min': 1500,  'custo_max': 4000},
    'Contaminação / umidade':                             {'mttr_min': 3,  'mttr_max': 6,  'equipe': 'Elétrica',        'custo_min': 400,   'custo_max': 1200},
    'Superaquecimento':                                   {'mttr_min': 2,  'mttr_max': 5,  'equipe': 'Elétrica',        'custo_min': 300,   'custo_max': 900},
    'Deriva de sinal / perda de calibração':              {'mttr_min': 1,  'mttr_max': 3,  'equipe': 'Instrumentação',  'custo_min': 150,   'custo_max': 600},
    'Falha de conexão elétrica':                          {'mttr_min': 1,  'mttr_max': 2,  'equipe': 'Instrumentação',  'custo_min': 80,    'custo_max': 300},
    'Dano físico (vibração/impacto)':                     {'mttr_min': 2,  'mttr_max': 4,  'equipe': 'Instrumentação',  'custo_min': 300,   'custo_max': 1200},
    'Falha de componente eletrônico':                     {'mttr_min': 3,  'mttr_max': 8,  'equipe': 'Instrumentação',  'custo_min': 500,   'custo_max': 2000},
    'Contaminação (poeira, umidade)':                     {'mttr_min': 1,  'mttr_max': 2,  'equipe': 'Instrumentação',  'custo_min': 80,    'custo_max': 250},
    'Vazamento interno / externo':                        {'mttr_min': 4,  'mttr_max': 10, 'equipe': 'Mecânica',        'custo_min': 600,   'custo_max': 2000},
    'Falha ao abrir/fechar sob demanda':                  {'mttr_min': 3,  'mttr_max': 8,  'equipe': 'Instrumentação',  'custo_min': 500,   'custo_max': 1800},
    'Falha de curso parcial':                             {'mttr_min': 2,  'mttr_max': 6,  'equipe': 'Instrumentação',  'custo_min': 300,   'custo_max': 1000},
    'Corrosão / erosão':                                  {'mttr_min': 8,  'mttr_max': 24, 'equipe': 'Caldeiraria',     'custo_min': 2000,  'custo_max': 6000},
    'Travamento mecânico / atrito excessivo':             {'mttr_min': 3,  'mttr_max': 8,  'equipe': 'Mecânica',        'custo_min': 400,   'custo_max': 1500},
    'Falha de selo mecânico / vazamento':                 {'mttr_min': 4,  'mttr_max': 10, 'equipe': 'Mecânica',        'custo_min': 1000,  'custo_max': 3500},
    'Dano ao impelidor (erosão/cavitação)':               {'mttr_min': 8,  'mttr_max': 24, 'equipe': 'Mecânica',        'custo_min': 2500,  'custo_max': 7000},
    'Bloqueio / restrição de fluxo':                      {'mttr_min': 2,  'mttr_max': 4,  'equipe': 'Mecânica',        'custo_min': 200,   'custo_max': 600},
    'Desalinhamento de eixo / vibração':                  {'mttr_min': 3,  'mttr_max': 6,  'equipe': 'Mecânica',        'custo_min': 400,   'custo_max': 1200},
    'Falha do módulo IGBT':                               {'mttr_min': 4,  'mttr_max': 12, 'equipe': 'Elétrica',        'custo_min': 2000,  'custo_max': 6000},
    'Degradação do capacitor (barramento DC)':            {'mttr_min': 3,  'mttr_max': 8,  'equipe': 'Elétrica',        'custo_min': 1000,  'custo_max': 3000},
    'Superaquecimento / bloqueio do resfriamento':        {'mttr_min': 1,  'mttr_max': 3,  'equipe': 'Elétrica',        'custo_min': 200,   'custo_max': 600},
    'Falha da placa de controle / firmware':              {'mttr_min': 4,  'mttr_max': 10, 'equipe': 'Elétrica',        'custo_min': 1500,  'custo_max': 4500},
    'Falha do retificador de entrada':                    {'mttr_min': 4,  'mttr_max': 10, 'equipe': 'Elétrica',        'custo_min': 1500,  'custo_max': 4000},
    'Falha de caixa de redução (desgaste de dentes)':     {'mttr_min': 8,  'mttr_max': 20, 'equipe': 'Mecânica',        'custo_min': 2000,  'custo_max': 6000},
    'Falha de rolamento (polias/acionamento)':            {'mttr_min': 4,  'mttr_max': 8,  'equipe': 'Mecânica',        'custo_min': 600,   'custo_max': 2000},
    'Desgaste / dano estrutural da correia':              {'mttr_min': 3,  'mttr_max': 8,  'equipe': 'Mecânica',        'custo_min': 500,   'custo_max': 2000},
    'Falha elétrica do motor':                            {'mttr_min': 4,  'mttr_max': 12, 'equipe': 'Elétrica',        'custo_min': 800,   'custo_max': 3000},
    'Dano em acoplamento / eixo':                         {'mttr_min': 4,  'mttr_max': 10, 'equipe': 'Mecânica',        'custo_min': 600,   'custo_max': 2000},
    'Falha de válvula (sucção/descarga)':                 {'mttr_min': 4,  'mttr_max': 10, 'equipe': 'Mecânica',        'custo_min': 800,   'custo_max': 2500},
    'Vazamento de vedação / gaxeta':                      {'mttr_min': 4,  'mttr_max': 8,  'equipe': 'Mecânica',        'custo_min': 600,   'custo_max': 2000},
    'Dano ao rotor / impelidor':                          {'mttr_min': 16, 'mttr_max': 48, 'equipe': 'Mecânica',        'custo_min': 5000,  'custo_max': 15000},
    'Falha do sistema de resfriamento':                   {'mttr_min': 3,  'mttr_max': 8,  'equipe': 'Mecânica',        'custo_min': 500,   'custo_max': 1500},
    'Fadiga / micropitting de dente de engrenagem':       {'mttr_min': 16, 'mttr_max': 48, 'equipe': 'Mecânica',        'custo_min': 4000,  'custo_max': 12000},
    'Falha de eixo':                                      {'mttr_min': 12, 'mttr_max': 32, 'equipe': 'Mecânica',        'custo_min': 3000,  'custo_max': 9000},
    'Vazamento de vedação / óleo':                        {'mttr_min': 2,  'mttr_max': 5,  'equipe': 'Mecânica',        'custo_min': 200,   'custo_max': 600},
    'Dano ao cárter / carcaça':                           {'mttr_min': 8,  'mttr_max': 24, 'equipe': 'Caldeiraria',     'custo_min': 2000,  'custo_max': 6000},
    'Erro posicional (desgaste harmonic drive)':          {'mttr_min': 8,  'mttr_max': 24, 'equipe': 'Mecânica',        'custo_min': 5000,  'custo_max': 15000},
    'Falha de servo motor / encoder':                     {'mttr_min': 6,  'mttr_max': 16, 'equipe': 'Elétrica',        'custo_min': 3000,  'custo_max': 9000},
    'Falha de sensor / fiação':                           {'mttr_min': 2,  'mttr_max': 5,  'equipe': 'Instrumentação',  'custo_min': 300,   'custo_max': 1000},
    'Falha do controlador / software':                    {'mttr_min': 4,  'mttr_max': 12, 'equipe': 'Elétrica',        'custo_min': 1500,  'custo_max': 5000},
    'Dano mecânico (colisão, sobrecarga)':                {'mttr_min': 8,  'mttr_max': 32, 'equipe': 'Mecânica',        'custo_min': 3000,  'custo_max': 12000},
    'Falha de placa de I/O':                              {'mttr_min': 3,  'mttr_max': 8,  'equipe': 'Elétrica',        'custo_min': 800,   'custo_max': 2500},
    'Falha de fonte de alimentação':                      {'mttr_min': 2,  'mttr_max': 5,  'equipe': 'Elétrica',        'custo_min': 400,   'custo_max': 1200},
    'Falha de comunicação / rede':                        {'mttr_min': 2,  'mttr_max': 6,  'equipe': 'Instrumentação',  'custo_min': 200,   'custo_max': 800},
    'Falha de CPU / memória':                             {'mttr_min': 4,  'mttr_max': 12, 'equipe': 'Elétrica',        'custo_min': 1000,  'custo_max': 4000},
    'Desgaste dos dedos de contato':                      {'mttr_min': 2,  'mttr_max': 5,  'equipe': 'Mecânica',        'custo_min': 300,   'custo_max': 1000},
    'Falha do atuador pneumático/elétrico':               {'mttr_min': 3,  'mttr_max': 8,  'equipe': 'Mecânica',        'custo_min': 500,   'custo_max': 1800},
    'Falha de sensor de presença/força':                  {'mttr_min': 1,  'mttr_max': 3,  'equipe': 'Instrumentação',  'custo_min': 200,   'custo_max': 800},
    'Dano estrutural (queda, colisão)':                   {'mttr_min': 8,  'mttr_max': 24, 'equipe': 'Mecânica',        'custo_min': 2000,  'custo_max': 8000},
    'Falha de fiação / conector':                         {'mttr_min': 1,  'mttr_max': 3,  'equipe': 'Elétrica',        'custo_min': 100,   'custo_max': 400},
    'Falha de motor / redutor':                           {'mttr_min': 6,  'mttr_max': 16, 'equipe': 'Mecânica',        'custo_min': 1500,  'custo_max': 5000},
    'Falha de sensor / fim de curso':                     {'mttr_min': 1,  'mttr_max': 3,  'equipe': 'Instrumentação',  'custo_min': 150,   'custo_max': 500},
    'Desgaste mecânico (corrente, guia, fuso)':           {'mttr_min': 4,  'mttr_max': 10, 'equipe': 'Mecânica',        'custo_min': 800,   'custo_max': 2500},
    'Falha pneumática':                                   {'mttr_min': 2,  'mttr_max': 5,  'equipe': 'Mecânica',        'custo_min': 300,   'custo_max': 1000},
    'Falha elétrica / fiação':                            {'mttr_min': 2,  'mttr_max': 5,  'equipe': 'Elétrica',        'custo_min': 300,   'custo_max': 1000},
    'Falha ao abrir sob demanda (FTO)':                   {'mttr_min': 6,  'mttr_max': 16, 'equipe': 'Instrumentação',  'custo_min': 1500,  'custo_max': 5000},
    'Vazamento de sede / falha ao resentar após atuação': {'mttr_min': 4,  'mttr_max': 10, 'equipe': 'Mecânica',        'custo_min': 800,   'custo_max': 2500},
    'Deriva de set point (relaxamento de mola)':          {'mttr_min': 3,  'mttr_max': 8,  'equipe': 'Instrumentação',  'custo_min': 600,   'custo_max': 2000},
    'Abertura espúria / chattering':                      {'mttr_min': 3,  'mttr_max': 8,  'equipe': 'Instrumentação',  'custo_min': 500,   'custo_max': 1800},
    'Dano mecânico a disco ou sede':                      {'mttr_min': 6,  'mttr_max': 16, 'equipe': 'Mecânica',        'custo_min': 1200,  'custo_max': 4000},
    'Falha do sistema de selagem / resistência':          {'mttr_min': 2,  'mttr_max': 5,  'equipe': 'Elétrica',        'custo_min': 400,   'custo_max': 1500},
    'Desgaste mecânico (corrente, fuso, guia)':           {'mttr_min': 4,  'mttr_max': 10, 'equipe': 'Mecânica',        'custo_min': 600,   'custo_max': 2000},
    'Falha de motor / acionamento':                       {'mttr_min': 4,  'mttr_max': 10, 'equipe': 'Elétrica',        'custo_min': 800,   'custo_max': 2500},
    'Obstrução / rasgo de filme':                         {'mttr_min': 1,  'mttr_max': 2,  'equipe': 'Mecânica',        'custo_min': 100,   'custo_max': 400},
}

PARAMS_DEFAULT = {'mttr_min': 4, 'mttr_max': 12, 'equipe': 'Mecânica', 'custo_min': 500, 'custo_max': 2000}

# =============================================================================
# 4. DELAYS POR CRITICIDADE
# =============================================================================

DELAY_NOTIF_OM = {'A': (0, 0), 'B': (0, 1), 'C': (1, 2)}
DELAY_OM_EXEC  = {'A': (0, 1), 'B': (1, 4), 'C': (3, 10)}

# =============================================================================
# 5. TÉCNICOS POR EQUIPE
# =============================================================================

TECNICOS = {
    'Mecânica':       [fake.name() for _ in range(8)],
    'Elétrica':       [fake.name() for _ in range(6)],
    'Instrumentação': [fake.name() for _ in range(5)],
    'Caldeiraria':    [fake.name() for _ in range(4)],
}

def sortear_tecnico(equipe):
    return np.random.choice(TECNICOS.get(equipe, TECNICOS['Mecânica']))

# =============================================================================
# 6. GERAÇÃO DAS OMs
# =============================================================================

ordens = []

for _, notif in df_notif.iterrows():

    modo_falha  = notif['modo_falha']
    criticidade = notif['criticidade']
    data_notif  = datetime.strptime(notif['data_notificacao'], '%Y-%m-%d')
    params      = PARAMS_OM.get(modo_falha, PARAMS_DEFAULT)

    # Notificação → OM aberta
    d_min, d_max     = DELAY_NOTIF_OM.get(criticidade, (0, 2))
    data_abertura_om = data_notif + timedelta(days=int(np.random.randint(d_min, d_max + 1)))

    # OM aberta → início execução
    d_min, d_max      = DELAY_OM_EXEC.get(criticidade, (1, 5))
    data_inicio_exec  = data_abertura_om + timedelta(days=int(np.random.randint(d_min, d_max + 1)))

    # MTTR e encerramento
    mttr_horas        = round(np.random.uniform(params['mttr_min'], params['mttr_max']), 1)
    data_encerramento = data_inicio_exec + timedelta(hours=mttr_horas)

    # Status
    if data_encerramento > DATA_CORTE:
        status                = 'Em Aberto'
        data_encerramento_str = None
        mttr_real             = None
        custo                 = None
    else:
        status                = 'Encerrada'
        data_encerramento_str = data_encerramento.strftime('%Y-%m-%d')
        mttr_real             = mttr_horas
        custo                 = round(np.random.uniform(params['custo_min'], params['custo_max']), 2)

    ordens.append({
        'id_om':                len(ordens) + 1,
        'id_notificacao':       notif['id_notificacao'],
        'tag_ativo':            notif['tag_ativo'],
        'criticidade':          criticidade,
        'tipo_manutencao':      'Corretiva',
        'equipe':               params['equipe'],
        'tecnico_responsavel':  sortear_tecnico(params['equipe']),
        'data_notificacao':     notif['data_notificacao'],
        'data_abertura_om':     data_abertura_om.strftime('%Y-%m-%d'),
        'data_inicio_execucao': data_inicio_exec.strftime('%Y-%m-%d'),
        'data_encerramento':    data_encerramento_str,
        'mttr_horas':           mttr_real,
        'custo_real':           custo,
        'status':               status,
    })

# =============================================================================
# 7. MONTA DATAFRAME E EXPORTA
# =============================================================================

df_om = pd.DataFrame(ordens)
df_om = df_om.sort_values('data_notificacao').reset_index(drop=True)

print(f"\nTotal de OMs geradas: {len(df_om)}")
print(f"\nStatus:")
print(df_om['status'].value_counts().to_string())
print(f"\nPor equipe:")
print(df_om['equipe'].value_counts().to_string())
print(f"\nMTTR médio por equipe (horas):")
print(df_om.groupby('equipe')['mttr_horas'].mean().round(1).to_string())
print(f"\nCusto total simulado: R$ {df_om['custo_real'].sum():,.2f}")

df_om.to_csv('/home/claude/ORDENS-CORRETIVAS.csv', index=False)
print("\nDataset exportado: ORDENS-CORRETIVAS.csv")
