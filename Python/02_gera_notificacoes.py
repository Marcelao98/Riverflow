import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta

fake = Faker('pt_BR')
np.random.seed(42)

DATA_INICIO  = datetime(2022, 1, 1)
DATA_FIM     = datetime(2024, 12, 31)
PERIODO_DIAS = (DATA_FIM - DATA_INICIO).days  # ~1095 dias

# =============================================================================
# 1. CARREGA BASE DE ATIVOS
# =============================================================================

df_ativos = pd.read_csv('/home/claude/BASE-ATIVOS-LIMPO.csv')
print(f'Ativos carregados: {len(df_ativos)}')

# =============================================================================
# 2. PARÂMETROS DE FALHA POR CLASSE
# =============================================================================

PARAMS_FALHA = {
    'Motor Elétrico': {
        'pf': 0.50, 'beta_inf': 1.8, 'beta_sup': 3.0,
        'qtd_falhas': 77, 'perfil': 'DESGASTE',
        'modos': [
            ('Falha de rolamento', 0.45),
            ('Falha de enrolamento / isolação', 0.25),
            ('Falha mecânica (eixo/acoplamento)', 0.12),
            ('Contaminação / umidade', 0.10),
            ('Superaquecimento', 0.08),
        ]
    },
    'Sensor': {
        'pf': 0.20, 'beta_inf': 0.8, 'beta_sup': 1.2,
        'qtd_falhas': 30, 'perfil': 'ALEATÓRIO',
        'modos': [
            ('Deriva de sinal / perda de calibração', 0.35),
            ('Falha de conexão elétrica', 0.25),
            ('Dano físico (vibração/impacto)', 0.20),
            ('Falha de componente eletrônico', 0.12),
            ('Contaminação (poeira, umidade)', 0.08),
        ]
    },
    'Válvula': {
        'pf': 0.50, 'beta_inf': 1.5, 'beta_sup': 2.5,
        'qtd_falhas': 35, 'perfil': 'DESGASTE',
        'modos': [
            ('Vazamento interno / externo', 0.38),
            ('Falha ao abrir/fechar sob demanda', 0.28),
            ('Falha de curso parcial', 0.16),
            ('Corrosão / erosão', 0.12),
            ('Travamento mecânico / atrito excessivo', 0.06),
        ]
    },
    'Bomba': {
        'pf': 0.80, 'beta_inf': 0.9, 'beta_sup': 1.5,
        'qtd_falhas': 56, 'perfil': 'MISTO',
        'modos': [
            ('Falha de selo mecânico / vazamento', 0.40),
            ('Falha de rolamento', 0.25),
            ('Dano ao impelidor (erosão/cavitação)', 0.15),
            ('Bloqueio / restrição de fluxo', 0.12),
            ('Desalinhamento de eixo / vibração', 0.08),
        ]
    },
    'Inversor de Frequência': {
        'pf': 0.10, 'beta_inf': 0.8, 'beta_sup': 1.2,
        'qtd_falhas': 4, 'perfil': 'ALEATÓRIO',
        'modos': [
            ('Falha do módulo IGBT', 0.38),
            ('Degradação do capacitor (barramento DC)', 0.22),
            ('Superaquecimento / bloqueio do resfriamento', 0.18),
            ('Falha da placa de controle / firmware', 0.12),
            ('Falha do retificador de entrada', 0.10),
        ]
    },
    'Esteira': {
        'pf': 0.30, 'beta_inf': 1.5, 'beta_sup': 2.5,
        'qtd_falhas': 6, 'perfil': 'DESGASTE',
        'modos': [
            ('Falha de caixa de redução (desgaste de dentes)', 0.35),
            ('Falha de rolamento (polias/acionamento)', 0.28),
            ('Desgaste / dano estrutural da correia', 0.20),
            ('Falha elétrica do motor', 0.10),
            ('Dano em acoplamento / eixo', 0.07),
        ]
    },
    'Compressor': {
        'pf': 0.20, 'beta_inf': 1.2, 'beta_sup': 2.5,
        'qtd_falhas': 3, 'perfil': 'DESGASTE',
        'modos': [
            ('Falha de rolamento', 0.35),
            ('Falha de válvula (sucção/descarga)', 0.25),
            ('Vazamento de vedação / gaxeta', 0.18),
            ('Dano ao rotor / impelidor', 0.12),
            ('Falha do sistema de resfriamento', 0.10),
        ]
    },
    'Redutor': {
        'pf': 0.50, 'beta_inf': 2.0, 'beta_sup': 3.5,
        'qtd_falhas': 23, 'perfil': 'DESGASTE',
        'modos': [
            ('Fadiga / micropitting de dente de engrenagem', 0.40),
            ('Falha de rolamento', 0.30),
            ('Falha de eixo', 0.15),
            ('Vazamento de vedação / óleo', 0.10),
            ('Dano ao cárter / carcaça', 0.05),
        ]
    },
    'Robô': {
        'pf': 0.15, 'beta_inf': 1.0, 'beta_sup': 2.5,
        'qtd_falhas': 1, 'perfil': 'MISTO',
        'modos': [
            ('Erro posicional (desgaste harmonic drive)', 0.35),
            ('Falha de servo motor / encoder', 0.25),
            ('Falha de sensor / fiação', 0.20),
            ('Falha do controlador / software', 0.12),
            ('Dano mecânico (colisão, sobrecarga)', 0.08),
        ]
    },
    'Controlador': {
        'pf': 0.10, 'beta_inf': 0.8, 'beta_sup': 1.1,
        'qtd_falhas': 1, 'perfil': 'ALEATÓRIO',
        'modos': [
            ('Falha de placa de I/O', 0.30),
            ('Falha de fonte de alimentação', 0.25),
            ('Falha de comunicação / rede', 0.20),
            ('Falha de CPU / memória', 0.15),
            ('Superaquecimento', 0.10),
        ]
    },
    'Garra': {
        'pf': 0.10, 'beta_inf': 1.5, 'beta_sup': 2.5,
        'qtd_falhas': 1, 'perfil': 'DESGASTE',
        'modos': [
            ('Desgaste dos dedos de contato', 0.35),
            ('Falha do atuador pneumático/elétrico', 0.28),
            ('Falha de sensor de presença/força', 0.20),
            ('Dano estrutural (queda, colisão)', 0.12),
            ('Falha de fiação / conector', 0.05),
        ]
    },
    'Paletizadora': {
        'pf': 0.10, 'beta_inf': 1.2, 'beta_sup': 2.0,
        'qtd_falhas': 1, 'perfil': 'DESGASTE',
        'modos': [
            ('Falha de motor / redutor', 0.33),
            ('Falha de sensor / fim de curso', 0.23),
            ('Desgaste mecânico (corrente, guia, fuso)', 0.20),
            ('Falha pneumática', 0.14),
            ('Falha elétrica / fiação', 0.10),
        ]
    },
    'Válvula de Segurança': {
        'pf': 0.15, 'beta_inf': 1.0, 'beta_sup': 1.8,
        'qtd_falhas': 3, 'perfil': 'MISTO',
        'modos': [
            ('Falha ao abrir sob demanda (FTO)', 0.35),
            ('Vazamento de sede / falha ao resentar após atuação', 0.28),
            ('Deriva de set point (relaxamento de mola)', 0.18),
            ('Abertura espúria / chattering', 0.12),
            ('Dano mecânico a disco ou sede', 0.07),
        ]
    },
    'Envolvedora': {
        'pf': 0.20, 'beta_inf': 1.2, 'beta_sup': 2.0,
        'qtd_falhas': 1, 'perfil': 'DESGASTE',
        'modos': [
            ('Falha do sistema de selagem / resistência', 0.35),
            ('Desgaste mecânico (corrente, fuso, guia)', 0.28),
            ('Falha de motor / acionamento', 0.18),
            ('Falha de sensor / fim de curso', 0.12),
            ('Obstrução / rasgo de filme', 0.07),
        ]
    },
}

