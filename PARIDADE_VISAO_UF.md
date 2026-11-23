# Paridade com o Power BI — Visão por UF

## Referência e cenário principal

Os visuais vieram da página PBIR `fc657e50ee32b5dc9e0d`. As medidas de participação, posição, indicadores e comparação anual vieram de `Crescimento Concorrentes.tmdl` e `Campos_Carteira.tmdl`. A homologação original usava a geometria do recurso `brazil.states.topo.json`. Os resultados abaixo foram conferidos no Power BI Desktop e na aplicação com os Parquets vigentes. A troca para a malha pública do IBGE foi validada separadamente. [Consultas DAX de referência](./tests/visao_uf.dax) · [Paridade da nova geometria](./PARIDADE_MAPA_PUBLICO.md)

| Caixa Seguradora · jan–set/2026 | DAX de referência | Web |
|---|---:|---|
| Atuação | 27 | 27 de 27 UFs |
| Liderança | `BLANK` | — |
| Top 3 | 0 | 0 UFs |
| Maior participação | 8,6745890222% · PI | 8,67% em PI |
| Piauí · prêmio da referência na cesta | R$ 18.837.475,83 | R$ 18.837.475,83 |
| Piauí · participação no ano anterior | 8,9020678069% | 8,90% no detalhe anual |
| Piauí · variação | −0,2274787847 p.p. | −0,23 p.p. no detalhe anual |
| Piauí · posição no agrupamento `Estado Mapa` | `BLANK` | — no tooltip |
| Piauí · posição no agrupamento `dim_uf[uf]` | 5 | 5 no cálculo de referência por código de UF |

O DAX confirmou que a posição é 5 quando `uf` está em escopo e fica em branco no agrupamento `Estado Mapa` usado pelo cloropleto. O traço no tooltip representa o resultado em branco, enquanto a cor trata o branco como zero conforme a configuração do visual.

## Testes adicionais

- **Brasilprev, out/2025–set/2026.** O DAX retornou atuação em 27 estados, liderança em 24, Top 3 em 27 e maior share em RR, 75,4419807045%. No Maranhão, o prêmio foi R$ 848.160.081,08, o share anterior foi 46,9528486957% e a variação foi +2,8742960906 p.p. O teste sobre o Parquet usa o mesmo intervalo e cesta de seis ramos, com aproximadamente 49,8271447864% de share atual.
- **Fator, mar/2026.** No Amapá, a comparação usa uma participação anterior negativa. No Acre, a participação anterior zero permanece válida. No Rio Grande do Norte, o prêmio atual negativo aparece como quantia e a participação atual permanece em branco. São testes de regressão em DuckDB sobre as regras do DAX.
- **Brasilprev, jan/2019.** O teste mantém a comparação anual em branco quando não há dados de janeiro de 2018. A suíte cobre também intervalos em que as janelas atual e anterior se sobrepõem.
- **Grupo, multisseleção e ausência de dados.** Em setembro de 2026, selecionar apenas Caixa Econômica deixa o ranking sem produção em função da lacuna de grupo histórico no fato UF. O navegador confirmou o estado. A página preserva os retornos das medidas que exigem uma única seguradora. Foram testados ainda ausência de referência e período invertido.

## Mapa e interações

| Gesto conferido no Desktop e no navegador | Resultado |
|---|---|
| Selecionar Piauí no mapa | Mantém o ranking Brasil na ordem original e sobrepõe os prêmios da UF nas barras nacionais. A variação do PI é destacada. Os cartões permanecem nacionais. |
| Selecionar Distrito Federal em Ganhos e Perdas | Mantém o título do ranking, sobrepõe os valores de DF e destaca o distrito no mapa, deixando as demais áreas cinza. |
| Selecionar Porto Seguro no ranking | Destaca a barra da seguradora. Os valores do mapa, da variação e dos cartões permanecem no contexto da referência. |
| Alternar entre Visão por UF e Raio-X | O mês alterado na Visão por UF foi preservado no Raio-X. Grupo e referência vieram do Início. |
| Largura de 390 px | Os painéis foram reorganizados em uma coluna, sem rolagem horizontal do documento. |

O navegador confirmou o tooltip do mapa pelo teclado, com 8,67%, R$ 18.837.475,83 e posição em branco para o Piauí. O detalhe das barras anual e de prêmios foi conferido com os valores atual, anterior e estadual sobreposto.

## Regras e diferenças de apresentação

- A cesta é formada com prêmio líquido da referência superior a R$ 0,01 no agregado das UFs. Ambas as janelas aplicam essa mesma cesta. As medidas usam exclusivamente o fato UF. A elegibilidade mais estrita do Notebook 04 e o preenchimento de vínculos históricos ausentes ficaram fora do cálculo.
- Prêmios e somas no DuckDB usam decimal. O Power BI opera em ponto flutuante e pode apresentar diferenças residuais perto de zero ou de um empate no centavo. Os cartões e os cenários acima coincidiram na precisão exibida ou informada.
- Na homologação original, a aplicação usava a geometria do PBIR com projeção Albers centrada no Brasil e um renderizador SVG. O encaixe e os contornos variavam em pixels em relação ao visual Shape Map. As zonas litigiosas daquele recurso não tinham códigos UF nem efeito nos cálculos. [Paridade da nova geometria](./PARIDADE_MAPA_PUBLICO.md)
- A interação web mantém uma seleção de visual por vez. O tooltip anual expõe as duas participações que compõem a variação, usando as medidas recuperadas. Não há série mensal adicional nesta aba, cuja evolução original é o gráfico de variação em relação ao mesmo período do ano anterior.

## Arquivos desta etapa

| Tipo | Arquivos |
|---|---|
| Criados | `uf_views.py`, `dist/uf.js`, `dist/uf.css`, `dist/uf-map.json`, `tools/build_uf_map.py`, `tests/test_uf.py`, `tests/visao_uf.dax` e este relatório. |
| Atualizados | `server.py`, `dist/index.html`, `dist/app.js` e `README.md`. |
| Integração com Raio-X | Sincronização dos seletores de período e reaproveitamento da validação de parâmetros e da conexão local. Os módulos de cálculo do Raio-X foram preservados. |

As instruções de execução e testes estão no [README](./README.md). O PBIX, os notebooks e os Parquets originais foram preservados. A entrega é local.
