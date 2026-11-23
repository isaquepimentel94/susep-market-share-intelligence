# Checklist do primeiro deploy

Infraestrutura proposta para o piloto. Uma instância Render **Free**, com 0,1 CPU e 512 MB. A alternativa **Starter** oferece 0,5 CPU e os mesmos 512 MB por US$ 7/mês. O primeiro deploy está condicionado às decisões abaixo. [Planos de computação](https://render.com/docs/compute-plans) · [Preços](https://render.com/pricing)

## 1. Decisões do responsável pelo projeto

- [ ] Autorizar a criação do serviço no Render e indicar o repositório e a branch. O plano do Blueprint é Free. A troca para Starter exige aprovação do custo recorrente.
- [ ] Autorizar quais materiais devem ser publicados, incluindo o código e o Guia. Autorizar separadamente a transferência dos nove Parquets para o armazenamento privado e para o serviço que responderá às consultas.
- [x] Preparar a geometria pública. A derivação autorizada da malha de UFs do IBGE de 2023 está em `dist/uf-map.json`, com crédito na página e validação no build. O mapa anterior permanece na referência local ignorada. [Paridade do mapa público](./PARIDADE_MAPA_PUBLICO.md)
- [ ] Definir, se desejado, uma autorização própria para a Release do PBIX de posição estável após examinar o modelo importado, os metadados e os direitos dos ativos incorporados. O piloto pode abrir com o download oculto.

## 2. Provisionar o snapshot

No PowerShell, a partir de `market-share-web`, substitua o valor de `$source` pela pasta com a versão canônica dos arquivos. O pacote e o diretório de verificação abaixo são locais e ignorados pelo Git. Use um novo nome se eles já existirem.

```powershell
$source = 'CAMINHO_DA_PASTA_CURATED'
$bundle = 'data/susep-201901-202609.tar.gz'
python -B tools/snapshot.py verify --source $source
python -B tools/snapshot.py pack --source $source --archive $bundle
python -B tools/snapshot.py verify --archive $bundle
python -B tools/snapshot.py install --archive $bundle --target 'data/curated-verificacao'
python -B tools/snapshot.py verify --source 'data/curated-verificacao'
Get-FileHash -Algorithm SHA256 -LiteralPath $bundle
```

- [ ] Após autorização, enviar somente o pacote verificado para um objeto privado e versionado no armazenamento escolhido. Guardar o hash do pacote. O manifesto em `deploy/parquets-201901-202609.sha256` fixa os hashes de cada Parquet.
- [ ] Gerar uma URL HTTPS de leitura com validade para o build. Inserir o valor em `SUSEP_PARQUETS_ARTIFACT_URL` diretamente no Render. Renovar a URL quando for disparar um build após o vencimento. A URL não deve aparecer em arquivos, issues, mensagens de commit ou logs de depuração.
- [ ] Conferir que o build validou o pacote e que `SUSEP_DATA_DIR` aponta para `data/curated`, fora de `dist/`. O Start Command usa a cópia do build e descarta a variável com o endereço privado antes de iniciar o servidor.

O instalador aceita somente os nomes esperados, arquivos regulares e hashes do manifesto. Limita a 64 MiB o pacote e o fluxo expandido, rejeita destinos públicos e só promove a pasta após a validação completa. Uma nova edição do snapshot exige atualização explícita do manifesto, eventual revisão do limite e regressão.

## 3. Configuração no Render

Após autorização, há dois caminhos equivalentes. Usar apenas um deles.

1. **Blueprint.** No painel, escolher **New → Blueprint**, conectar o repositório autorizado, selecionar a branch e revisar `render.yaml` na raiz. Informar a URL privada quando o painel solicitar o segredo. A aplicação do Blueprint cria e inicia o serviço. Revisar o plano Free antes de aplicar. [Referência do Blueprint](https://render.com/docs/blueprint-spec)
2. **Manual.** Escolher **New → Web Service → Git Provider**, selecionar o repositório e a branch autorizados e copiar os valores da tabela abaixo. O botão **Deploy Web Service** cria e implanta o serviço. [Primeiro deploy no Render](https://render.com/docs/your-first-deploy)

| Campo | Valor para o primeiro serviço |
|---|---|
| Name | `susep-market-share` ou o nome escolhido para o serviço |
| Language/runtime | Python nativo, série 3.14 via `.python-version` |
| Region | Virginia, conforme o Blueprint |
| Root Directory | Vazio quando `market-share-web` for a raiz do repositório |
| Instance Type | Free |
| Build Command | `bash deploy/build.sh` |
| Start Command | `bash deploy/start.sh` |
| Pre-Deploy Command | Vazio |
| Health Check Path | `/healthz` |
| Auto-Deploy | Off |
| Persistent Disk | Ausente |
| `SUSEP_HOST` | `0.0.0.0` |
| `PORT` | Manter o valor injetado pelo Render |
| `SUSEP_DATA_DIR` | `data/curated` |
| `SUSEP_DUCKDB_MEMORY_LIMIT` | `192 MiB` |
| `SUSEP_DUCKDB_THREADS` | `1` |
| `SUSEP_QUERY_SLOTS` | `1` |
| `SUSEP_DUCKDB_TEMP_DIR` | `/tmp/susep-duckdb` |
| `SUSEP_PARQUETS_ARTIFACT_URL` | Inserir o segredo no painel |
| `SUSEP_PBIX_URL` | Deixar ausente |

Se o upload do snapshot exigir novo build, verificar o prazo do segredo e as franquias do workspace. O runtime Free pode hibernar e levar cerca de um minuto para acordar. O build Starter do Hobby é uma cota separada, de 500 minutos por mês. [Render Free](https://render.com/docs/free) · [Build Pipeline](https://render.com/docs/build-pipeline)

## 4. Arquivos candidatos ao primeiro envio

Lista da árvore de integração após as exclusões do Git. Ela inclui a apresentação estática anterior e os dois arquivos de instruções legados. O mapa autorizado ocupa `dist/uf-map.json` e a atribuição está na página Visão por UF. A checagem do Build Command verifica a proveniência e os códigos das 27 UFs antes de instalar dependências ou provisionar os dados. [Integração ao repositório existente](./INTEGRACAO_GITHUB.md)

```text
.gitattributes
.gitignore
.python-version
CHECKLIST_DEPLOY.md
COLOQUE_CAPTURAS_AQUI.txt
EVOLUCAO_MARKET_SHARE.md
INSTRUCOES.md
INTEGRACAO_GITHUB.md
PARIDADE_GUIA.md
PARIDADE_MA.md
PARIDADE_MAPA_PUBLICO.md
PARIDADE_POWER_BI.md
PARIDADE_SIMULADOR.md
PARIDADE_VISAO_UF.md
PLANO_PUBLICACAO.md
README.md
REVISAO_GITHUB.md
analysis_views.py
core.py
deploy/build.sh
deploy/parquets-201901-202609.sha256
deploy/start.sh
dist/app.js
dist/guide-data.json
dist/guide.css
dist/guide.js
dist/index.html
dist/ma.css
dist/ma.js
dist/simulation.css
dist/simulation.js
dist/styles.css
dist/uf-map.json
dist/uf.css
dist/uf.js
index.html
ma_views.py
render.yaml
requirements.txt
server.py
simulation.py
tests/caixa_2026.dax
tests/ma_referencia.dax
tests/ranking_caixa_2026.dax
tests/simulador_diagnostico_caixa_2026.dax
tests/simulador_validacao_caixa_2026.dax
tests/test_guide.mjs
tests/test_guide_data.py
tests/test_ma.py
tests/test_parity.py
tests/test_simulation.py
tests/test_snapshot.py
tests/test_uf.py
tests/test_web_deployment.py
tests/visao_uf.dax
tools/benchmark_hosting.py
tools/build_guide.py
tools/build_uf_map.py
tools/check_uf_map.py
tools/requirements-map.txt
tools/snapshot.py
uf_views.py
```

No Git, revisar tanto os candidatos (`git ls-files --others --exclude-standard`) como o conteúdo a enviar (`git diff --cached --name-only`). Entre as exclusões estão `data/`, Parquets, CSVs, arquivos compactados, PBIX, ambientes, caches, material de auditoria, `.env`, chaves e `work/local-maps/uf-map.powerbi.json`. Entre os arquivos que começam com `dist/uf-map`, somente o caminho canônico da geometria pública está liberado.

## 5. Homologação antes de divulgar a URL

- [ ] Conferir `/healthz`, catálogo, um cenário de cada endpoint analítico e a Visão por UF com a geometria autorizada. Conferir HTTP 404 para caminhos de Parquet e HTTP 400 para período inválido. Comparar os cenários conhecidos com os resultados registrados.
- [ ] Medir `/healthz` e o primeiro acesso após mais de 15 minutos ociosos no Free. Conferir que o snapshot volta com o artefato do build. Anotar o tempo total visto pelo usuário, incluindo o despertar do provedor.
- [ ] Repetir o teste de cache preenchido e consultas concorrentes. Medir p95 e picos de memória da instância, observar HTTP 5xx, reinícios e mensagens de OOM. Se a espera do Free for inadequada e houver margem de memória, o Starter é o próximo teste. Com aprovação de custo, alterar para `0.5c-512mb` em `render.yaml` se o serviço for gerenciado por Blueprint, ou nas configurações de computação se foi criado manualmente. Considerar 2 GB se houver pressão de memória ou falhas sustentadas em 512 MB, ou se a CPU do Starter não atender à latência necessária.
- [ ] Conferir controles de custo e tráfego antes de divulgar a URL. Se houver publicação do PBIX em outra etapa, configurar somente o endereço real do anexo aprovado.

### Comandos de regressão local

Com as dependências do projeto instaladas no ambiente ativo, preparar um `SUSEP_DATA_DIR` válido e executar.

```powershell
$env:SUSEP_DUCKDB_MEMORY_LIMIT = '192 MiB'
$env:SUSEP_DUCKDB_THREADS = '1'
$env:SUSEP_QUERY_SLOTS = '1'
python -B -m unittest tests.test_parity tests.test_uf tests.test_simulation tests.test_ma tests.test_web_deployment tests.test_snapshot
```

O benchmark abre um servidor de loopback isolado por perfil. No Windows, use um Python com `psutil` para o medidor. Use `--python` para apontar o servidor a outro Python que possua as dependências do projeto. No Linux, o medidor lê `/proc`.

```powershell
python -B tools/benchmark_hosting.py --data-dir $source --python .\.venv\Scripts\python.exe
```

As medições, as limitações dos testes locais e a comparação com 512 MB estão no [plano atualizado](./PLANO_PUBLICACAO.md).