# =============================================================================
# 3. TEMPLATES DE DESCRIÇÃO POR MODO DE FALHA
# =============================================================================
# Textos realistas simulando o que um técnico escreveria no SAP

DESCRICOES = {
    'Falha de rolamento':                        ['rolamento com ruído anormal', 'vibração elevada no mancal', 'temperatura alta no rolamento', 'rolamento travado'],
    'Falha de enrolamento / isolação':            ['motor não parte - enrolamento queimado', 'fuga à terra no estator', 'curto no enrolamento', 'resistência de isolação baixa'],
    'Falha mecânica (eixo/acoplamento)':          ['acoplamento partido', 'eixo com folga excessiva', 'vibração alta - verificar acoplamento'],
    'Contaminação / umidade':                     ['motor com entrada de água', 'contaminação interna por poeira', 'umidade no terminal de ligação'],
    'Superaquecimento':                           ['motor desarmando por temperatura', 'proteção térmica atuando', 'motor muito quente ao toque'],
    'Deriva de sinal / perda de calibração':      ['sinal fora do esperado', 'leitura incorreta - calibrar sensor', 'sensor com deriva de zero'],
    'Falha de conexão elétrica':                  ['sensor sem sinal - verificar fiação', 'cabo danificado no sensor', 'conector solto no sensor'],
    'Dano físico (vibração/impacto)':             ['sensor danificado por impacto', 'sensor quebrado por vibração excessiva'],
    'Falha de componente eletrônico':             ['placa do sensor queimada', 'sensor sem resposta - componente interno'],
    'Contaminação (poeira, umidade)':             ['sensor com lente suja', 'umidade interna no sensor'],
    'Vazamento interno / externo':                ['válvula com vazamento externo', 'gotejamento no corpo da válvula', 'vazamento pela gaxeta'],
    'Falha ao abrir/fechar sob demanda':          ['válvula não abre ao comando', 'válvula travada na posição fechada', 'atuador sem resposta'],
    'Falha de curso parcial':                     ['válvula não atinge posição 100%', 'curso limitado - verificar atuador'],
    'Corrosão / erosão':                          ['corpo da válvula com corrosão avançada', 'erosão na sede da válvula'],
    'Travamento mecânico / atrito excessivo':     ['válvula com esforço excessivo para operar', 'haste travada'],
    'Falha de selo mecânico / vazamento':         ['selo mecânico com vazamento', 'bomba perdendo produto pelo eixo', 'gaxeta danificada'],
    'Falha de rolamento':                         ['rolamento da bomba com ruído', 'vibração anormal na bomba'],
    'Dano ao impelidor (erosão/cavitação)':       ['cavitação na bomba', 'impelidor desgastado - perda de vazão', 'ruído de cavitação'],
    'Bloqueio / restrição de fluxo':              ['bomba sem vazão - verificar filtro', 'sucção bloqueada'],
    'Desalinhamento de eixo / vibração':          ['vibração alta na bomba - verificar alinhamento', 'desalinhamento motor-bomba'],
    'Falha do módulo IGBT':                       ['inversor desarmando - falha IGBT', 'módulo de potência queimado'],
    'Degradação do capacitor (barramento DC)':    ['inversor com alarme de barramento DC', 'capacitor com falha interna'],
    'Superaquecimento / bloqueio do resfriamento':['inversor desligando por temperatura', 'filtro do ventilador entupido'],
    'Falha da placa de controle / firmware':      ['inversor sem comunicação', 'parâmetros perdidos no inversor'],
    'Falha do retificador de entrada':            ['inversor sem tensão no barramento', 'falha na entrada do inversor'],
    'Falha de caixa de redução (desgaste de dentes)': ['ruído na caixa de redução', 'desgaste nos dentes da engrenagem'],
    'Falha de rolamento (polias/acionamento)':    ['rolamento da polia com ruído', 'vibração na polia de acionamento'],
    'Desgaste / dano estrutural da correia':      ['correia com desgaste excessivo', 'correia partida', 'correia com fissuras'],
    'Falha elétrica do motor':                    ['motor da esteira sem partir', 'proteção elétrica do motor atuando'],
    'Dano em acoplamento / eixo':                 ['acoplamento da esteira danificado', 'eixo com folga'],
    'Falha de válvula (sucção/descarga)':         ['válvula de sucção do compressor com folga', 'válvula de descarga travada'],
    'Vazamento de vedação / gaxeta':              ['gaxeta do compressor com vazamento', 'vedação de eixo danificada'],
    'Dano ao rotor / impelidor':                  ['rotor com desgaste', 'impelidor do compressor danificado'],
    'Falha do sistema de resfriamento':           ['compressor desarmando por temperatura', 'radiador entupido'],
    'Fadiga / micropitting de dente de engrenagem': ['ruído anormal no redutor', 'engrenagem com desgaste por fadiga', 'vibração elevada no redutor'],
    'Falha de eixo':                              ['eixo do redutor com trinca', 'quebra de eixo no redutor'],
    'Vazamento de vedação / óleo':                ['vazamento de óleo no redutor', 'nível de óleo abaixo do mínimo'],
    'Dano ao cárter / carcaça':                   ['carcaça do redutor trincada', 'dano no cárter por impacto'],
    'Erro posicional (desgaste harmonic drive)':  ['robô fora de posição', 'erro de posicionamento no eixo'],
    'Falha de servo motor / encoder':             ['alarme de encoder no robô', 'servo motor sem resposta'],
    'Falha de sensor / fiação':                   ['sensor do robô sem sinal', 'fiação danificada no braço'],
    'Falha do controlador / software':            ['CLP do robô em falha', 'programa corrompido no controlador'],
    'Dano mecânico (colisão, sobrecarga)':        ['robô colidiu com estrutura', 'sobrecarga mecânica no eixo'],
    'Falha de placa de I/O':                      ['entrada digital sem resposta no CLP', 'placa de I/O com falha'],
    'Falha de fonte de alimentação':              ['CLP sem tensão de alimentação', 'fonte do painel queimada'],
    'Falha de comunicação / rede':                ['CLP sem comunicação com supervisório', 'rede profibus com falha'],
    'Falha de CPU / memória':                     ['CLP em modo de falha - CPU', 'memória do CLP corrompida'],
    'Desgaste dos dedos de contato':              ['garra com desgaste nos dedos', 'perda de preensão na garra'],
    'Falha do atuador pneumático/elétrico':       ['atuador da garra sem pressão', 'atuador elétrico sem resposta'],
    'Falha de sensor de presença/força':          ['sensor de presença da garra sem sinal', 'célula de carga com leitura errada'],
    'Dano estrutural (queda, colisão)':           ['garra danificada por queda', 'estrutura da garra deformada por colisão'],
    'Falha de motor / redutor':                   ['motor da paletizadora sem partir', 'redutor da paletizadora com ruído'],
    'Falha de sensor / fim de curso':             ['fim de curso não acionando', 'sensor de posição sem sinal'],
    'Desgaste mecânico (corrente, guia, fuso)':   ['corrente da paletizadora com desgaste', 'guia linear com folga excessiva'],
    'Falha pneumática':                           ['cilindro pneumático sem pressão', 'vazamento na linha pneumática'],
    'Falha elétrica / fiação':                    ['curto na fiação do painel', 'disjuntor desarmando sem causa aparente'],
    'Falha ao abrir sob demanda (FTO)':           ['válvula de segurança não abriu no teste', 'mola travada - válvula não alivia'],
    'Vazamento de sede / falha ao resentar após atuação': ['válvula de segurança vazando após teste', 'sede com dano - não veda após atuação'],
    'Deriva de set point (relaxamento de mola)':  ['válvula aliviando abaixo da pressão de set', 'mola com relaxamento - pressão de abertura baixa'],
    'Abertura espúria / chattering':              ['válvula de segurança abrindo sem sobrepressão', 'chattering na válvula de alívio'],
    'Dano mecânico a disco ou sede':              ['partículas no fluido danificaram a sede', 'disco da válvula de segurança com erosão'],
    'Falha do sistema de selagem / resistência':  ['resistência de selagem queimada', 'sistema de solda sem temperatura'],
    'Desgaste mecânico (corrente, fuso, guia)':   ['fuso da envolvedora com desgaste', 'corrente de acionamento esticada'],
    'Falha de motor / acionamento':               ['motor da envolvedora sem partir', 'acionamento sem resposta'],
    'Obstrução / rasgo de filme':                 ['filme rasgando na envolvedora', 'obstrução no rolo de filme'],
}

