# =============================================================================
# GERAÇÃO DA DIMENSÃO CALENDÁRIO
# Fábrica fictícia de água mineral - Planta 1 (pl1)
# =============================================================================
# Cobre o período completo do projeto: 2021-01-01 → 2024-12-31
# =============================================================================

import pandas as pd
from datetime import date

DATA_INICIO = date(2021, 1, 1)
DATA_FIM    = date(2024, 12, 31)

MESES_PT = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março',    4: 'Abril',
    5: 'Maio',    6: 'Junho',     7: 'Julho',     8: 'Agosto',
    9: 'Setembro',10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}

DIAS_PT = {
    0: 'Segunda-feira', 1: 'Terça-feira',  2: 'Quarta-feira',
    3: 'Quinta-feira',  4: 'Sexta-feira',  5: 'Sábado',
    6: 'Domingo'
}

datas = pd.date_range(start=DATA_INICIO, end=DATA_FIM, freq='D')

df = pd.DataFrame({'data': datas})

df['ano']            = df['data'].dt.year
df['mes']            = df['data'].dt.month
df['nome_mes']       = df['data'].dt.month.map(MESES_PT)
df['trimestre']      = df['data'].dt.quarter
df['nome_trimestre'] = 'T' + df['trimestre'].astype(str)
df['semana']         = df['data'].dt.isocalendar().week.astype(int)
df['dia']            = df['data'].dt.day
df['dia_semana']     = df['data'].dt.weekday.map(DIAS_PT)
df['eh_fim_semana']  = df['data'].dt.weekday >= 5
df['ano_mes']        = df['data'].dt.to_period('M').astype(str)
df['data']           = df['data'].dt.strftime('%Y-%m-%d')

print(f"Dimensão calendário gerada: {len(df)} datas")
print(f"Período: {df['data'].min()} → {df['data'].max()}")
print(f"\nPrimeiras linhas:")
print(df.head(5).to_string())

df.to_csv('/home/claude/DIM_CALENDARIO.csv', index=False)
print("\nExportado: DIM_CALENDARIO.csv")
