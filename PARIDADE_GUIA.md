# Paridade do Guia de Indicadores

## Referências verificadas no Power BI

- Página PBIR `7aaac082eac32520176c`. A definição da página, os oito visuais e a definição do relatório são idênticos no PBIX original e na cópia `SUSEP - Market Share Simulador - Posicao Estavel.pbix`. Os dois arquivos preservaram o SHA-256 anterior à implementação.
- `Guia_Indicadores.tmdl` contém 16 registros. `Guia_Conteudo.tmdl` reúne esses 16 com 22 registros adicionais e é a tabela consultada pelos seletores. A extração conferiu 38 indicadores e seis categorias. Foram preservados os 35 registros com status `Implementado` e os três com status `Planejado`. O PBIR não vincula esse campo a nenhum visual.
- Os textos e as fórmulas são literais no TMDL. Os quatro cartões avaliam `SELECTEDVALUE` sobre a respectiva coluna de `Guia_Conteudo`, com a alternativa literal `Selecione um indicador ou conceito.`. O Guia é independente da entidade e do período das páginas analíticas.

| Componente no PBIR | Vínculo e reprodução na web |
|---|---|
| Título | **SUSEP \| Guia de Indicadores**, com destaque dourado |
| Orientação | Definições, fórmulas, fontes e critérios utilizados nas análises de mercado e desempenho técnico. |
| Categoria | `Guia_Conteudo[Categoria]`, seleção única e ordem alfabética |
| Indicador | `Guia_Conteudo[Indicador]`, seleção única, ordem alfabética e opções filtradas pela categoria |
| Significado | `[Guia Definição]` sobre `[Definicao]` |
| Fórmula | `[Guia Fórmula]` sobre `[Calculo]` |
| Interpretação | `[Guia Interpretação]` sobre `[Interpretacao]` |
| Origem dos dados | `[Guia Fonte]` sobre `[Fonte]` |

| Categoria recuperada | Indicadores |
|---|---:|
| Atributos e Filtros | 5 |
| Competitividade Regional | 8 |
| Concentração de Mercado | 2 |
| Desempenho Técnico | 7 |
| Metodologia | 6 |
| Participação e Ranking | 10 |

## Comparação e testes

| Cenário | Evidência e resultado |
|---|---|
| Conteúdo integral | A extração repetida a partir dos dois TMDL e do PBIR da cópia estável coincidiu com os 38 registros de `guide-data.json`. SHA-256 do arquivo `ca5ff10e77e679a69f96248e316b6d589b11fa5d2738675e3c602d140512adfe`. |
| Abertura com a seleção salva | **Desempenho Técnico / Margem Técnica Parcial** no Desktop e no navegador, com os quatro textos recuperados, incluindo a fórmula `(Prêmios ganhos - Sinistros ocorridos - Despesas comerciais) / Prêmios ganhos x 100` e a origem `fato_premios_nacional`. |
| Mudança para Concentração de Mercado | Desktop e navegador mantiveram **Margem Técnica Parcial** como seleção anterior. Os quatro cartões exibiram `Selecione um indicador ou conceito.`. O seletor de indicador ofereceu **CR4 - Concentração das 4 Maiores** e **Índice Herfindahl-Hirschman (HHI)**. |
| Seleção de HHI | Os quatro cartões do navegador exibiram os textos recuperados e conferidos no Desktop. A fórmula foi `HHI = soma dos quadrados dos Market Shares expressos de 0 a 100.`. A origem foi `Prêmios SUSEP e mercado comparável`. |
| Sem indicador em Concentração de Mercado | No navegador, três cartões exibiram o texto alternativo. A origem continuou `Prêmios SUSEP e mercado comparável`, valor comum a HHI e CR4. O resultado foi conferido contra a lógica de valores distintos de cada medida no TMDL. |
| Tela móvel de 390 × 844 | Os seletores permitiram escolher **Competitividade Regional / Market Share por UF**. Os quatro cartões de 366 px foram empilhados, com a origem `fato_premios_uf` e largura total de 390 px. |
| Navegação e regressão no navegador | O Início abriu com o grupo salvo. No período jan–set/2026, a Caixa retornou 2,62% e 12º no Raio-X e 27 de 27 UFs, com 8,67% em PI, na Visão por UF. O Simulador exibiu 3,07%, +0,46 p.p. e R$ 834,68 Mi. M&A exibiu 11,76% para Allianz e Mapfre. Ao retornar ao Guia, o indicador escolhido permanecia selecionado. O console terminou sem erros. |
| Testes automatizados | 47 testes Python passaram, incluindo 45 das etapas anteriores e dois de integridade e extração do Guia. Três testes JavaScript passaram cobrindo a seleção inicial, a seleção incompatível e valores distintos por cartão. |

