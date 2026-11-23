# Paridade de Fusão e Aquisição

## Fonte e escopo

A página web ocupa a aba existente `#fusao-aquisicao`. A referência foi a página PBIR `0f0b767feb40200900a6` da cópia de posição estável do PBIX, preservada separadamente. Executei consultas sobre as medidas gravadas no Power BI Desktop, sem redefinir medidas ou salvar mudanças no PBIX. Os seus 15 visuais e a definição da página são idênticos aos do relatório original.

| Componentes do PBIR | Quantidade | Correspondência na web |
|---|---:|---|
| Seletores de seguradora A, seguradora B, mês inicial e mês final | 4 | Controles de seleção única. Os meses são compartilhados. |
| Seletor oculto de entidade | 1 | Referência compartilhada escolhida no Início. |
| Grupos de cartões de posição da referência, entidade resultante e concentração | 3 | Nove indicadores, em três grupos. |
| Tabelas por UF e grupo de ramos | 2 | Colunas, totais, ordenação e filtro cruzado. |
| Cartões de referência em análise e cobertura dos dados | 2 | Identificação da entidade e cobertura até setembro de 2026. |
| Textos de título, introdução e fonte | 3 | Cabeçalho e rodapé da página. |

## Cenário salvo

Caixa Seguradora `05631`, Allianz `05177` como A, Mapfre `06238` como B e período jan–set/2026. Os valores DAX abaixo foram conferidos no Desktop e os valores web vieram de consultas aos Parquets vigentes. [Consultas de referência](./tests/ma_referencia.dax)

| Indicador | Power BI Desktop | Web |
|---|---:|---:|
| Posição atual da referência | 12ª | 12ª |
| Posição da referência após M&A | 11ª | 11ª |
| Variação de posição | +1 | +1 |
| Posição da entidade resultante | 2ª | 2ª |
| Prêmios A | R$ 6.542.993.339,14 | R$ 6.542.993.339,14 |
| Prêmios B | R$ 3.363.501.362,12 | R$ 3.363.501.362,12 |
| Prêmios combinados | R$ 9.906.494.701,26 | R$ 9.906.494.701,26 |
| Mercado da carteira | R$ 84.243.304.989,16 | R$ 84.243.304.989,16 |
| Participação combinada | 11,75938516% | 11,75938516% |
| HHI antes | 691,74063216 | 691,74063216 |
| HHI após | 753,75999336 | 753,75999336 |
| Variação do HHI | +62,01936120 pts | +62,01936120 pts |

Os cartões compactam os prêmios para **9,91 Bi**, exibem a participação como **11,76%**, os HHIs como **691,74** e **753,76** e a diferença como **+62,019 pts**. O cartão de prêmios permite consultar o valor em reais com centavos.

### Tabelas

A consulta DAX retornou **27 UFs** e **sete grupos**. Os totais correspondem à reavaliação de cada medida no contexto geral da tabela. O total por UF pode diferir da soma das linhas, pois a cesta de ramos é reavaliada em cada UF.

| Linha conferida no Desktop e na web | Prêmios combinados | Mercado | Participação | Δ HHI |
|---|---:|---:|---:|---:|
| Acre | R$ 12.870.084,99 | R$ 53.131.403,45 | 24,22% | +0,328 pts |
| Amapá | R$ 3.518.236,26 | R$ 37.459.928,62 | 9,39% | 0,000 pts |
| São Paulo | R$ 3.642.024.864,99 | R$ 32.951.718.234,21 | 11,05% | +61,080 pts |
| Automóvel | R$ 7.679.118.526,26 | R$ 40.231.285.324,31 | 19,09% | +151,283 pts |
| Total de cada tabela, sem seleção de linha | R$ 9.906.494.701,26 | R$ 84.243.304.989,16 | 11,76% | +62,019 pts |

Em Automóvel, o prêmio de referência foi R$ 500.253.789,70, o de A foi R$ 5.420.451.903,02 e o de B foi R$ 2.258.666.623,24. A razão `Combinado / Referência` foi 1.535,04%. Riscos Financeiros e Crédito aparecem com prêmio de referência igual a zero e os valores da operação em branco. A ordenação inicial da tabela de grupos é decrescente pelo prêmio de B.

## Escopos e regras

- A consulta filtra o fato UF pelo intervalo inclusivo. A cesta usa os ramos com prêmio líquido da referência de valor absoluto superior a R$ 0,01 no contexto da medida. Uma seleção explícita de entidade tem precedência sobre o grupo econômico histórico. Os fatos nacional e UF permanecem separados.
- Os dois seletores da operação são independentes da referência e aceitam repetir uma seguradora. A e B iguais deixam os resultados combinados e os efeitos da operação em branco, preservando os prêmios individuais e os indicadores anteriores à operação.
- As posições mantêm a comparação estrita. A posição anterior compara os prêmios em centavos e exclui explicitamente a referência. Para o cenário posterior, A e B saem da relação de concorrentes e a resultante entra uma vez. Quando a operação inclui a própria referência, a posição posterior segue a da entidade resultante conforme o DAX.
- O HHI usa shares em **percentual**. Para uma fração `s`, o percentual é `100 × s`. O HHI anterior soma os quadrados dos shares percentuais com prêmios elegíveis positivos. O mercado da carteira preserva os saldos assinados. A variação é `2 × (100 × sA) × (100 × sB)`, em pontos de HHI. O HHI posterior soma a variação ao HHI anterior quando ambos são definidos. O indicador mede a concentração na carteira comparável.
- A variação do HHI no cartão exige prêmio positivo para A e B. Na tabela, um prêmio individual em branco ou zero pode produzir variação zero para uma operação válida, conforme a comparação DAX. Um prêmio individual negativo mantém a variação em branco. Os valores monetários continuam assinados.

