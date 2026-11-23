# Evolução mensal do Market Share entre anos

## Origem da limitação

| Camada | Comportamento original |
|---|---|
| PBIR, visual `3c8780df0093c866e423` | Eixo `Eixo_Mes[Mês]`, legenda `Eixo_Historico[Ano]` e valor `Seletor_Metrica[Evolução Competitiva %]`. Mês sem ano não identifica um ponto cronológico. |
| `Seletor_Metrica.tmdl` | A opção Market Share chama `[Market Share Comparativo %]`. As verificações próprias de ano único e de faixa de meses da medida estão no ramo dos indicadores técnicos. |
| `Eixo_Historico.tmdl`, `[Market Share Comparativo %]` | Admite o ano do fim da seleção e o anterior. Chama `[Market Share Histórico %]`, que divide os prêmios históricos da referência pelos prêmios históricos do mercado. |
| `Eixo_Historico.tmdl`, `[Prêmios Base Histórico]` | Retorna `BLANK()` quando `YEAR(Inicio) <> YEAR(Fim)`. No eixo, testa o número do mês entre `MONTH(Inicio)` e `MONTH(Fim)` e reconstrói a data com o ano da legenda. Fora do eixo mensal, usa `YEAR(Fim) - AnoGrafico` para deslocar o intervalo. O subtítulo histórico antigo também tem uma mensagem para ano único, embora o PBIR desse gráfico não se vincule a essa medida. |
| Tradução web anterior | O backend só enumerava meses quando início e fim caíam no mesmo ano. O gráfico ordenava números de mês e agrupava por ano. Retirar só a condição no backend ainda deixaria janeiro antes de dezembro e sobreporia competências de anos diferentes. |

## Regra da entrega web

A série atual usa as competências da seleção em ordem crescente. No modo comparativo, cada ponto do ano anterior é observado 12 meses antes da competência exibida. Por exemplo, na posição de nov/2025, a comparação usa nov/2024. Uma data que pertence tanto à janela atual como à janela anterior pode aparecer nos dois papéis, em posições diferentes do eixo.

A carteira continua fixa, com os ramos cujo prêmio líquido da referência tem valor absoluto superior a R$ 0,01 no intervalo atual. A mesma carteira vale para todos os pontos atuais e anteriores. Se houver seleção de grupo de ramos, ela restringe a cesta da evolução. No numerador entra a seleção explícita de seguradoras ou, na ausência dela, o grupo histórico. O denominador soma o prêmio direto de todas as seguradoras nos mesmos ramos e na competência observada. Ausência de numerador, ausência de mercado e mercado zero mantêm o valor em branco. Um numerador observado com valor zero continua zero quando a divisão é válida.

A divergência em relação ao PBIX é deliberada e se restringe à evolução de Market Share em períodos entre anos. Os cartões, a tabela de diagnóstico, o ranking e os indicadores técnicos continuam com suas regras anteriores. Nenhum arquivo do Power BI foi alterado.

## Alteração DAX proposta para o PBIX

A proposta cria uma medida exclusiva para o gráfico mensal de Market Share. Ela mantém as medidas compartilhadas do modelo e o DAX de Sinistralidade e Margem, que ainda usam o gráfico original. As expressões abaixo são uma proposta para homologação posterior numa cópia do PBIX.

Crie duas tabelas calculadas **sem relacionamento** com as outras tabelas. Ordene `Rotulo` por `AnoMes` e `Serie` por `Deslocamento` em ordem decrescente ou, no visual, configure os papéis pela legenda. As datas do eixo são as competências de `dim_calendario`.

```dax
Eixo_MS_Ano_Mes =
SELECTCOLUMNS(
    VALUES(dim_calendario[data_mes]),
    "DataMes", dim_calendario[data_mes],
    "AnoMes", YEAR(dim_calendario[data_mes]) * 100 + MONTH(dim_calendario[data_mes]),
    "Rotulo", FORMAT(dim_calendario[data_mes], "mmm/yyyy", "pt-BR")
)
```

```dax
Eixo_MS_Serie =
DATATABLE(
    "Serie", STRING,
    "Deslocamento", INTEGER,
    {
        { "Período selecionado", 0 },
        { "Ano anterior", -12 }
    }
)
```

