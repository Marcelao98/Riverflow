# =============================================================================
# CONSOLIDAÇÃO FINAL DOS DATASETS
# Fábrica fictícia de água mineral - Planta 1 (pl1)
# =============================================================================
# Agrupa e unifica todos os datasets gerados em dois CSVs finais:
#
#   NOTIFICACOES-FINAL.csv — todas as notificações (2021-2024)
#     Fontes: NOTIFICACOES-CORRETIVAS (2021-2023) + NOTIFICACOES-2024
#
#   ORDENS-FINAL.csv — todas as ordens de manutenção (2021-2024)
#     Fontes: ORDENS-CORRETIVAS (2021-2023) + ORDENS-2024 + ORDENS-PREVENTIVAS
#
# Tratamentos aplicados:
#   - IDs reindexados de forma sequencial e única
#   - Colunas padronizadas entre os datasets
#   - Campos ausentes preenchidos com None
#   - Ordenação por data
# =============================================================================

import pandas as pd
import numpy as np

# =============================================================================
# 1. CONSOLIDA NOTIFICAÇÕES
# =============================================================================

notif_2123 = pd.read_csv('/mnt/user-data/uploads/NOTIFICACOES-CORRETIVAS.csv')
notif_2024 = pd.read_csv('/home/claude/NOTIFICACOES-2024.csv')

print(f"Notificações 2021-2023: {len(notif_2123)}")
print(f"Notificações 2024:      {len(notif_2024)}")

df_notif = pd.concat([notif_2123, notif_2024], ignore_index=True)

# Reindexar IDs sequencialmente
df_notif = df_notif.sort_values('data_notificacao').reset_index(drop=True)
df_notif['id_notificacao'] = range(1, len(df_notif) + 1)

# Garante tipos corretos
df_notif['data_notificacao'] = pd.to_datetime(df_notif['data_notificacao']).dt.strftime('%Y-%m-%d')

print(f"\nTotal notificações consolidadas: {len(df_notif)}")
print(f"Período: {df_notif['data_notificacao'].min()} → {df_notif['data_notificacao'].max()}")
print(f"\nPor tipo:")
print(df_notif['tipo_manutencao'].value_counts().to_string())
print(f"\nPor ano:")
df_notif['ano'] = pd.to_datetime(df_notif['data_notificacao']).dt.year
print(df_notif['ano'].value_counts().sort_index().to_string())
df_notif = df_notif.drop(columns=['ano'])

# =============================================================================
# 2. CONSOLIDA ORDENS
# =============================================================================

ordens_2123 = pd.read_csv('/home/claude/ORDENS-CORRETIVAS.csv')
ordens_2024 = pd.read_csv('/home/claude/ORDENS-2024.csv')
ordens_prev = pd.read_csv('/home/claude/ORDENS-PREVENTIVAS.csv')

print(f"\nOrdens corretivas 2021-2023: {len(ordens_2123)}")
print(f"Ordens corretivas/preditivas 2024: {len(ordens_2024)}")
print(f"Ordens preventivas 2021-2024: {len(ordens_prev)}")

# --- Padroniza colunas das corretivas/preditivas ---
# Adiciona campos que preventivas não têm
for df in [ordens_2123, ordens_2024]:
    df['atividade']    = None
    df['duracao_horas'] = df['mttr_horas']

# Preventivas não têm esses campos de corretiva
ordens_prev['id_notificacao']   = None
ordens_prev['data_notificacao'] = None
ordens_prev['data_abertura_om'] = None
ordens_prev['data_inicio_execucao'] = ordens_prev['data_execucao']
ordens_prev['mttr_horas']       = ordens_prev['duracao_horas']
ordens_prev['custo_real']       = None

# Colunas finais padronizadas
COLUNAS_ORDENS = [
    'id_om',
    'id_notificacao',
    'tag_ativo',
    'criticidade',
    'tipo_manutencao',
    'atividade',
    'equipe',
    'tecnico_responsavel',
    'data_notificacao',
    'data_abertura_om',
    'data_inicio_execucao',
    'data_encerramento',
    'mttr_horas',
    'duracao_horas',
    'custo_real',
    'status',
]

for df in [ordens_2123, ordens_2024, ordens_prev]:
    for col in COLUNAS_ORDENS:
        if col not in df.columns:
            df[col] = None

ordens_2123 = ordens_2123[COLUNAS_ORDENS]
ordens_2024 = ordens_2024[COLUNAS_ORDENS]
ordens_prev = ordens_prev[COLUNAS_ORDENS]

# Concatena tudo
df_ordens = pd.concat([ordens_2123, ordens_2024, ordens_prev], ignore_index=True)

# Ordena por data de execução
df_ordens['_data_sort'] = pd.to_datetime(
    df_ordens['data_inicio_execucao'].fillna(df_ordens['data_notificacao'])
)
df_ordens = df_ordens.sort_values('_data_sort').reset_index(drop=True)
df_ordens = df_ordens.drop(columns=['_data_sort'])

# Reindexar IDs
df_ordens['id_om'] = range(1, len(df_ordens) + 1)

print(f"\nTotal ordens consolidadas: {len(df_ordens)}")
print(f"\nPor tipo:")
print(df_ordens['tipo_manutencao'].value_counts().to_string())
print(f"\nPor status:")
print(df_ordens['status'].value_counts().to_string())
print(f"\nPor ano (data execução):")
df_ordens['ano'] = pd.to_datetime(df_ordens['data_inicio_execucao'], errors='coerce').dt.year
print(df_ordens['ano'].value_counts().sort_index().to_string())
df_ordens = df_ordens.drop(columns=['ano'])

print(f"\nCusto total corretivas+preditivas: R$ {df_ordens['custo_real'].sum():,.2f}")
print(f"MTTR médio corretivas: {df_ordens[df_ordens['tipo_manutencao']=='Corretiva']['mttr_horas'].mean():.1f}h")
print(f"MTTR médio preditivas: {df_ordens[df_ordens['tipo_manutencao']=='Preditiva']['mttr_horas'].mean():.1f}h")

# =============================================================================
# 3. EXPORTA
# =============================================================================

df_notif.to_csv('/home/claude/NOTIFICACOES-FINAL.csv', index=False)
df_ordens.to_csv('/home/claude/ORDENS-FINAL.csv', index=False)

print(f"\n✅ NOTIFICACOES-FINAL.csv exportado: {len(df_notif)} linhas")
print(f"✅ ORDENS-FINAL.csv exportado: {len(df_ordens)} linhas")