def gerar_descricao(modo_falha):
    """Sorteia uma descrição realista para o modo de falha."""
    opcoes = DESCRICOES.get(modo_falha)
    if opcoes:
        return np.random.choice(opcoes)
    return modo_falha.lower()

# =============================================================================
# 4. DISTRIBUIÇÃO PARETO (30/70) POR CLASSE
# =============================================================================

def distribuir_falhas_pareto(ids_ativos, qtd_total):
    """
    Distribui qtd_total falhas entre os ativos seguindo Pareto 30/70:
    ~30% dos ativos recebem ~70% das falhas.
    Retorna dict {id_ativo: qtd_falhas}.
    """
    n = len(ids_ativos)
    if n == 0 or qtd_total == 0:
        return {}

    ids = list(ids_ativos)
    np.random.shuffle(ids)

    # 30% críticos recebem 70% das falhas
    n_criticos = max(1, round(n * 0.30))
    qtd_criticos = round(qtd_total * 0.70)
    qtd_normais  = qtd_total - qtd_criticos

    criticos = ids[:n_criticos]
    normais  = ids[n_criticos:]

    dist = {}

    # Distribui falhas nos críticos com pesos aleatórios
    if qtd_criticos > 0 and criticos:
        pesos = np.random.dirichlet(np.ones(len(criticos)))
        for ativo, peso in zip(criticos, pesos):
            dist[ativo] = max(1, round(peso * qtd_criticos))

    # Distribui falhas nos normais
    if qtd_normais > 0 and normais:
        pesos = np.random.dirichlet(np.ones(len(normais)))
        for ativo, peso in zip(normais, pesos):
            n_falhas = round(peso * qtd_normais)
            if n_falhas > 0:
                dist[ativo] = dist.get(ativo, 0) + n_falhas

    # Ajusta para bater exatamente qtd_total
    total_atual = sum(dist.values())
    diff = qtd_total - total_atual
    if diff != 0 and dist:
        ativo_ajuste = max(dist, key=dist.get)
        dist[ativo_ajuste] += diff
        if dist[ativo_ajuste] <= 0:
            dist[ativo_ajuste] = 1

    return dist

