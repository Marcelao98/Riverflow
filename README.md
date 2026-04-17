
Riverflow | Pipeline de Dados para Confiabilidade e Performance
O Riverflow é um projeto de engenharia de dados end-to-end que simula o ecossistema de uma planta de tratamento de água. O objetivo é demonstrar o fluxo completo da informação: desde a geração de dados brutos até a entrega de dashboards estratégicos para tomada de decisão em Manutenção e Confiabilidade.

🏗️ A Arquitetura do Projeto
O projeto foi estruturado em três camadas principais, integrando engenharia, estatística e tecnologia:

![Fluxograma do Pipeline](https://github.com/Marcelao98/Riverflow/blob/main/Imagens/fluxograma-removebg-preview.png?raw=true)

1. Camada de Simulação (Python)
Para garantir um cenário realista de 3 anos de histórico, utilizei Python para simular o comportamento físico e operacional dos ativos:

Lógica de Falhas: Aplicação de Distribuição de Weibull para modelar o tempo entre falhas (MTBF), simulando diferentes estágios de vida dos equipamentos (mortalidade infantil, falhas aleatórias e desgaste).

Priorização: Uso do Princípio de Pareto para distribuição de custos e criticidade.

Outputs: Geração de tabelas de Ordens de Manutenção (OM), Notas e Registros de Custos (CSV).

2. Camada de Engenharia e Inteligência (SQL)
Nesta etapa, o dado bruto foi transformado em ativos de decisão. Concentrei toda a lógica de negócio e estruturação diretamente no banco de dados:

Modelagem Star Schema: Estruturação de um Data Warehouse com tabelas de Fato (Ordens e Notas) e Dimensões (Ativos, Calendário e Localização), garantindo performance analítica.

Cálculo de KPIs via Views: Inteligência embarcada em SQL para cálculo de indicadores de classe mundial: MTBF, MTTR, Disponibilidade, Backlog e aderência ao planejamento (HH).

![Diagrama Star Schema](https://github.com/Marcelao98/Riverflow/blob/main/Imagens/diagrama.jpg?raw=true)

3. Camada de Visualização (Tableau BI)
A entrega final consiste em um ecossistema de dashboards dinâmicos, permitindo o drill-down do estratégico ao operacional:

Dashboard de Performance: Visões integradas de Confiabilidade (engenharia), Operacional (PCM) e Custos (gestão financeira).

![Dashboard Riverflow - Visão Geral](https://github.com/Marcelao98/Riverflow/blob/main/Imagens/vis%C3%A3ogeral.jpg?raw=true)
🚀 Como Explorar
Simulação: O script de geração dos dados está em /data_simulation.

Engenharia/SQL: As queries de modelagem e Views de inteligência estão em /scripts_sql.

Dashboard Interativo: [Acesse o projeto no Tableau Public aqui]
