# Paridade do Simulador — Simulações Estratégicas

## Referências e componentes

A referência visual é a página PBIR `959e4eb429a566a2b0ea`. As medidas foram recuperadas de `Crescimento Concorrentes.tmdl`, `Crescimento Referência.tmdl`, `Meta_Movimento.tmdl`, `Seletor_Entidade.tmdl` e `Eixo_Historico.tmdl`.

| Componentes PBIR | Quantidade | Correspondência na aplicação |
|---|---:|---|
| Seletores de competência, crescimento e meta | 5 | Dois meses, dois controles de crescimento e objetivo competitivo |
| Seletor oculto de seguradora | 1 | Estado compartilhado de entidade e grupo |
| Cartões de participação e posição | 6 | Shares atual e simulado, diferença em p.p., duas posições e variação de posição |
| Cartões de metas | 2 | Margem de segurança e crescimento adicional |
| Cartões de contexto | 2 | Referência em análise e cobertura dos dados |
| Textos | 4 | Cabeçalho, descrições e fonte |
| Gráfico e tabela | 2 | Prêmios atuais e simulados e colocação de cada seguradora |
| **Total** | **22** | |

Os sliders usam valores inteiros de −30 a +100, em passos de um ponto percentual, com `GENERATESERIES(-30, 100, 1)` como origem. A lista de metas mantém a ordem de `Meta_Movimento`: Sem meta, Subir 1–5 posições e Cair 1–5 posições. O estado de referência contém +18% para a seguradora, 0% para os concorrentes e Cair 3 posições.

## Regras preservadas

- A carteira usa ramos cujo prêmio líquido da referência tem valor absoluto superior a R$ 0,01 no período. Os prêmios dos concorrentes são somados nesses ramos, aceitando atuação parcial e preservando saldos assinados. A fonte é o fato estadual, sem adição ao fato nacional. A seleção explícita de seguradoras tem precedência sobre o grupo histórico.
- O share atual divide `Prêmios Referência` pelo mercado da carteira. No cenário simulado, a taxa da referência multiplica seu volume e a taxa dos concorrentes multiplica o complemento `mercado da carteira − prêmio da referência`. Os dois termos reconstituem o mesmo denominador do share atual quando as duas taxas são zero.
- O cartão de posição atual conta os concorrentes estritamente acima. O cartão simulado aplica a taxa de cada seguradora, compara prêmios arredondados a centavos segundo o DAX e conta quem fica estritamente acima. A tabela usa ranking denso sobre valores positivos, sem arredondamento intermediário. Assim, para prêmios de 100, 100 e 80, as posições densas da tabela são 1, 1 e 2, enquanto a posição do cartão para a terceira seguradora é 3.
- O gráfico mostra a união do Top 10 atual com o Top 10 simulado, além da referência quando tem dados na cesta. Cada Top 10 filtra os valores positivos, desempata pelo código da seguradora e o visual é ordenado por prêmio atual decrescente. A tabela é ordenada pela posição atual. Posições em branco e filtros visuais seguem suas condições específicas no DAX.
- A meta relativa é a posição atual menos o movimento escolhido. A referência fica fora da lista de corte. A meta de avanço usa a posição-alvo e acrescenta um centavo ao prêmio de corte. A meta de recuo usa a posição logo acima da posição-alvo e subtrai um centavo do corte, com piso zero. A meta inválida fica em branco.

## Correções e decisões de paridade

### Impacto Simulado MS p.p.

O DAX original define as variáveis de share, mas o resultado usa um marcador de código com o literal `0`. O cartão exibia 0,00 p.p. mesmo com participações diferentes. A correção usa os dois shares como frações e multiplica a diferença por 100. Se um share está em branco, o impacto também fica em branco. O arredondamento ocorre apenas na exibição.

```dax
Impacto Simulado MS p.p. =
VAR MSAtual = [Market Share da Referência]
VAR MSSimulado = [Market Share Simulado %]
RETURN
    IF(
        ISBLANK(MSAtual) || ISBLANK(MSSimulado),
        BLANK(),
        (MSSimulado - MSAtual) * 100
    )
```