## Filtros cruzados e diferenças observadas

- **Acre.** Ao selecionar AC no Desktop e no navegador, os cartões passam para 7ª → 6ª, resultante 1ª, share de 20,91% e Δ HHI de +0,244 pts. A tabela de UF preserva suas 27 linhas e o total original. A tabela de ramos recebe o filtro. A linha AC usa a cesta da UF e mantém 24,22% e +0,328 pts. O cartão usa, no denominador, os ramos qualificados sem restringir a UF na composição da cesta, com os prêmios avaliados no recorte selecionado.
- **Automóvel.** Ao selecionar o grupo, os cartões passam para 10ª → 9ª, resultante 2ª, 19,09% e +151,283 pts. O total da tabela de UF muda para R$ 7.679.118.526,26 em prêmios e R$ 40.231.285.324,31 em mercado. O total da tabela de grupos conserva o contexto que precedia o clique.
- **Troca de tabela.** O clique simples substitui a seleção e o clique repetido no mesmo item limpa o filtro. A web mantém uma linha ativa por vez e restaura o contexto quando a linha deixa de existir. Os seletores são controles HTML. Em tela estreita, as tabelas têm rolagem horizontal própria. Essas são adaptações de interação e apresentação.
- **Posição estabilizada.** A mesma consulta a Caixa, Allianz e Mapfre retornou variação de posição `+1, +2, +1` em três execuções no PBIX anterior. Na execução com `+2`, os campos individuais ainda mostraram 12ª e 11ª, pois são avaliações separadas. No PBIX com posição estável, três reexecuções retornaram `+1, +1, +1`. As posições exibidas da Caixa e da resultante, os prêmios combinados, a participação e a variação do HHI coincidiram. A dependência está em `[Impacto Posição M&A]`, que usa `[Posição de Mercado Individual]`. O HHI, a posição posterior, a posição resultante e as tabelas usam suas fórmulas próprias.

## Casos adicionais

| Cenário | Resultado verificado |
|---|---|
| A = B = Allianz | Prêmio B R$ 6.542.993.339,14. Combinado e variação do HHI em branco. A web preservou posição atual 12ª e HHI atual 691,74. |
| B sem produção elegível, código `01848` | Prêmio B em branco, combinado R$ 6.542.993.339,14, Δ HHI em branco no cartão e zero na tabela. |
| B com saldo zero, código `03727` | Prêmio B R$ 0,00, combinado R$ 6.542.993.339,14, Δ HHI em branco no cartão e zero na tabela. |
| B negativo, Taamin `01864` | Prêmio B −R$ 103.118,68, combinado R$ 6.542.890.220,46 e Δ HHI em branco nos dois escopos. |
| Nov/2025–mar/2026 | No navegador, Allianz e Mapfre deram 10,90% combinados, 11ª → 10ª para a Caixa e Δ HHI de +53,485 pts. Raio-X e Visão por UF receberam as mesmas competências. |
| Troca global e ausência da referência | O navegador recebeu Porto Seguro do Início e exibiu 1ª no cenário testado. Sem entidade e sem grupo, exibiu cartões em branco e tabelas sem linhas. |

## Inicialização e regressão

O carregamento pendente vinha do import estático de `dist/ma.js` ausente, que impedia a execução de `dist/app.js` antes da consulta ao catálogo. A folha `dist/ma.css` também faltava. Ambos foram adicionados. A verificação HTTP recebeu 200 para a raiz, o módulo compartilhado, os dois arquivos de M&A, o catálogo e o endpoint de dados. Um teste automatizado cobre juntos esses recursos e a resposta real da página.

- **45 testes automatizados** passaram com `python -B -m unittest discover -s tests -v`, incluindo 12 de M&A e 33 das etapas anteriores. A suíte cobre HHI, valores em branco e assinados, empates, totais, filtros cruzados, trocas de referência e regressões do Raio-X, da evolução cronológica, da Visão por UF e do Simulador.
- `node --check dist/app.js` e `node --check dist/ma.js` passaram. O navegador não registrou erros JavaScript no fluxo validado.
- No navegador, foram verificados a inicialização do Simulador, os cartões de referência de Raio-X e Visão por UF, o retorno ao Simulador e a volta a M&A. Em M&A, foram validados mudança de seguradora B, seleção e limpeza de linha com mouse e teclado, ordenação, referências, datas e estado vazio. Em 390 × 844, a largura da página permaneceu dentro do viewport, com rolagem nas tabelas.
- Os hashes do PBIX original e da cópia estável permaneceram iguais aos registros anteriores. As consultas temporárias do Desktop foram descartadas.

## Arquivos da etapa

| Arquivo | Alteração |
|---|---|
| `ma_views.py` | Contextos de carteira, posições, índices e totais com Python, DuckDB e Decimal. |
| `server.py` | Seleção salva, validação dos parâmetros, cache e endpoint `/api/fusao-aquisicao`. |
| `dist/index.html`, `dist/app.js` | Aba integrada à navegação e aos filtros compartilhados. |
| `dist/ma.js`, `dist/ma.css` | Cartões, tabelas e interações de M&A. |
| `tests/test_ma.py`, `tests/ma_referencia.dax` | Paridade com dados reais, regressão HTTP e consultas de conferência. |
| `README.md`, `PARIDADE_MA.md`, `PARIDADE_SIMULADOR.md` | Execução local, evidências de paridade e referência ao PBIX de posição estável. |