A medida de base valida a data **exibida** contra os limites da seleção. Só então ela desloca a data consultada. Os filtros de dimensão de data são substituídos para permitir a consulta ao ano anterior, mantendo os demais filtros aplicáveis.

```dax
Prêmios Base Evolução MS =
VAR Inicio = SELECTEDVALUE(Filtro_Mes_Inicial[Data])
VAR Fim = SELECTEDVALUE(Filtro_Mes_Final[Data])
VAR MesEixo = SELECTEDVALUE(Eixo_MS_Ano_Mes[DataMes])
VAR Deslocamento = SELECTEDVALUE(Eixo_MS_Serie[Deslocamento])
RETURN
    IF(
        NOT ISBLANK(Inicio)
            && NOT ISBLANK(Fim)
            && Inicio <= Fim
            && NOT ISBLANK(MesEixo)
            && MesEixo >= Inicio
            && MesEixo <= Fim
            && NOT ISBLANK(Deslocamento),
        VAR MesObservado = EDATE(MesEixo, Deslocamento)
        RETURN
            CALCULATE(
                SUM(fato_premios_uf[premio_direto]),
                REMOVEFILTERS(dim_calendario),
                TREATAS({ MesObservado }, dim_calendario[data_mes])
            )
    )
```

A medida final mantém a lógica de `[Prêmios Históricos Referência]` e `[Prêmios Históricos Mercado]`. A cesta é avaliada com `[Prêmios Referência]` no intervalo atual e fora do filtro de UF. Os seletores e eixos desconectados mantêm esse contexto independente do mês observado.

```dax
Market Share Evolução Mensal % =
VAR RamosFixos =
    FILTER(
        ALL(dim_ramo[ramo]),
        VAR Premio =
            CALCULATE([Prêmios Referência], REMOVEFILTERS(dim_uf))
        RETURN NOT ISBLANK(Premio) && ABS(Premio) > 0.01
    )
VAR Entidades = VALUES(Seletor_Entidade[coenti])
VAR TemEntidades =
    ISFILTERED(Seletor_Entidade[Seguradora])
        || ISFILTERED(Seletor_Entidade[coenti])
VAR Grupo = SELECTEDVALUE(Seletor_Grupo[cogrupo])
VAR PremioReferencia =
    SWITCH(
        TRUE(),
        TemEntidades,
            CALCULATE(
                [Prêmios Base Evolução MS],
                REMOVEFILTERS(dim_seguradora),
                REMOVEFILTERS(dim_grupo_segurador),
                REMOVEFILTERS(dim_ramo),
                TREATAS(Entidades, fato_premios_uf[coenti]),
                TREATAS(RamosFixos, dim_ramo[ramo])
            ),
        NOT ISBLANK(Grupo),
            CALCULATE(
                [Prêmios Base Evolução MS],
                REMOVEFILTERS(dim_seguradora),
                REMOVEFILTERS(dim_grupo_segurador),
                REMOVEFILTERS(dim_ramo),
                TREATAS({ Grupo }, fato_premios_uf[cogrupo_historico]),
                TREATAS(RamosFixos, dim_ramo[ramo])
            )
    )
VAR PremioMercado =
    CALCULATE(
        [Prêmios Base Evolução MS],
        REMOVEFILTERS(dim_seguradora),
        REMOVEFILTERS(dim_grupo_segurador),
        REMOVEFILTERS(dim_ramo),
        REMOVEFILTERS(fato_premios_uf[coenti]),
        REMOVEFILTERS(fato_premios_uf[cogrupo_historico]),
        TREATAS(RamosFixos, dim_ramo[ramo])
    )
RETURN
    IF(COUNTROWS(RamosFixos) > 0, DIVIDE(PremioReferencia, PremioMercado))
```

No visual mensal de Market Share, configure `Eixo_MS_Ano_Mes[Rotulo]` no eixo X, `Eixo_MS_Serie[Serie]` na legenda e `[Market Share Evolução Mensal %]` no eixo Y. Formate a medida como percentual com duas casas. Para manter competências sem nenhum ponto, ative a exibição de itens sem dados e filtre o eixo pelo intervalo selecionado com a medida abaixo. Para preservar lacunas, configure o gráfico para não conectar pontos nulos.