A mudança se limita à medida de impacto. Com o mesmo universo e o mesmo percentual de crescimento para ambos os lados, o share se mantém quando os denominadores são válidos.

### Cartões de metas

O PBIR declara quatro interações `NoFilter`, uma de cada slider para cada cartão de meta. Os sliders são `ee4d9c9f269700320d10` e `93d669eebd9733b7a5d5`. Os cartões são `c6b2bb80bb23c93d15d0` e `48905170bdb7058806e6`. Nesses cartões, a ausência dos filtros faz as taxas efetivas assumirem 0% pelo `SELECTEDVALUE` do modelo. As demais seleções continuam afetando os cartões.

A página web informa junto aos cartões de meta que eles usam o cenário atual, com crescimento de 0% para a referência e para os concorrentes. No cenário salvo, o corte de recuo é **R$ 1.369.570.174,24** e a margem é **R$ 834.682.969,01**. Esse é o comportamento mantido na homologação.

## Cenário principal

**Caixa Seguradora (`05631`), jan–set/2026, taxas +18% e 0%, objetivo Cair 3 posições.** Valores reproduzidos por consulta independente aos Parquets com aritmética decimal, usando as fórmulas recuperadas.

| Medida | Valor de referência | Exibição esperada |
|---|---:|---:|
| Prêmio da referência | R$ 2.204.253.143,25 | — |
| Mercado da carteira | R$ 84.243.304.989,16 | — |
| Prêmio simulado da referência | R$ 2.601.018.709,0350 | — |
| Prêmio simulado dos concorrentes | R$ 82.039.051.845,91 | — |
| Participação atual | 2,6165321310% | 2,62% |
| Participação simulada | 3,0730346655% | 3,07% |
| Impacto corrigido | +0,4565025345 p.p. | +0,46 p.p. |
| Posição atual e simulada | 12 e 10 | 12ª e 10ª |
| Variação de posição | 2 | avanço de 2 posições |
| Margem de segurança | R$ 834.682.969,01 | R$ 834,68 Mi |
| Crescimento adicional | Em branco | — |

A carteira tem 18 ramos. Antes dos filtros específicos de visual e posição, há 111 seguradoras com saldo positivo, cinco com zero e três com saldo negativo.

## Casos de referência adicionais

Os resultados da tabela foram calculados de forma independente com os Parquets, aplicando as taxas sobre as quantias completas. Esta tabela distingue as referências numéricas dos testes executados no navegador ou no Desktop.

| Cenário | Share simulado | Impacto em p.p. | Posição atual → simulada | Meta |
|---|---:|---:|---|---|
| Caixa, jan–set/2026, 0% / 0% | 2,6165321310% | 0 | 12 → 12 | Margem R$ 834.682.969,01 |
| Caixa, −30% / 0% | 1,8460633439% | −0,7704687871 | 12 → 13 | Mesma margem |
| Caixa, +100% / 0% | 5,0996307840% | +2,4830986530 | 12 → 7 | Mesma margem |
| Caixa, +18% / +20% | 2,5740457744% | −0,0424863566 | 12 → 12 | Mesma margem |
| Caixa, +18% / −20% | 3,8120072557% | +1,1954751247 | 12 → 9 | Mesma margem |
| Caixa, +18% / 0%, Subir 3 posições | 3,0730346655% | +0,4565025345 | 12 → 10 | Crescimento adicional 46,9792545054% |
| Caixa, +18% / 0%, Sem meta | 3,0730346655% | +0,4565025345 | 12 → 10 | Ambos os cartões em branco |
| Caixa, nov/2025–mar/2026, +18% / 0% | 3,2785622938% | +0,4861542902 | 11 → 10 | Margem R$ 538.689.974,65 |
| Porto Seguro (`05886`), jan–set/2026, +18% / 0% | 14,3286237040% | +1,9143814025 | 1 → 1 | Margem R$ 8.801.993.838,46 |
| Taamin (`01864`), mar/2026, 0% / 0% | −0,6211535594% | 0 | em branco → em branco | Sem posição por prêmio líquido negativo |

