# Paridade com o Power BI — Etapa 1

## Cenário obrigatório

A consulta `tests/caixa_2026.dax` foi executada no modo Consulta DAX do Power BI Desktop sobre a cópia local de `Susep - Market Share.pbix`. O contexto fixa Caixa Seguradora (`05631`), grupo Caixa Econômica (`00230`) e o intervalo inclusivo jan–set/2026. O teste automatizado compara valores monetários no centavo, contagens inteiras e a precisão registrada pelo DAX de ponto flutuante.

| Medida | Referência DAX | Aplicação na precisão do Power BI |
|---|---:|---:|
| Participação da referência | 0,0261653213099 como fração | 2,62% |
| Prêmios da referência | R$ 2.204.253.143,25 | R$ 2,20 Bi |
| Mercado da carteira | R$ 84.243.304.989,16 | Usado no denominador |
| Posição da referência | 12 | 12º |
| Seguradoras com prêmio positivo | 111 | entre 111 seguradoras |
| Distância até a próxima posição | R$ 61.653.812,34 | R$ 61,65 Mi |
| Distância até a liderança | R$ 11.814.810.669,58 | R$ 11,81 Bi |
| Variação da participação | −0,013738334 p.p. | −0,01 p.p. |

A contagem de 111 segue a medida vinculada ao cartão e inclui a própria referência. Os dois valores monetários de distância coincidiram em centavos. O navegador exibiu os seis indicadores solicitados com os mesmos valores arredondados.

## Gráficos, diagnóstico e interações

- A consulta `tests/ranking_caixa_2026.dax` retornou seis registros na opção **Margem parcial**, ordenados por margem. O navegador mostrou Caixa, Bradesco Auto/RE, Porto Seguro, Tokio Marine, Allianz e Bradesco Vida e Previdência. A composição das barras vem da posição por prêmio na cesta. A ordem das barras vem da métrica ativa. A versão web acomoda as seis barras. Na captura do canvas do Desktop, cinco estavam visíveis.
- O diagnóstico de margem da Caixa exibiu **53,36%** para a referência, **25,84%** para o mercado e **27,51 p.p.** de diferença. A linha técnica do cenário de referência tem nove meses de 2026. A série técnica anterior permanece vazia na janela comparativa, por efeito dos filtros do DAX. Na opção Market Share, as duas séries têm pontos.
- Clicar **Habitacional** no diagnóstico recalculou os cartões e a evolução e manteve visível a tabela de origem. A seleção retornou **24,37%**, **2ª entre 23 seguradoras** e ambas as distâncias de **R$ 148,58 Mi**, como no Desktop. O ranking exibe a parcela destacada correspondente ao grupo.
- Clicar **Porto Seguro** no ranking reduziu a posição contextual da Caixa para **2ª** e preservou o total de prêmios e o share. O diagnóstico recalculou os ramos visíveis para o filtro. A margem de mercado resultante foi **24,59%**.
- A seleção de um ponto mensal serve para consultar seu valor. No Desktop, o clique testado em fevereiro preservou os demais visuais.

## Casos adicionais automatizados

| Caso | Resultado verificado na aplicação |
|---|---|
| Brasilprev, jan/2019 | 1ª posição e distâncias em branco. |
| Taamin, mar/2026 | Prêmio líquido de −R$ 24.335.500,92, com produção no diagnóstico e posição em branco. |
| Caixa, ramos 0112 e 0167 | Os estornos de −R$ 15.086,47 e −R$ 972,81 mantêm os ramos na cesta pelo limiar absoluto. |
| Apenas grupo Caixa Econômica, ago/2026 | Prêmio de R$ 2.912.091.664,67, sem posição individual. |
| Apenas grupo Caixa Econômica, set/2026 | Sem referência produtiva no fato UF porque o grupo histórico está vazio. A consulta individual da Caixa mantém dados no mês. |
| Seleção explícita e multisseleção | A seleção de seguradoras tem precedência sobre o grupo. A posição individual e o ranking ficam em branco na multisseleção. |
| Sem entidade nem grupo, período invertido ou janela entre anos | Estados em branco quando aplicável. Em janela entre anos, o volume atual pode existir com evolução e variação anual vazias. |
| Métricas, filtros cruzados e entradas inválidas | Cartões base permanecem iguais ao alternar a métrica. Os filtros cruzados mudam apenas os contextos pertinentes. Códigos e filtros inválidos são rejeitados pela API. |

O navegador também foi verificado com largura de 390 px. Os cartões se reorganizam e a tabela mantém a rolagem horizontal local. A navegação para uma tela reservada mostrou somente seu estado, sem métricas.

## Diferenças e limites

- A web adapta o canvas do Power BI para telas menores, com tipografia e gráficos próprios. A interação cruzada admite uma categoria por vez, a partir do ranking ou do diagnóstico e a troca de seleção substitui o filtro anterior. Os modos específicos do Power BI Desktop e combinações com Ctrl entre categorias não foram reproduzidos.
- O DuckDB preserva centavos. O Power BI usa ponto flutuante nas medidas monetárias da origem importada. A auditoria observou R$ 0,01 de diferença na soma global UF, fora do conjunto de cartões obrigatório. Próximo aos limiares do DAX, essa diferença de representação pode afetar empates. A aplicação mantém os limiares e as regras recuperadas.
- O DAX do relatório define a cesta, inclusive estornos líquidos e participação parcial dos concorrentes. A elegibilidade mais estrita do Notebook 04 permanece documentada como uma regra diferente. Os prêmios UF do Raio-X e os insumos nacionais das métricas técnicas continuam em universos próprios.
- A cobertura validada é a geração de jan/2019–set/2026. O PBIP recuperado foi usado como referência sem alterar PBIX, notebooks ou Parquets. A comparação direta no Desktop cobriu o cenário obrigatório, a composição do ranking e as interações descritas. Os casos adicionais são testes de regressão sobre a tradução do DAX e os Parquets, sem alegar exportação de cada cenário do Desktop.