# =============================================================================
# 5. GERAÇÃO DAS NOTIFICAÇÕES
# =============================================================================

# Classes com mortalidade infantil (falhas de startup nos primeiros 60 dias)
# Representa problemas de comissionamento, configuração inicial, etc.
CLASSES_INFANTIL = {
    'Sensor':               0.15,  # 15% das falhas são infantis
    'Motor Elétrico':       0.08,
    'Inversor de Frequência': 0.20,
    'Controlador':          0.25,
}

def gerar_data_falha_weibull(beta):
    """
    Gera tempo até falha (em dias) via Weibull com eta calibrado.
    A mediana é posicionada em ~60% do período para distribuição natural.
    Retorna None se a falha cair fora do período (será descartada).
    """
    # Posiciona a mediana em 60% do período
    # eta = t_mediana / (ln(2))^(1/beta)
    t_mediana = PERIODO_DIAS * 0.60
    eta = t_mediana / (np.log(2) ** (1.0 / beta))

    tempo = eta * np.random.weibull(beta)

    # Descarta falhas fora do período (sem truncar — evita spike no fim)
    if tempo > PERIODO_DIAS:
        return None
    return int(tempo)

def gerar_data_falha_infantil():
    """
    Gera falha de mortalidade infantil nos primeiros 60 dias.
    Usa Weibull com beta baixo (0.4) — taxa de falha decrescente.
    """
    beta_inf = 0.4
    eta_inf  = 30  # mediana em ~24 dias
    tempo = eta_inf * np.random.weibull(beta_inf)
    tempo = min(tempo, 60)  # limita a 60 dias de startup
    return int(tempo)