Para testar ausência de produção, selecionar somente o grupo Caixa Econômica em set/2026 preserva a lacuna do grupo histórico no fato UF. Para testar empate, compare a contagem estrita e o ranking denso. A regra de centavos da posição simulada pode agrupar quantias que a classificação densa por valor completo distingue.

## Validação no Power BI Desktop

A correção foi aplicada à medida `Impacto Simulado MS p.p.` na cópia de trabalho baseada no PBIX cronológico. A edição foi confirmada no modelo, salva em `SUSEP - Market Share Simulador.pbix` e reaberta no Desktop. O PBIX original manteve o SHA-256 `CFCAB66A04CCAD06807602B55B044CDC74D375B812864E78C380EC69A415ADDC`. O backup anterior à edição foi preservado separadamente. A cópia entregue mantém as vinculações do visual cronológico do Raio-X ao eixo `Eixo_MS_Ano_Mes[Rotulo]` e à medida `Evolução Competitiva Cronológica %`.

| Cenário observado no relatório | Share atual → simulado | Impacto em p.p. | Posição atual → simulada | Margem |
|---|---:|---:|---:|---:|
| Caixa, jan–set/2026, +18% / 0%, Cair 3 | 2,62% → 3,07% | +0,46 | 12 → 10 | R$ 834,68 Mi |
| Caixa, nov/2025–mar/2026, +18% / 0%, Cair 3 | 2,79% → 3,28% | +0,49 | 11 → 10 | R$ 538,69 Mi |

No navegador, o gráfico destaca a seleção de uma seguradora e restringe a tabela à linha correspondente. Selecionar a mesma seguradora pela tabela recalcula os cartões afetados e mantém as séries completas no gráfico. Clicar novamente limpa o filtro. A web aplica uma seguradora por vez nesses filtros cruzados. A seleção de referência feita no Início é compartilhada pelas páginas de análise.

## Homologação da posição e da margem

### Contextos comparados

O Analisador de Desempenho do Power BI Desktop registrou duas consultas independentes, dos visuais `83a113bb473c9a887cd6` (posição) e `c6b2bb80bb23c93d15d0` (margem). A página `959e4eb429a566a2b0ea` e os cartões não têm filtros próprios salvos. O relatório, a página e os 22 visuais do Simulador têm as mesmas definições no PBIX original e no PBIX do Simulador.

| Contexto | Consulta avulsa original | Posição no relatório | Margem no relatório |
|---|---|---|---|
| Entidade | `Seletor_Entidade[coenti] = "05631"` | `Seletor_Entidade[Seguradora] = "CAIXA SEGURADORA S/A"` | Mesmo seletor oculto sincronizado |
| Grupo | `Seletor_Grupo[cogrupo] = "00230"` | Sem filtro de grupo | Sem filtro de grupo |
| Período | `[Data]` em jan e set/2026 | `[Mês/Ano]` com os dois rótulos | Mesmos rótulos |
| Meta | `[Movimento] = -3` | `[Objetivo] = "Cair 3 posições"` | Mesmo objetivo |
| Crescimento | +18% / 0%, removidos dentro da expressão da margem | +18% / 0% | Filtros ausentes por `NoFilter` |
| Avaliação | `CALCULATETABLE(ROW(...))` combinado | `SUMMARIZECOLUMNS` do visual | `SUMMARIZECOLUMNS` separado |

Os seletores de entidade, grupo, meses, crescimento e meta não têm relações que propaguem filtros ao fato UF. Os meses têm relações com tabelas locais de data. O DAX resolve os meses com `SELECTEDVALUE` e aplica o intervalo a `dim_calendario[data_mes]`. A entidade explícita tem precedência sobre o grupo em `[Prêmios Referência]`. O seletor de grupo do Início não é sincronizado com a página, e o filtro `[Entidade Pertence ao Grupo] = 1` pertence ao visual do seletor de entidade. A consulta capturada dos cartões não traz esse filtro. O fato UF se relaciona com as dimensões de seguradora, ramo, calendário, UF e grupo de ramos. Sem uma seleção no gráfico ou na tabela, a consulta capturada não aplica filtros cruzados de seguradora.

