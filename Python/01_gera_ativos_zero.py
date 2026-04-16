# =============================================================================
# GERAÇÃO DO DATASET DE ATIVOS - DO ZERO
# Fábrica fictícia de água mineral - Planta 1 (pl1)
# =============================================================================
# Este script define a estrutura da planta industrialmente e gera o dataset
# de ativos do zero, sem depender de nenhum arquivo externo.
#
# A fábrica possui 4 setores:
#   - REC (Recebimento): capta água, filtra e encaminha para o processo
#   - ENV (Envase): envasa a água nas garrafas
#   - PAL (Paletização): organiza e paletiza as caixas
#   - UL  (Utilidades): infraestrutura de suporte (ar comprimido, energia, etc.)
#
# Hierarquia de ativos (taxonomia):
#   Nível 3 — Equipamento principal (Bomba, Motor standalone, Compressor...)
#   Nível 4 — Subequipamento/componente funcional (Motor de bomba, Sensor, Válvula...)
#
# Lógica de geração:
#   Cada equipamento nível 3 é definido com seus filhos nível 4.
#   Tags seguem o padrão: pl1-{setor}-{tipo}{n}-{filho}
# =============================================================================
 
import pandas as pd
import numpy as np
from faker import Faker
from datetime import date
 
fake = Faker('pt_BR')
np.random.seed(42)  # Reprodutibilidade
 
PLANTA   = 'pl1'
DATA_MIN = date(2018, 1, 1)
DATA_MAX = date(2021, 12, 31)
 
 
# =============================================================================
# 1. DEFINIÇÃO DA ESTRUTURA DA PLANTA
# =============================================================================
# Cada entrada define um equipamento nível 3 e seus filhos nível 4.
# Estrutura: (tipo_tag, classe, filhos)
# filhos: lista de (sufixo_tag, classe_filho)
 
