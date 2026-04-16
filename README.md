Riverflow | Pipeline de Dados para Confiabilidade e Performance
O Riverflow é um projeto de engenharia de dados end-to-end que simula o ecossistema de uma planta de tratamento de água. O objetivo é demonstrar o fluxo completo da informação: desde a geração de dados brutos (simulando um ERP) até a entrega de dashboards estratégicos para tomada de decisão em Manutenção e Confiabilidade.

🏗️ A Arquitetura do Projeto
O projeto foi estruturado em quatro camadas principais:

1. Simulação de Dados (Python)
Para garantir um cenário realista de 3 anos de histórico, utilizei Python para simular o comportamento dos ativos.

Lógica de Falhas: Aplicação de Distribuição de Weibull para modelar o tempo entre falhas (MTBF), permitindo simular diferentes estágios de vida dos equipamentos (mortalidade infantil, falhas aleatórias e desgaste).

Priorização: Uso do Princípio de Pareto para distribuir custos e criticidade entre os ativos.

Outputs: Geração de tabelas de Ordens de Manutenção (OM), Notas de Manutenção e Registros de Custos.

2. Modelagem de Dados (SQL & Star Schema)
Os dados brutos foram estruturados em um banco de dados seguindo o modelo Star Schema (Esquema Estrela), garantindo performance e integridade:

Fato: Ordens de Manutenção e Custos.

Dimensões: Ativos (Bombas, Motores, Painéis), Localização Industrial e uma Dimensão Calendário robusta para análises temporais.

3. Camada de Inteligência (SQL Views)
Em vez de processar cálculos no BI, a inteligência foi embarcada no SQL através de Views complexas para o cálculo de KPIs de Classe Mundial:

Confiabilidade: MTBF, MTTR e Disponibilidade Inerente/Operacional.

Operacional: Backlog, Aderência ao Cronograma Semanal (HH Planejado vs. Executado).

Financeiro: Evolução de custos (Corretiva vs. Preventiva).

4. Visualização de Dados (Tableau)
A entrega final consiste em um Dashboard dinâmico dividido em três perspectivas:

Painel de Confiabilidade: Foco técnico em engenharia de ativos.

Painel Operacional: Gestão do dia a dia para o PCM e Supervisão.

Painel de Custos: Visão executiva para controle orçamentário.

🚀 Como Explorar
SQL: As queries de criação das tabelas e KPIs estão na pasta /scripts_sql.

Python: O notebook de simulação está em /data_simulation.

Dashboard: [Link para o seu Tableau Public aqui]