### Causa demonstrada no mecanismo DAX

A mesma consulta capturada do cartão de posição retornou **13 e 12** em reexecuções no mesmo PBIX, com os filtros idênticos. A consulta combinada original também apresentou variação. Esse controle isola o problema dos filtros de grupo, dos campos usados pelos seletores e da remoção dos sliders.

Em `Seletor_Entidade.tmdl`, `[Posição de Mercado Individual]` inclui a referência em `ADDCOLUMNS(ALL(dim_seguradora[coenti]), ...)`. O prêmio dessa linha é uma soma por transição de contexto. O prêmio da referência é outra soma, calculada por `REMOVEFILTERS` e `TREATAS` com a mesma carteira. O campo `fato_premios_uf[premio_direto]` é `double`. A medida aplica `[@Premio] > PremioEntidade` sobre os resultados brutos, sem excluir a referência. As duas somas exibem R$ 2.204.253.143,25 a centavos.

Instrumentei essa comparação no contexto capturado do cartão. Em uma execução, o diagnóstico retornou **13 com a referência e 12 sem ela**, identificou **05631**, a própria Caixa, e mediu um excesso de cerca de **0,48 microrreal** na parcela iterada. Em outra execução da mesma consulta, a comparação não incluiu a Caixa e retornou **12 em ambas as contagens**. A consulta instrumentada e o cálculo original podem agregar separadamente. [Consulta de diagnóstico](./tests/simulador_diagnostico_caixa_2026.dax)

O DuckDB confirma **11 concorrentes com prêmio estritamente superior** na carteira comparável, com e sem `00230`. A posição atual mantém a comparação estrita, em que um empate não acrescenta uma posição. A medida de posição simulada compara a centavos. A tabela usa `RANKX DENSE` sobre prêmios positivos. O cálculo de corte usa concorrentes com prêmio positivo, exclui a referência, ordena por prêmio decrescente e desempata por código.

| Posição de partida | Posição-alvo | Corte entre concorrentes | Prêmio de corte | Limite após deduzir R$ 0,01 | Margem calculada |
|---:|---:|---|---:|---:|---:|
| 12 | 15 | 14º · Zurich Santander (`06564`) | R$ 1.369.570.174,25 | R$ 1.369.570.174,24 | **R$ 834.682.969,01** |
| 13 | 16 | 15º · Mongeral Aegon (`02101`) | R$ 1.265.839.314,61 | R$ 1.265.839.314,60 | **R$ 938.413.828,65** |

A diferença de R$ 103.730.859,64 vem integralmente do deslocamento do corte da meta. O rank simulado permaneceu em 10 nas consultas comparadas.

### Referência de regressão

A nova consulta de validação replica os contextos capturados, separa posição e margem e define medidas locais para excluir a autocontagem da posição e propagar esse resultado até a margem. Preserva a comparação estrita entre concorrentes, a cesta, o critério de corte e o arredondamento original do limite. O código de produção da web já realiza a comparação com valores decimais e produz os resultados esperados. A correção do Market Share cronológico e os PBIX entregues foram preservados. [Consulta DAX de validação](./tests/simulador_validacao_caixa_2026.dax)

Executada no Power BI Desktop, a consulta revisada mostrou posição atual **12**, posição simulada **10**, shares **2,6165321310%** e **3,0730346655%** e impacto de **+0,4565025345 p.p.**. No resultado separado de meta, a posição-alvo foi **15**, o limite foi **R$ 1.369.570.174,24** e a margem foi **R$ 834.682.969,01**. A consulta de diagnóstico documenta a instabilidade da cópia anterior à correção definitiva.

O teste de cenário compara os 11 concorrentes acima da Caixa, o código e o prêmio de corte, a posição 12 e a margem ao centavo. Um teste sintético cobre o uso do prêmio comparável para a posição, empate e exclusão da própria referência no corte. A suíte também verifica que alterar os sliders modifica a simulação e preserva os dois cartões de meta. [Testes do Simulador](./tests/test_simulation.py)

## Correção definitiva no PBIX

