# =============================================================================
# GERAÇÃO DE ORDENS DE MANUTENÇÃO PREVENTIVAS
# Fábrica fictícia de água mineral - Planta 1 (pl1)
# =============================================================================
# Preventivas geradas a partir de 01/01/2022 até 31/12/2024.
# Cada ativo elegível recebe OMs periódicas conforme plano por classe
# e criticidade. Uma margem de erro pequena (±5 dias) simula atrasos
# e adiantamentos reais de programação.
#
# Equipes:
#   - Lubrificação → Mecânica (sempre)
#   - Inspeção mecânica → Mecânica
#   - Inspeção elétrica → Elétrica
#   - Limpeza/ventilação → Elétrica
#   - Teste de válvula → Instrumentação
#
# Input:  BASE-ATIVOS-LIMPO.csv
# Output: ORDENS-PREVENTIVAS.csv
# =============================================================================

import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta

fake = Faker('pt_BR')
np.random.seed(99)

DATA_INICIO = datetime(2022, 1, 1)
DATA_FIM    = datetime(2024, 12, 31)

# =============================================================================
# 1. CARREGA ATIVOS
# =============================================================================

df_ativos = pd.read_csv('/home/claude/BASE-ATIVOS-LIMPO.csv')
print(f"Ativos carregados: {len(df_ativos)}")

# =============================================================================
# 2. PLANOS DE PREVENTIVA POR CLASSE E CRITICIDADE
# =============================================================================
# frequencia_dias: intervalo entre execuções
# duracao_horas: tempo estimado de execução
# equipe: time responsável
#
# Estrutura: classe → lista de planos
# Cada plano: (atividade, freq_A, freq_B, freq_C, duracao_h, equipe)

PLANOS = {
    'Motor Elétrico': [
        ('Lubrificação de rolamentos',
         90, 180, 365, 1.5, 'Mecânica'),
        ('Limpeza geral e verificação elétrica',
         180, 180, 365, 2.0, 'Elétrica'),
    ],
    'Bomba': [
        ('Lubrificação de rolamentos',
         90, 180, 365, 1.5, 'Mecânica'),
        ('Inspeção de selo mecânico e gaxeta',
         180, 180, 365, 2.5, 'Mecânica'),
        ('Verificação de alinhamento',
         180, 365, 365, 3.0, 'Mecânica'),
    ],
    'Redutor': [
        ('Inspeção de vedação e nível de óleo',
         90, 90, 180, 1.0, 'Mecânica'),
        ('Troca de óleo lubrificante',
         180, 180, 365, 2.0, 'Mecânica'),
    ],
    'Compressor': [
        ('Troca de filtro de ar e óleo',
         90, 90, 180, 2.0, 'Mecânica'),
        ('Lubrificação geral e verificação de válvulas',
         180, 180, 365, 3.0, 'Mecânica'),
    ],
    'Esteira': [
        ('Lubrificação de corrente e rolamentos',
         30, 30, 90, 1.0, 'Mecânica'),
        ('Verificação de tensionamento e desgaste da correia',
         90, 90, 180, 2.0, 'Mecânica'),
    ],
    'Inversor de Frequência': [
        ('Limpeza de filtro e verificação de ventilação',
         180, 180, 365, 1.0, 'Elétrica'),
    ],
    'Válvula de Segurança': [
        ('Teste de atuação e calibração de set point',
         365, 365, 365, 4.0, 'Instrumentação'),
    ],
}

# =============================================================================
# 3. TÉCNICOS POR EQUIPE
# =============================================================================

TECNICOS = {
    'Mecânica':       [fake.name() for _ in range(8)],
    'Elétrica':       [fake.name() for _ in range(6)],
    'Instrumentação': [fake.name() for _ in range(5)],
}

def sortear_tecnico(equipe):
    return np.random.choice(TECNICOS.get(equipe, TECNICOS['Mecânica']))

# =============================================================================
# 4. GERAÇÃO DAS OMs PREVENTIVAS
# =============================================================================

ordens = []
id_om  = 1

for classe, planos in PLANOS.items():

    ativos_classe = df_ativos[df_ativos['classe_ativo'] == classe]

    if len(ativos_classe) == 0:
        print(f"  [AVISO] Nenhum ativo para classe: {classe}")
        continue

    for _, ativo in ativos_classe.iterrows():

        criticidade = ativo['criticidade']

        for (atividade, freq_a, freq_b, freq_c, duracao_h, equipe) in planos:

            # Define frequência pela criticidade
            freq_map = {'A': freq_a, 'B': freq_b, 'C': freq_c}
            freq_dias = freq_map.get(criticidade, freq_b)

            # Gera OMs ao longo do período
            data_atual = DATA_INICIO + timedelta(days=freq_dias)

            while data_atual <= DATA_FIM:

                # Margem de erro: ±5 dias
                jitter = int(np.random.randint(-5, 6))
                data_exec = data_atual + timedelta(days=jitter)

                # Garante que não ultrapassa DATA_FIM
                if data_exec > DATA_FIM:
                    break

                # Duração com pequena variação (±15%)
                duracao = round(duracao_h * np.random.uniform(0.85, 1.15), 1)
                data_enc = data_exec + timedelta(hours=duracao)

                ordens.append({
                    'id_om':                id_om,
                    'tag_ativo':            ativo['tag'],
                    'criticidade':          criticidade,
                    'tipo_manutencao':      'Preventiva',
                    'atividade':            atividade,
                    'equipe':               equipe,
                    'tecnico_responsavel':  sortear_tecnico(equipe),
                    'data_execucao':        data_exec.strftime('%Y-%m-%d'),
                    'data_encerramento':    data_enc.strftime('%Y-%m-%d'),
                    'duracao_horas':        duracao,
                    'status':               'Encerrada',
                })

                id_om += 1
                data_atual += timedelta(days=freq_dias)

# =============================================================================
# 5. MONTA DATAFRAME E EXPORTA
# =============================================================================

df_prev = pd.DataFrame(ordens)
df_prev = df_prev.sort_values('data_execucao').reset_index(drop=True)

print(f"\nTotal de OMs preventivas: {len(df_prev)}")
print(f"\nPor classe (via tag):")
print(df_prev.groupby('tipo_manutencao')['id_om'].count().to_string())
print(f"\nPor equipe:")
print(df_prev['equipe'].value_counts().to_string())
print(f"\nPor atividade:")
print(df_prev['atividade'].value_counts().to_string())
print(f"\nPrimeiras OMs:")
print(df_prev.head(5).to_string())

df_prev.to_csv('/home/claude/ORDENS-PREVENTIVAS.csv', index=False)
print("\nDataset exportado: ORDENS-PREVENTIVAS.csv")
