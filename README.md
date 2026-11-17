# SUSEP | Market Share Intelligence

**Inteligência competitiva para o mercado segurador brasileiro, desenvolvida em Power BI a partir de dados públicos da SUSEP.**

O projeto transforma dados do mercado de seguros em uma visão de negócio sobre **participação de mercado, posicionamento competitivo, desempenho técnico e presença regional**. A análise parte de uma seguradora de referência e compara sua atuação com a de concorrentes em **carteiras de produtos equivalentes**.

**Atualização dos dados:** setembro de 2026  
**Ferramenta de visualização:** Microsoft Power BI Desktop  
**Formato disponível:** `.pbix` (relatório com modelo de dados importado)

### [📥 Baixar o dashboard — versão mais recente](https://github.com/isaquepimentel94/susep-market-share-intelligence/releases/latest)

> O relatório está disponível para **download e exploração no Power BI Desktop**, gratuitamente. Não há uma versão interativa hospedada no navegador neste momento. O código do ETL e os notebooks de processamento **não fazem parte desta publicação**.

## Problema de negócio

Comparar a participação de seguradoras no mercado total pode distorcer a análise quando elas atuam em linhas de produtos diferentes. Uma empresa focada em automóveis, por exemplo, não deve ter sua posição competitiva avaliada com base em receitas de produtos que não comercializa.

Este dashboard busca responder a perguntas como:

- Qual é a posição da seguradora em seu **mercado efetivamente comparável**?
- Quanto a separa da próxima colocação e da liderança?
- Quais grupos de ramos sustentam sua participação e quais apresentam crescimento ou retração?
- Como sua **sinistralidade** e sua **margem técnica parcial** se comparam às das concorrentes?
- Em quais estados a seguradora apresenta maior participação, liderança ou perda de espaço?

## Visões do dashboard

| Visão | O que permite analisar |
| --- | --- |
| **Raio-X Competitivo** | Ranking por prêmios diretos, Market Share, distância competitiva, evolução mensal e diagnóstico por grupo de ramos. Alternância entre participação de mercado, sinistralidade e margem técnica parcial. |
| **Competitividade por UF** | Distribuição territorial da atuação, participação por estado, posição no ranking, lideranças e evolução regional. |
| **Guia de Indicadores** | Definições, regras de cálculo, interpretações e fontes utilizadas na leitura do relatório. |

Os indicadores respondem à seleção da seguradora e do período de análise, permitindo observar diferentes cenários competitivos sem alterar o modelo.

## Diferencial metodológico: carteira comparável

A comparação não usa indiscriminadamente todo o mercado segurador. Ela segue o seguinte critério:

1. **Definir a seguradora de referência** e o período analisado.
2. **Identificar os ramos com produção positiva** na carteira dessa seguradora no período de referência.
3. **Aplicar o mesmo conjunto de ramos aos concorrentes**, considerando apenas os prêmios dos produtos abrangidos pela carteira selecionada.
4. **Manter o universo de produtos comparável** nas análises regionais e nas comparações entre períodos.

**Exemplo:** se a seguradora de referência atua em Automóvel, os prêmios de Vida de uma concorrente que também vende Automóvel não entram no cálculo do mercado comparável.

Essa abordagem aproxima o ranking e o Market Share da competição relevante para a seguradora analisada.

## Indicadores e análises

**Participação e posicionamento:** prêmios diretos, Market Share, posição competitiva, distância para a próxima posição e para a liderança, composição e evolução da carteira.

**Desempenho técnico:** sinistralidade, margem técnica parcial e diferenças em relação ao mercado de comparação.

**Competitividade regional:** participação por UF, posições estaduais, presença territorial, lideranças e ganhos ou perdas de Market Share.

**Documentação:** guia com conceitos e critérios que ajudam a interpretar os resultados sem depender do conhecimento prévio das medidas DAX.

## Tecnologias e competências aplicadas

| Tecnologia | Aplicação no projeto |
| --- | --- |
| **Power BI** | Modelo analítico, páginas do relatório, filtros e interações. |
| **DAX** | Indicadores de participação, rankings, comparações temporais e métricas técnicas. |
| **Power Query** | Consumo e preparação dos conjuntos de dados utilizados pelo modelo. |
| **Python / DuckDB / Parquet** | Preparação prévia dos dados para consumo analítico; os arquivos e o código dessa etapa não são publicados nesta versão. |
| **SUSEP** | Fonte pública dos dados do mercado segurador brasileiro. |

## Como explorar o relatório

1. Acesse **[Releases](https://github.com/isaquepimentel94/susep-market-share-intelligence/releases/latest)**.
2. Em **Assets**, baixe o arquivo `.pbix` da versão mais recente.
3. Abra o arquivo no **[Power BI Desktop](https://www.microsoft.com/pt-br/download/details.aspx?id=58494)**.
4. Escolha a seguradora e o intervalo de análise; navegue pelas páginas e alterne entre as métricas disponíveis.

**Observação:** o arquivo disponibilizado inclui os dados importados necessários para a visualização. Para **atualizar a origem dos dados**, seriam necessários os arquivos e caminhos de processamento utilizados no ambiente de desenvolvimento, que não integram este repositório. Não é necessário executar o ETL para explorar a versão publicada.

## Fonte, escopo e ressalvas

- **Fonte:** [Superintendência de Seguros Privados (SUSEP)](https://www.gov.br/susep/pt-br) — dados públicos do mercado supervisionado.
- **Recorte desta versão:** informações disponibilizadas até setembro de 2026; resultados dependem dos filtros escolhidos no relatório.
- **Escopo público:** documentação e arquivo Power BI. Não são disponibilizados notebooks, scripts de extração, arquivos Parquet ou bases intermediárias.
- **Interpretação:** indicadores nacionais e estaduais podem ter granularidades e conceitos diferentes; não devem ser somados ou tratados como equivalentes sem conciliação.

Este é um **projeto independente de portfólio**, sem vínculo ou endosso institucional da SUSEP. As análises têm finalidade informativa e demonstrativa, não constituindo parecer regulatório, auditoria ou recomendação de investimento.