ESTRUTURA_PLANTA = {
 
    # ------------------------------------------------------------------
    # RECEBIMENTO (rec)
    # Bombas captam água do rio. Cada bomba tem motor, sensor e válvula.
    # Motores standalone têm inversor e sensor de vibração.
    # ------------------------------------------------------------------
    'rec': {
        'equipamentos': [
            # 10 bombas centrífugas, cada uma com motor, sensor de pressão e válvula
            # Recebimento tem mais bombas pois é o setor de captação e filtragem da água
            *[('bb', 'Bomba', [('mtr1', 'Motor Elétrico'),
                               ('sns-p1', 'Sensor'),
                               ('vlv1', 'Válvula')]) for _ in range(10)],
            # 3 motores standalone com inversor e sensor de vibração
            *[('mtr', 'Motor Elétrico', [('inv1', 'Inversor de Frequência'),
                                         ('sns-v1', 'Sensor')]) for _ in range(3)],
            # 2 motores com redutor acoplado (conjuntos de redução de velocidade)
            *[('mtr', 'Motor Elétrico', [('inv1', 'Inversor de Frequência'),
                                         ('red1', 'Redutor'),
                                         ('sns-v1', 'Sensor')]) for _ in range(2)],
            # 6 sensores standalone
            *[('sns', 'Sensor', []) for _ in range(6)],
        ]
    },
 
    # ------------------------------------------------------------------
    # ENVASE (env)
    # Bombas de envase, esteiras, motores, redutores e sensores.
    # ------------------------------------------------------------------
    'env': {
        'equipamentos': [
            # 8 bombas de envase com motor, sensor e válvula
            # Envase tem várias bombas para diferentes linhas de produção
            *[('bb', 'Bomba', [('mtr1', 'Motor Elétrico'),
                               ('sns-p1', 'Sensor'),
                               ('vlv1', 'Válvula')]) for _ in range(8)],
            # 4 esteiras com motor, redutor e sensor
            # Esteiras usam redutor para controle de velocidade da correia
            *[('est', 'Esteira', [('mtr1', 'Motor Elétrico'),
                                  ('red1', 'Redutor'),
                                  ('sns1', 'Sensor')]) for _ in range(4)],
            # 4 motores standalone com inversor, redutor e sensor
            *[('mtr', 'Motor Elétrico', [('inv1', 'Inversor de Frequência'),
                                          ('red1', 'Redutor'),
                                          ('sns-v1', 'Sensor')]) for _ in range(4)],
        ]
    },
 
    # ------------------------------------------------------------------
    # PALETIZAÇÃO (pal)
    # Robôs, paletizadoras, envolvedoras, esteiras e garras.
    # ------------------------------------------------------------------
    'pal': {
        'equipamentos': [
            # 2 robôs com motor e controlador
            *[('rob', 'Robô', [('mtr1', 'Motor Elétrico'),
                               ('ctrl1', 'Controlador')]) for _ in range(2)],
            # 2 paletizadoras com motor e sensor
            *[('pal', 'Paletizadora', [('mtr1', 'Motor Elétrico'),
                                       ('sns1', 'Sensor')]) for _ in range(2)],
            # 2 envolvedoras com motor e sensor
            *[('env', 'Envolvedora', [('mtr1', 'Motor Elétrico'),
                                      ('sns1', 'Sensor')]) for _ in range(2)],
            # 2 esteiras com motor e redutor
            *[('est', 'Esteira', [('mtr1', 'Motor Elétrico'),
                                  ('red1', 'Redutor'),
                                  ('sns1', 'Sensor')]) for _ in range(2)],
            # 2 garras com motor e sensor
            *[('grr', 'Garra', [('mtr1', 'Motor Elétrico'),
                                ('sns1', 'Sensor')]) for _ in range(2)],
        ]
    },
 
    # ------------------------------------------------------------------
    # UTILIDADES (ul)
    # Compressores, válvulas de segurança e sensores de suporte.
    # ------------------------------------------------------------------
    'ul': {
        'equipamentos': [
            # 2 compressores com motor, inversor e válvula de segurança
            *[('cmp', 'Compressor', [('mtr1', 'Motor Elétrico'),
                                     ('inv1', 'Inversor de Frequência'),
                                     ('vlv-sg1', 'Válvula de Segurança')]) for _ in range(2)],
            # 3 compressores com motor, redutor, inversor e válvula de segurança
            # Compressores de alta pressão usam redutor para controle de rotação
            *[('cmp', 'Compressor', [('mtr1', 'Motor Elétrico'),
                                     ('red1', 'Redutor'),
                                     ('inv1', 'Inversor de Frequência'),
                                     ('vlv-sg1', 'Válvula de Segurança')]) for _ in range(3)],
            # 5 bombas de recirculação e utilidades
            *[('bb', 'Bomba', [('mtr1', 'Motor Elétrico'),
                               ('sns-p1', 'Sensor'),
                               ('vlv1', 'Válvula')]) for _ in range(5)],
        ]
    },
}
 
 
# =============================================================================
# 2. NOMES DESCRITIVOS POR CLASSE
# =============================================================================
 
NOMES_CLASSE = {
    'Bomba':                  'Bomba Centrífuga',
    'Motor Elétrico':         'Motor Elétrico',
    'Compressor':             'Compressor',
    'Válvula':                'Válvula de Controle',
    'Válvula de Segurança':   'Válvula de Segurança',
    'Inversor de Frequência': 'Inversor de Frequência',
    'Controlador':            'Controlador',
    'Redutor':                'Redutor',
    'Robô':                   'Robô Industrial',
    'Esteira':                'Esteira Transportadora',
    'Envolvedora':            'Envolvedora',
    'Paletizadora':           'Paletizadora',
    'Garra':                  'Garra Mecânica',
    'Sensor':                 'Sensor',
}
 
SETOR_DESC = {
    'rec': 'Recebimento',
    'env': 'Envase',
    'pal': 'Paletização',
    'ul':  'Utilidades',
}
 
 
# =============================================================================
# 3. GERAÇÃO DOS ATIVOS
# =============================================================================
 
def data_aleatoria():
    """Gera data de instalação aleatória entre 2018 e 2021."""
    delta = (DATA_MAX - DATA_MIN).days
    return DATA_MIN + pd.Timedelta(days=int(np.random.randint(0, delta)))
 
 