A medida `Seletor_Entidade[Posição de Mercado Individual]` foi atualizada no modelo pelo Power BI Desktop e salva em `SUSEP - Market Share Simulador - Posicao Estavel.pbix`. O arquivo foi fechado, reaberto e validado em uma nova sessão do Desktop. ZIP íntegro e SHA-256 `1AAB22E455FB33288FC49FD1626F75B52AF8BBA37B49F2ACD3A5DB7F75827021`.

O backup anterior à mudança é idêntico à cópia anterior do Simulador, com SHA-256 `A8115CF3D3264F97841C2B1C344A623AA98CE4A01C25FA3650ECA050AAB865EB`. O PBIX original e o PBIX cronológico mantiveram seus hashes.

### Comparação monetária e empates

Os dois Parquets UF conferidos, o de origem do modelo e o usado pela web, têm `premio_direto` como `DECIMAL(38,2)`. Nos 4.003.131 registros de cada arquivo, a verificação encontrou zero valores com frações de centavo. O modelo importa o campo como `double`. Por isso o DAX passa a normalizar **os totais agregados** da referência e dos concorrentes a duas casas para a comparação de posição. A verificação de prêmio positivo da referência usa a mesma precisão. A seleção única, a cesta de ramos, o universo de concorrentes e a verificação de produção positiva seguem os critérios originais.

```dax
VAR PremioEntidadeCentavos = ROUND(PremioEntidade, 2)
RETURN
    IF(
        ISBLANK(Entidade)
            || COUNTROWS(VALUES(Seletor_Entidade[coenti])) <> 1
            || PremioEntidadeCentavos <= 0,
        BLANK(),
        1 + COUNTROWS(
            FILTER(
                Ranking,
                dim_seguradora[coenti] <> Entidade
                    && ROUND([@Premio], 2) > PremioEntidadeCentavos
            )
        )
    )
```

A regra de empate continua sendo **1 + a quantidade estritamente acima**. Valores iguais em centavos dividem a posição mesmo se os resultados binários diferirem por resíduos de soma. A posição simulada mantém sua comparação a centavos. A classificação densa da tabela e o desempate por código no corte da meta mantêm as expressões próprias.

### Resultados na cópia reaberta

A aba **Consulta 2** contém a validação com as medidas persistidas, sem `DEFINE MEASURE`. As **quatro execuções consecutivas** no PBIX reaberto deram posição atual **12**, posição simulada **10**, avanço **2**, impacto de **+0,4565025345 p.p.**, posição-alvo **15**, limite de **R$ 1.369.570.174,24** e margem de **R$ 834.682.969,01**. O relatório mostrou o impacto como **0,46 p.p.** e a margem como **R$ 834,68 Mi**. A meta de avanço **Subir 3 posições** apresentou **46,98%** de crescimento adicional. Os cartões de meta continuam com as interações `NoFilter` dos dois sliders.

| Cenário de controle | Prêmio de referência | Posição, posição-alvo e margem |
|---|---:|---|
| Sem seleção de referência | Em branco | Em branco |
| Caixa e Porto Seguro selecionadas | R$ 20.299.882.981,51 | Em branco |
| Taamin em mar/2026 | −R$ 24.335.500,92 | Em branco |
| Grupo Caixa Econômica em set/2026, sem produção no fato | Em branco | Em branco |

- **Raio-X.** Os consumidores da medida compartilhada exibiram 12ª posição, 111 seguradoras e distância para a 11ª de R$ 61.653.812,34. A **Consulta 1** cronológica permaneceu idêntica e retornou zero diferenças para Market Share, Sinistralidade e Margem parcial em jan–set/2026. Para nov/2025–mar/2026, retornou dez pontos, cinco competências em cada uma das duas séries.
- **Visão por UF.** A página reaberta mostrou 27 de 27 UFs com atuação, 0 no Top 3, maior participação de 8,67% no Piauí e liderança em branco.
- **Demais páginas.** A análise de dependências identificou que um cartão já existente de Fusão e Aquisição usa a posição base e o impacto derivado dela. Ele recebe a correção compartilhada. A auditoria desse efeito se limitou à dependência da medida. As definições dos visuais, as interações e os filtros salvos permaneceram idênticos ao PBIX anterior. Nos metadados do relatório, o único campo que mudou foi a página ativa, gravada como Início.
- **Aplicação web.** Os 33 testes passaram na reexecução, incluindo posição, corte, margem, empates e cronologia. A lógica web permaneceu com a aritmética decimal já homologada.

