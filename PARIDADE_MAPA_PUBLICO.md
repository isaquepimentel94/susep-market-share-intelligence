# Paridade do mapa público da Visão por UF

Validação em 22 de novembro de 2026 com a versão da web homologada e o cenário Caixa Seguradora, janeiro a setembro de 2026.

## Fonte e licença

A cartografia é **IBGE, Malha Municipal Digital 2023, Unidades da Federação (BR_UF_2023)**. O ZIP foi obtido diretamente do repositório oficial do IBGE. O Shapefile usa SIRGAS 2000 geográfico (`EPSG:4674`), UTF-8 e escala de origem de 1:250.000. A nota técnica da edição autoriza reutilização, adaptação e redistribuição com atribuição em termos compatíveis com **CC BY 4.0**. A Visão por UF exibe autoria, edição e licença sob a legenda e informa que a geometria foi projetada e simplificada para SVG. Os metadados de `uf-map.json` também registram a fonte, os termos aplicáveis e as transformações. [ZIP oficial BR_UF_2023](https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2023/Brasil/BR_UF_2023.zip) · [Página da edição](https://www.ibge.gov.br/geociencias/organizacao-do-territorio/estrutura-territorial/15774-malhas.html?edicao=42093) · [Nota técnica, p. 8](https://www.ibge.gov.br/biblioteca/visualizacao/livros/liv102152.pdf#page=8) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.pt-br)

| Arquivo | SHA-256 |
|---|---|
| ZIP oficial `BR_UF_2023.zip` | `5273fc6a3add9f3f18dbbcf4d844a03f9ed0c76a1fe779ce03cfff313488460c` |
| Geometria pública `dist/uf-map.json` | `d7c6a05f3ee985a87d7ca0f108c50d8820fed15ef10c5c4c02e376fa8808aac4` |
| Referência local em `work/local-maps/uf-map.powerbi.json` | `26f96e95cddea227b9f7a1c7eda21c129c08efd592c13d1183f382f257da0ec3` |

## Transformações

1. A leitura dos atributos oficiais `CD_UF` e `SIGLA_UF` confirma uma correspondência exclusiva para as 27 UFs. O JSON preserva o código numérico como texto no campo `code` e mantém a sigla em `uf`, usada pelos filtros e pelo endpoint.
2. Aplicação da mesma convenção cartográfica da web anterior, uma Albers equivalente esférica com meridiano central −54° e paralelos padrão −2° e −22°. As unidades intermediárias em quilômetros servem à simplificação. Os caminhos finais são transladados, escalados para uma extensão máxima de 640 unidades com 8 unidades de margem por lado e arredondados a duas casas no SVG.
3. O mapa de visão nacional omite partes com área projetada inferior a 12 km², abaixo de um pixel na dimensão de referência. A malha de origem tem 1.029 partes. O SVG mantém 46 partes, incluindo a ilha principal de Fernando de Noronha, e conserva todas as 27 UFs. O recorte elimina detalhes insulares pequenos e altera o desenho de algumas costas e ilhas. Os arquivos de origem preservam esses detalhes.
4. A simplificação Visvalingam–Whyatt usa tolerância de 4 km e considera a cobertura inteira, mantendo as fronteiras comuns. A verificação topológica da cobertura passou antes e depois da simplificação. Os 27 polígonos ou multipolígonos reconstruídos dos caminhos SVG de duas casas também foram válidos e formaram uma cobertura sem sobreposições e com arestas compartilhadas coincidentes. O resultado tem 5.822 vértices SVG, sem contar a repetição de fechamento de cada anel. [Shapely coverage_simplify](https://shapely.readthedocs.io/en/stable/reference/shapely.coverage_simplify.html)

| Região | Pares oficiais conferidos |
|---|---|
| Norte | 11 RO, 12 AC, 13 AM, 14 RR, 15 PA, 16 AP, 17 TO |
| Nordeste | 21 MA, 22 PI, 23 CE, 24 RN, 25 PB, 26 PE, 27 AL, 28 SE, 29 BA |
| Sudeste | 31 MG, 32 ES, 33 RJ, 35 SP |
| Sul | 41 PR, 42 SC, 43 RS |
| Centro-Oeste | 50 MS, 51 MT, 52 GO, 53 DF |

## Comparação visual e analítica

O mapa anterior usava um `viewBox` de 650,40 × 656,00. A nova extensão de 656,00 × 621,07 deixa a silhueta um pouco mais horizontal dentro do mesmo painel. A coloração coincide nas **27 UFs** no cenário de referência. As divisas e os contornos costeiros têm mais detalhe. A ilha principal de Fernando de Noronha aparece como parte de PE. As quatro formas decorativas sem código do mapa anterior deixaram de aparecer como formas separadas. A atribuição usa o espaço abaixo da legenda.

A resposta de `/api/visao-uf` foi idêntica byte a byte antes e depois da troca no cenário Caixa, inclusive os 27 registros de UF, os cartões, o ranking e a comparação anual. O SHA-256 do corpo foi `faf4b931b828bc37c40eb155b21a17c37f0fd98b6b408c36d15522393f24fa4b`. Os nove hashes dos Parquets conferiram com o manifesto. [Paridade analítica da Visão por UF](./PARIDADE_VISAO_UF.md)

| Indicador da Caixa | Antes e depois |
|---|---|
| UFs com atuação | 27 de 27 UFs |
| UFs na liderança | Em branco, exibido como travessão |
| UFs no Top 3 | 0 UFs |
| Maior participação por UF | 8,67% em PI |
| Tooltip de PI | 8,67%, posição em branco e R$ 18.837.475,83 |

## Testes de navegador e build

| Verificação | Resultado |
|---|---|
| Mapa e tooltips das 27 UFs | Todos os caminhos receberam foco e exibiram as três medidas do tooltip. Os nomes e rótulos preservaram o padrão anterior do endpoint. A cor de cada UF coincidiu com a referência. |
| Seleção de PI no mapa | O clique atualizou o estado pressionado, atenuou as outras UFs, destacou PI no gráfico de variação e exibiu a sobreposição estadual no ranking Brasil. Enter limpou a seleção. |
| Filtro a partir da variação | A seleção de DF destacou DF no mapa, exibiu as demais UFs em cinza e sobrepôs o recorte estadual no ranking. Um segundo clique limpou a seleção. |
| Responsividade e navegação | Em viewport de 390 × 844, o mapa e os gráficos ficaram em uma coluna, com a atribuição dentro da área útil e sem rolagem horizontal. Início → Visão por UF manteve Caixa, jan–set/2026 e os cartões. O console não registrou erros. |
| Testes automatizados | 12 testes de Visão por UF passaram. O teste HTTP verificou o vínculo do JSON com as 27 linhas da API e os pares de código e sigla. O teste do asset verificou a rejeição de proveniência ausente e código duplicado. |
| Build | O validador passou com o asset público e rejeitou o mapa legado. Uma segunda geração reproduziu o arquivo byte a byte. `pip check` passou. No ensaio offline com os nove Parquets provisionados sob uma pasta temporária, o mapa, `/healthz` e a API responderam corretamente e o acesso HTTP ao Parquet retornou 404. O inventário Git conferiu os 57 candidatos e permitiu somente `dist/uf-map.json` entre os caminhos de mapa verificados. |

A verificação local executou a validação da geometria e do manifesto de dados. O sandbox Windows bloqueou a inicialização do Git Bash. A execução integral do shell do build no Render permanece para a implantação autorizada. [Checklist de deploy](./CHECKLIST_DEPLOY.md)

## Reprodução local

Com o ZIP oficial em pasta ignorada pelo Git, execute a partir da raiz da aplicação. As dependências geográficas são usadas apenas na geração.

```powershell
python -m pip install -r tools/requirements-map.txt
python -B tools/build_uf_map.py 'work/BR_UF_2023.zip'
python -B tools/check_uf_map.py
python -B -m unittest tests.test_uf -v
```

## Arquivos alterados

| Grupo | Arquivos |
|---|---|
| Mapa e atribuição | `dist/uf-map.json`, `dist/index.html`, `dist/uf.css` |
| Geração, testes e build | `tools/build_uf_map.py`, `tools/requirements-map.txt`, `tools/check_uf_map.py`, `tests/test_uf.py`, `deploy/build.sh`, `.gitignore` |
| Documentação | `PARIDADE_MAPA_PUBLICO.md`, `PARIDADE_VISAO_UF.md`, `README.md`, `PLANO_PUBLICACAO.md`, `CHECKLIST_DEPLOY.md` |
| Referência local ignorada | `work/local-maps/uf-map.powerbi.json` |