def criticidade_aleatoria(classe):
    """
    Define criticidade com base na classe do ativo.
    Equipamentos de processo (Bomba, Motor) tendem a ter criticidade mais alta.
    Sensores e válvulas têm distribuição mais uniforme.
    """
    pesos = {
        'Bomba':                  [0.45, 0.30, 0.25],  # mais crítico
        'Motor Elétrico':         [0.35, 0.40, 0.25],
        'Compressor':             [0.40, 0.20, 0.40],
        'Válvula':                [0.20, 0.45, 0.35],
        'Válvula de Segurança':   [0.00, 0.60, 0.40],
        'Inversor de Frequência': [0.25, 0.50, 0.25],
        'Controlador':            [0.00, 0.00, 1.00],
        'Redutor':                [0.33, 0.33, 0.34],
        'Robô':                   [0.50, 0.50, 0.00],
        'Esteira':                [0.50, 0.50, 0.00],
        'Envolvedora':            [0.00, 1.00, 0.00],
        'Paletizadora':           [0.50, 0.50, 0.00],
        'Garra':                  [0.00, 0.50, 0.50],
        'Sensor':                 [0.35, 0.37, 0.28],
    }
    p = pesos.get(classe, [0.33, 0.33, 0.34])
    return np.random.choice(['A', 'B', 'C'], p=p)
 
 
registros = []
id_ativo = 1
 
for setor, config in ESTRUTURA_PLANTA.items():
    setor_desc = SETOR_DESC[setor]
 
    # Contador por tipo de equipamento dentro do setor
    contadores = {}
 
    for (tipo_tag, classe_pai, filhos) in config['equipamentos']:
 
        # Incrementa contador do tipo
        contadores[tipo_tag] = contadores.get(tipo_tag, 0) + 1
        n = contadores[tipo_tag]
 
        # Tag e nome do equipamento pai (nível 3)
        tag_pai_setor = f"{PLANTA}-{setor}"
        tag_equip     = f"{tag_pai_setor}-{tipo_tag}{n}"
        nome_equip    = f"{NOMES_CLASSE.get(classe_pai, classe_pai)} {n} - {setor_desc}"
 
        registros.append({
            'id_ativo':        id_ativo,
            'tag':             tag_equip,
            'tag_pai':         tag_pai_setor,
            'nivel_taxonomia': 3,
            'classe_ativo':    classe_pai,
            'nome':            nome_equip,
            'setor':           setor,
            'setor_desc':      setor_desc,
            'criticidade':     criticidade_aleatoria(classe_pai),
            'data_instalacao': data_aleatoria(),
            'planta':          PLANTA,
        })
        id_ativo += 1
 
        # Gera filhos (nível 4)
        for (sufixo_filho, classe_filho) in filhos:
            tag_filho  = f"{tag_equip}-{sufixo_filho}"
            nome_filho = f"{NOMES_CLASSE.get(classe_filho, classe_filho)} da {NOMES_CLASSE.get(classe_pai, classe_pai)} {n} - {setor_desc}"
 
            registros.append({
                'id_ativo':        id_ativo,
                'tag':             tag_filho,
                'tag_pai':         tag_equip,
                'nivel_taxonomia': 4,
                'classe_ativo':    classe_filho,
                'nome':            nome_filho,
                'setor':           setor,
                'setor_desc':      setor_desc,
                'criticidade':     criticidade_aleatoria(classe_filho),
                'data_instalacao': data_aleatoria(),
                'planta':          PLANTA,
            })
            id_ativo += 1
 
 
# =============================================================================
# 4. MONTA DATAFRAME E EXPORTA
# =============================================================================
 
df = pd.DataFrame(registros)
 
print(f"Total de ativos gerados: {len(df)}")
print(f"\nDistribuição por classe:")
print(df['classe_ativo'].value_counts().to_string())
print(f"\nDistribuição por setor:")
print(df['setor_desc'].value_counts().to_string())
df.to_csv(r'C:\Users\marce\Downloads\Projeto Dados - Manutenção\Bases\BASE-ATIVOS-LIMPO.csv', index=False)
print("Dataset exportado: BASE-ATIVOS.csv")