Os seletores nativos usam **Todas** e **Todos** para remover o respectivo filtro. A validação desse estado na web usou as medidas TMDL como referência. A página web adapta o canvas fixo de 1920 × 1080 com controles ao lado dos cartões em telas largas e uma coluna em telas estreitas. Nenhuma divergência textual foi identificada.

## Esclarecimentos metodológicos

- **Carteira comparável.** O Guia original descreve a cesta como ramos com “produção positiva”. As medidas comparam no contexto de cada página. O Raio-X e M&A qualificam ramos pelo valor absoluto do prêmio líquido superior a R$ 0,01. Na Visão por UF, a cesta usa o prêmio líquido positivo acima de R$ 0,01 no agregado das UFs e se aplica a cada estado. A descrição recuperada permanece visível tal como no modelo. [Raio-X](./PARIDADE_POWER_BI.md) · [Visão por UF](./PARIDADE_VISAO_UF.md) · [M&A](./PARIDADE_MA.md)
- **HHI.** A escala 0–100 da fórmula do Guia é a escala percentual dos shares. Em M&A, se `sA` e `sB` são frações, a variação é `2 × (100 × sA) × (100 × sB)`. Saldos assinados, ramos elegíveis e estados em branco seguem as regras documentadas de cada visual. A descrição do Guia mantém a referência conceitual a 10.000. O registro de HHI está marcado como `Planejado` na tabela, campo que os visuais do Guia não exibem. A página de M&A implementa o cálculo conforme as medidas homologadas. [Paridade de M&A](./PARIDADE_MA.md)
- **Filtros cruzados.** No PBIR, Categoria filtra as opções de Indicador e ambos filtram os cartões. Indicador → Categoria está configurado como `NoFilter`. As seleções do Guia são locais à página. Os filtros cruzados dos painéis analíticos seguem as interações de cada painel.

## Execução local

Abra um PowerShell no diretório da aplicação, execute `python -B server.py` e abra a aba **Guia de Indicadores**. [Guia local](http://127.0.0.1:8000/#guia)

```powershell
python -B -m unittest discover -s tests -v
node --test tests/test_guide.mjs
```

Para regenerar o conteúdo, defina `$pastaTmdl` com o diretório `definition/tables` do modelo auditado e `$copiaPbix` com a cópia de posição estável do PBIX. Esses insumos são preservados separadamente. O script escreve `dist/guide-data.json`.

```powershell
python -B tools/build_guide.py $pastaTmdl $copiaPbix
```

## Arquivos criados ou alterados

| Arquivo | Alteração |
|---|---|
| `dist/index.html` | Título, orientação, seletores e cartões da aba existente |
| `dist/app.js` | Rota, carregamento sob demanda e tratamento de falhas do Guia |
| `dist/guide.js` | Filtros, atualização dos cartões e regra de valores distintos |
| `dist/guide.css` | Estilos e disposição responsiva do Guia |
| `dist/guide-data.json` | Conteúdo extraído dos TMDL e seleções salvas no PBIR |
| `tools/build_guide.py` | Extração reproduzível do modelo e do relatório |
| `tests/test_guide_data.py` | Testes da extração e da integridade dos textos |
| `tests/test_guide.mjs` | Testes do comportamento dos cartões |
| `README.md`, `PARIDADE_GUIA.md` | Instruções locais e registro de comparação |