## Testes executados

- `python -B -m unittest discover -s tests -q` passou nos **33 testes**, incluindo nove do Simulador e as suítes existentes do Raio-X e da Visão por UF. A suíte do Simulador inclui dados reais, saldos assinados, empates, metas, troca de período e referência, ausência de produção e filtros cruzados. O teste HTTP da Visão por UF recebeu 200 no endpoint e no arquivo do mapa.
- `node --check dist/app.js` e `node --check dist/simulation.js` passaram. O teste de integridade do arquivo PBIX por `python -B -m zipfile -t` também passou.
- No navegador, o cenário principal exibiu oito cartões calculados, 11 seguradoras no gráfico e 111 linhas na tabela. Em 0% / 0%, o impacto foi 0,00 p.p. Em −30% / 0%, foi −0,77 p.p. Em +100% / 0%, foi +2,48 p.p. Em +18% / +20%, foi −0,04 p.p. Em +18% / −20%, foi +1,20 p.p.
- **Subir 3 posições** exibiu 46,98% de crescimento adicional. **Cair 3 posições** exibiu R$ 834,68 Mi de margem. **Sem meta** deixou os dois cartões em branco. Clicar na barra da Porto reduziu a tabela a uma linha, com posições 2 e 2 nos cartões e margem de R$ 0,00. Clicar na Porto por meio da tabela deixou as 111 linhas visíveis e afetou os mesmos cartões. Limpar a seleção restaurou o cenário de referência.
- O período nov/2025–mar/2026 exibiu +0,49 p.p. e foi preservado ao navegar para o Raio-X e a Visão por UF. A troca da Caixa para Porto Seguro pelo Início foi refletida nas três páginas. No Simulador, a Porto exibiu 14,33% de share simulado em jan–set/2026. Um período invertido exibiu erro de validação. Selecionar somente o grupo Caixa Econômica em set/2026 deixou os indicadores sem dados.
- No teste com viewport de 390 × 844, os oito cartões, o gráfico e a tabela estavam disponíveis e a página ficou dentro da largura do viewport.
- Na homologação, o navegador exibiu o texto sobre a base de 0% junto aos cartões. Ao passar o crescimento da referência de +18% para +100%, o impacto mudou de +0,46 p.p. para +2,48 p.p. e a margem continuou em R$ 834.682.969,01. O console do navegador ficou sem erros.

## Arquivos da entrega

| Arquivos | Alteração |
|---|---|
| `simulation.py` | Cálculos de cenário, posições, metas, gráfico e tabela usando os agregados UF. |
| `server.py` | Endpoint `/api/simulacoes` e validação de taxas, meta e seleção competitiva. |
| `dist/index.html`, `dist/app.js` | Página e integração dos filtros, navegação, carregamento e resultados. |
| `dist/simulation.js`, `dist/simulation.css` | Controles, cartões, gráfico, tabela e estilos responsivos. |
| `tests/test_simulation.py` | Nove testes específicos do Simulador, incluindo as regressões de posição e margem da homologação. |
| `tests/simulador_diagnostico_caixa_2026.dax`, `tests/simulador_validacao_caixa_2026.dax` | Captura dos contextos de posição e meta, diagnóstico de autocontagem e consulta de referência sem autocontagem. |
| `README.md`, `PARIDADE_SIMULADOR.md` | Execução local, validação e diferenças de paridade. |
| `SUSEP - Market Share Simulador - Posicao Estavel.pbix` | Cópia de trabalho preservada separadamente. Inclui a evolução cronológica, o impacto em p.p. e a posição estabilizada. Referência usada em Fusão e Aquisição. |
| Versão anterior e backups do PBIX | Referências locais preservadas separadamente. |
