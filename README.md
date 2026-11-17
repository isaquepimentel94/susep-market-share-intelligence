# SUSEP | Market Share Intelligence

**Projeto de Business Intelligence para análise da competitividade do mercado segurador brasileiro**, desenvolvido em Power BI com dados públicos da Superintendência de Seguros Privados (SUSEP).

**Referência dos dados:** até setembro de 2026.

## Objetivo

Analisar o posicionamento competitivo de uma seguradora de referência em relação ao mercado segurador, considerando sua **carteira comparável de ramos**. O relatório reúne participação de mercado, ranking competitivo, indicadores técnicos e distribuição territorial.

## Visões do relatório

- **Raio-X Competitivo:** participação de mercado, prêmios diretos, ranking e distância competitiva, com alternância entre Market Share, Sinistralidade e Margem Técnica Parcial.
- **Competitividade Regional:** atuação e posicionamento por unidade da Federação, incluindo participação, liderança e evolução regional.
- **Guia de Indicadores:** definições, interpretações, fontes e regras metodológicas para leitura dos resultados.

## Metodologia

O mercado comparável é delimitado pelos ramos da carteira da seguradora de referência. As seguradoras concorrentes são avaliadas **somente pelos prêmios dos ramos pertinentes à carteira analisada**, evitando comparações com produtos fora do universo selecionado.

Os indicadores técnicos e geográficos podem utilizar bases com granularidades e conceitos diferentes. Os resultados devem ser interpretados no contexto de cada indicador, sem somar indiscriminadamente as fontes nacional e estadual.

## Tecnologias e fonte

- Power BI — modelagem, relatórios e visualização
- DAX — indicadores, contextos de filtro, rankings e comparações temporais
- SUSEP — dados públicos de mercado

## Visualizar o projeto

**[Abrir a página de apresentação do portfólio](https://isaquepimentel94.github.io/susep-market-share-intelligence/)**

A página apresenta a metodologia, as visões e as capturas de tela adicionadas ao repositório. **Esta publicação é uma demonstração visual estática**, não uma hospedagem do relatório interativo do Power BI.

## Capturas de tela

Para exibir imagens de setembro/2026 na página, adicione na pasta `assets/` os arquivos abaixo, mantendo exatamente os nomes:

- `raio-x-market-share.png`
- `raio-x-sinistralidade.png`
- `raio-x-margem.png`
- `competitividade-uf.png`
- `guia-indicadores.png`

A página detecta e mostra automaticamente as imagens que estiverem presentes.

## Escopo do repositório

Apenas apresentação do painel. **Não estão publicados** notebooks de ETL, arquivos Parquet, bases de dados, scripts de extração ou o arquivo `.pbix`.

**Nota:** projeto independente de portfólio, sem vínculo oficial com a SUSEP. Os resultados não constituem parecer regulatório nem recomendação de investimento.