```dax
Exibir Mês Evolução MS =
VAR Inicio = SELECTEDVALUE(Filtro_Mes_Inicial[Data])
VAR Fim = SELECTEDVALUE(Filtro_Mes_Final[Data])
VAR MesEixo = SELECTEDVALUE(Eixo_MS_Ano_Mes[DataMes])
RETURN
    IF(
        NOT ISBLANK(Inicio)
            && NOT ISBLANK(Fim)
            && Inicio <= Fim
            && NOT ISBLANK(MesEixo)
            && MesEixo >= Inicio
            && MesEixo <= Fim,
        1
    )
```

A alteração inclui a configuração do visual. Trocar apenas a medida do gráfico existente mantém o eixo de mês sem ano. Para preservar o layout original dos indicadores técnicos e a legenda do comparativo de ano único, mantenha o visual original nessas situações. Caso se queira um único componente que também preserve essa apresentação, a troca automática entre as duas estruturas de eixo deve ser resolvida no visual. Os trechos DAX acima calculam o gráfico cronológico e não alternam os campos do visual.

## Validação e limites

| Cenário Caixa Seguradora | Resultado |
|---|---|
| Jan–set/2026 | 9 pontos em cada série, mantendo o share agregado homologado de 2,62% e a comparação de jan/2025 de 2,68216302%. |
| Nov/2025–mar/2026 | Nov/25 → Dez/25 → Jan/26 → Fev/26 → Mar/26, com 5 pontos em cada série. Ranking e diagnóstico carregaram. |
| Out/2024–fev/2025 | Out/24 → Nov/24 → Dez/24 → Jan/25 → Fev/25, com 5 pontos em cada série. |
| Out/2025–set/2026 | 12 competências e 24 pontos nas duas séries. O gráfico reduz os rótulos visíveis conforme a largura e mantém todos os pontos e tooltips. |
| Nov/2019–fev/2020 | Comparação vazia para nov/2018 e dez/2018, seguida dos valores disponíveis de jan/2019 e fev/2019. |
| Datas invertidas e grupo sem produção | Gráfico sem pontos. O navegador exibiu a mensagem de datas invertidas. |

Os quatro primeiros intervalos e as datas invertidas foram conferidos no navegador. A suíte de 24 testes passou, incluindo regressões do Raio-X e da Visão por UF. Os novos testes conferem as datas deslocadas, lacunas e o valor inicial de cada janela com uma consulta separada em DuckDB.

## Aplicação no Power BI Desktop

A cópia cronológica do PBIX foi gerada pelo Power BI Desktop e reaberta em uma nova janela. O Raio-X foi salvo com Caixa Seguradora, Market Share e nov/2025–mar/2026, para reproduzir a virada de ano ao entrar na página. O original e o backup feito antes da alteração tinham SHA-256 idênticos. Os PBIX dessa validação são preservados separadamente.

O visual passou a usar as tabelas desconectadas `Eixo_MS_Ano_Mes` e `Eixo_MS_Serie` e a medida `Evolução Competitiva Cronológica %`. Foram adicionadas também `Data Eixo Evolução`, `Deslocamento Série Evolução`, `Prêmios Base Evolução MS`, `Market Share Evolução Mensal %` e `Exibir Mês Evolução MS`. A lógica dos indicadores técnicos continua chamando a medida original.

| Comparação executada no Desktop | Resultado |
|---|---|
| Jan–set/2026, Market Share | 18 pontos original e 18 na cópia, zero diferenças a oito casas percentuais. |
| Jan–set/2026, Sinistralidade | 9 pontos em cada versão, zero diferenças a oito casas percentuais. |
| Jan–set/2026, Margem parcial | 9 pontos em cada versão, zero diferenças a oito casas percentuais. |
| Nov/2025–mar/2026, Market Share | 5 competências em ordem e 10 pontos nas duas séries, todos iguais aos da web a oito casas percentuais. A visualização também foi conferida após reabrir o PBIX. |

Na janela cruzando anos, o Desktop usa rótulos como `nov/2025` e `Ano anterior`. A web usa `Nov/25` e `12 meses antes`. A apresentação difere, e as séries comparam as mesmas competências.