def gerar_data_falha(data_instalacao_str, beta, classe=''):
    """
    Gera data de falha combinando:
    - Mortalidade infantil (startup): primeiros 60 dias, para classes elétricas
    - Weibull normal: resto do período
    Retorna None se a falha cair fora do período.
    """
    prob_infantil = CLASSES_INFANTIL.get(classe, 0.0)

    if np.random.random() < prob_infantil:
        tempo_dias = gerar_data_falha_infantil()
    else:
        tempo_dias = gerar_data_falha_weibull(beta)
        if tempo_dias is None:
            return None

    return DATA_INICIO + timedelta(days=tempo_dias)


notificacoes = []
id_notif = 1

for classe, params in PARAMS_FALHA.items():

    # Filtra ativos da classe no dataset
    # Mapeia nome da classe (pode ter variações entre params e dataset)
    ativos_classe = df_ativos[df_ativos['classe_ativo'] == classe]

    if len(ativos_classe) == 0:
        # Tenta match parcial (ex: 'Bomba' vs 'Bomba Centrífuga' não existe aqui,
        # mas garante robustez)
        print(f"  [AVISO] Nenhum ativo encontrado para classe: {classe}")
        continue

    qtd_falhas = int(round(params['qtd_falhas']))
    modos      = params['modos']
    beta_inf   = params['beta_inf']
    beta_sup   = params['beta_sup']

    # Distribui falhas entre ativos (Pareto 30/70)
    dist_falhas = distribuir_falhas_pareto(
        ativos_classe['id_ativo'].tolist(),
        qtd_falhas
    )

    for id_ativo, n_falhas in dist_falhas.items():

        # Recupera dados do ativo
        ativo = ativos_classe[ativos_classe['id_ativo'] == id_ativo].iloc[0]

        for _ in range(n_falhas):

            # Sorteia beta dentro do range da classe
            beta = np.random.uniform(beta_inf, beta_sup)

            # Gera data da falha — tenta até 5x se cair fora do período
            data_falha = None
            for _ in range(5):
                data_falha = gerar_data_falha(ativo['data_instalacao'], beta, classe)
                if data_falha is not None:
                    break
            if data_falha is None:
                continue  # descarta essa falha se não convergiu

            # Sorteia modo de falha
            modos_desc  = [m[0] for m in modos]
            modos_probs = [m[1] for m in modos]
            modo_falha  = np.random.choice(modos_desc, p=modos_probs)

            # Gera descrição realista
            descricao = gerar_descricao(modo_falha)

            notificacoes.append({
                'id_notificacao':   id_notif,
                'id_ativo':         id_ativo,
                'tag_ativo':        ativo['tag'],
                'classe_ativo':     classe,
                'setor':            ativo['setor'],
                'setor_desc':       ativo['setor_desc'],
                'criticidade':      ativo['criticidade'],
                'data_notificacao': data_falha.strftime('%Y-%m-%d'),
                'tipo_manutencao':  'Corretiva',
                'modo_falha':       modo_falha,
                'descricao':        descricao,
            })

            id_notif += 1

# =============================================================================
# 6. MONTA DATAFRAME E EXPORTA
# =============================================================================

df_notif = pd.DataFrame(notificacoes)
df_notif = df_notif.sort_values('data_notificacao').reset_index(drop=True)

print(f"\nTotal de notificações geradas: {len(df_notif)}")
print(f"\nPor classe:")
print(df_notif['classe_ativo'].value_counts().to_string())
print(f"\nPor setor:")
print(df_notif['setor_desc'].value_counts().to_string())
print(f"\nPrimeiras notificações:")
print(df_notif.head(10).to_string())

df_notif.to_csv('/home/claude/NOTIFICACOES-CORRETIVAS.csv', index=False)
print("\nDataset exportado: NOTIFICACOES-CORRETIVAS.csv")
