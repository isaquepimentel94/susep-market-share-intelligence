# Plano de publicação do Market Share Intelligence Web

O primeiro candidato é **um Web Service Render Free de 512 MB**, com frontend e API Python/DuckDB na mesma origem HTTPS. **Starter, com os mesmos 512 MB**, é a opção seguinte se a suspensão ou a latência do Free forem inconvenientes. A geometria pública do IBGE já está preparada. As demais decisões de divulgação estão no [checklist de deploy](./CHECKLIST_DEPLOY.md).

## Arquitetura e configuração

O proxy do Render termina o HTTPS e encaminha as requisições ao Waitress. Um único processo serve `dist/` e os endpoints `/api/catalog`, `/api/raio-x`, `/api/visao-uf`, `/api/simulacoes` e `/api/fusao-aquisicao`. O frontend continua usando caminhos relativos. O servidor abre os Parquets locais em DuckDB, conserva os cálculos e a serialização de decimais e responde `/healthz` após carregar o catálogo. Os testes e o build usam Python 3.14 e DuckDB 2.0.0. [Serviços web no Render](https://render.com/docs/web-services)

A alternativa de HTML/JS no GitHub Pages com API separada mantém o custo de CPU e RAM do backend, acrescenta uma URL de API e configuração de CORS, e exige coordenar dois deploys. O processamento permaneceria em Python/DuckDB. [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)

| Item | Perfil de 512 MB |
|---|---|
| Processo | Uma instância Waitress, 8 threads HTTP e limite atual de 64 conexões |
| DuckDB | `SUSEP_DUCKDB_MEMORY_LIMIT=192 MiB`, `SUSEP_DUCKDB_THREADS=1` e `SUSEP_DUCKDB_TEMP_DIR=/tmp/susep-duckdb` |
| Concorrência | `SUSEP_QUERY_SLOTS=1`. Requisições podem chegar juntas e enfileirar quando precisam executar uma consulta. |
| Cache | Mantém a capacidade de 32 resultados por endpoint analítico, 128 ao todo |
| Rede | `SUSEP_HOST=0.0.0.0` no Render e `PORT` definido pelo provedor. O padrão local continua `127.0.0.1:8000`. |
| Snapshot | `SUSEP_DATA_DIR=data/curated` no build do Render. Em execução local, `--data-dir` continua com precedência sobre `SUSEP_DATA_DIR`. |

Os padrões da aplicação local continuam quatro threads DuckDB e dois slots quando as novas variáveis estão ausentes. O limite de memória do DuckDB cobre a memória gerenciada pelo mecanismo. Python, caches, decimais, conexões e certas alocações do DuckDB integram a memória total do processo. Por isso a homologação acompanha o pico residente e, no Windows, o pico de memória privada comprometida. [Guia de memória do DuckDB](https://duckdb.org/docs/current/guides/performance/oom) · [Contadores de memória do Windows](https://learn.microsoft.com/pt-br/windows/win32/api/psapi/ns-psapi-process_memory_counters_ex)

## Custos e critérios para mudar de plano

| Render | Recursos | Custo do serviço e uso sugerido |
|---|---|---|
| Free | 0,1 CPU, 512 MB | US$ 0 dentro das franquias. Hiberna após 15 minutos sem tráfego, pode levar cerca de um minuto para acordar e tem 750 h/mês compartilhadas no workspace. O sistema de arquivos de runtime é efêmero. Usar para piloto. |
| Starter `0.5c-512mb` | 0,5 CPU, 512 MB | US$ 7/mês, sem a hibernação por inatividade do Free. Primeiro candidato se o teste no Render mostrar fila ou espera de startup excessiva com a memória dentro do orçamento. |
| Standard `1c-2g` | 1 CPU, 2 GB | US$ 25/mês. Avaliar se 512 MB produzirem OOM ou reinícios sob a carga alvo com um slot, ou se 0,5 CPU ficar insuficiente para a latência necessária. |

O workspace Hobby inclui **5 GB/mês de tráfego de saída** e **500 minutos de build**. O build Starter do Hobby roda com 2 CPUs e 8 GB, independentemente da instância de runtime. Exceder franquias pode bloquear novos builds, suspender serviços Free ou gerar cobrança conforme configuração da conta. O orçamento não inclui eventual armazenamento privado, impostos, domínio ou saída excedente. No plano econômico, a cópia dos Parquets é montada no artefato do build e o runtime usa disco efêmero para arquivos temporários. [Planos](https://render.com/docs/compute-plans) · [Preços](https://render.com/pricing) · [Render Free](https://render.com/docs/free) · [Build Pipeline](https://render.com/docs/build-pipeline) · [Tráfego de saída](https://render.com/docs/outbound-bandwidth)

## Snapshot e arquivos de implantação

Os nove arquivos de jan/2019 a set/2026 ocupam **61.328.111 bytes (58,49 MiB)**. São seis dimensões, o fato nacional, o fato UF e a ponte mensal seguradora–grupo. Os fatos permanecem separados. A análise da Etapa 6 verificou chaves institucionais, competências, ramos, UFs e dados monetários. O servidor usa o snapshot verificado para entregar apenas as consultas da aplicação. [SUSEP Dados Abertos](https://www.gov.br/susep/pt-br/acesso-a-informacao/dados-abertos) · [SES/SUSEP](https://www2.susep.gov.br/menuestatistica/ses/principal.aspx)

| Arquivo | Papel |
|---|---|
| `render.yaml` | Blueprint de um Web Service Free, deploy automático desligado, sem valores de credenciais |
| `deploy/build.sh` | Valida a geometria pública do IBGE, instala dependências fixadas e provisiona o snapshot autenticado |
| `deploy/start.sh` | Resolve a raiz do aplicativo, remove a variável privada do ambiente do servidor e executa Python com os dados empacotados no build |
| `tools/snapshot.py` e `deploy/parquets-201901-202609.sha256` | Empacotamento reprodutível, validação por SHA-256, instalação dos nove Parquets em pasta fora de `dist/` |
| `tools/benchmark_hosting.py` | Medição local de inicialização, cache, concorrência, respostas e memória |
| `.gitignore` e `.gitattributes` | Separam arquivos locais e sigilosos, liberam o mapa público e padronizam o fim de linha dos scripts e do manifesto |

O build recebe uma URL HTTPS temporária em `SUSEP_PARQUETS_ARTIFACT_URL`, via variável secreta do Render. O instalador confere nomes, tipos e hashes, rejeita links e duplicatas e recusa instalação em `dist/`. O start usa o resultado do build, sem baixar os dados a cada despertar. A URL da origem privada deve ser renovada para builds futuros conforme a validade. O repositório contém apenas o manifesto de hashes e o código do instalador. [Variáveis e segredos no Render](https://render.com/docs/blueprint-spec#prompting-for-secret-values)

O [checklist](./CHECKLIST_DEPLOY.md) traz o comando para o pacote privado, a lista exata de candidatos a Git e as configurações para aplicar o Blueprint ou criar o serviço manualmente. O build inicial e o teste de reabertura após hibernação ficam para o Render, depois da autorização.

## Geometria e PBIX

A Visão por UF usa a malha nacional **BR_UF_2023** do IBGE, em termos compatíveis com **CC BY 4.0**. A derivação pública em `dist/uf-map.json` inclui os 27 códigos oficiais. A página credita o IBGE e informa que a geometria foi simplificada e projetada. O build valida a nova proveniência. A geometria anterior do Power BI fica sob `work/local-maps/`, fora da raiz pública e do inventário Git. [Paridade do mapa público](./PARIDADE_MAPA_PUBLICO.md) · [Nota técnica do IBGE, p. 8](https://www.ibge.gov.br/biblioteca/visualizacao/livros/liv102152.pdf#page=8)

O `SUSEP - Market Share Simulador - Posicao Estavel.pbix` tem 108,01 MiB e SHA-256 `1AAB22E455FB33288FC49FD1626F75B52AF8BBA37B49F2ACD3A5DB7F75827021`. A cópia fica fora do histórico Git. Após revisão dos metadados, do Power Query e do modelo importado, uma Release autorizada pode sediar o binário. Só configurar `SUSEP_PBIX_URL` após testar a URL por tag e conferir o SHA-256 do download. [Arquivos grandes no GitHub](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github) · [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)

## Homologação local

Medições no Windows com Python 3.14.7, DuckDB 2.0.0 e oito CPUs lógicas. O benchmark inicia o Waitress real em loopback. Cada execução completa carrega o catálogo, preenche 32 chaves distintas por rota analítica, repete as 128 consultas com o cache aquecido e dispara três pares de M&A concorrentes no intervalo completo de 93 meses, com 178 seguradoras e pares A/B distintos. As medições incluem o processo Python servidor, o launcher da venv e o cache dos resultados. O Windows registra os picos de cada processo. A soma desses picos é um limite superior conservador para a árvore.

| Reprodução completa | Até `/healthz` | RSS da árvore após replay | Limite superior do pico RSS | Limite superior do pico de commit privado | Mediana de um par M&A |
|---|---:|---:|---:|---:|---:|
| Referência, configuração padrão com 4 threads e 2 slots | 0,95 s | 106,51 MiB | 302,37 MiB | 311,73 MiB | 3,05 s |
| Econômico, 192 MiB, 1 thread e 1 slot, com teto por processo de 512.000.000 bytes no Windows | 0,93 s | 83,82 MiB | 151,42 MiB | 128,46 MiB | 6,34 s |

No perfil econômico, o processo servidor atingiu **147,29 MiB residentes** e **127,63 MiB de commit privado**. O teto de 512.000.000 bytes foi aplicado a cada processo por Windows Job Object e cobriu a execução completa. As 262 requisições analíticas retornaram 200. Após aquecer o cache, as medianas por rota ficaram entre 15,8 e 17,0 ms naquele ambiente. O limite de commit no Windows e o RSS medido são métricas distintas. Um limite Linux também pode contabilizar cache de arquivos e demais processos da instância. O teste local demonstra folga na carga amostrada e, até aqui, não indica necessidade de 2 GB. O cgroup e a disponibilidade do Render ainda precisam de medição. [Limites do Windows Job Object](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information)

### Sensibilidade à CPU

Um segundo lote aplicou ao grupo de processos cotas aproximadas de 0,1 e 0,5 CPU, mantendo o teto de commit e a configuração econômica. Foram três chaves por rota em cada fase de cache e um par de M&A com a base completa. A tabela mostra inicialização local e medianas sem cache. A duração do par é uma única observação por cota. As duas execuções retornaram HTTP 200 em toda a carga.

| Cota aproximada no Windows | Até `/healthz` | Raio-X | Visão por UF | Simulador | M&A | Par completo de M&A |
|---|---:|---:|---:|---:|---:|---:|
| 0,1 CPU, aproximação do Free | 5,13 s | 8,91 s | 4,72 s | 2,39 s | 2,98 s | 62,94 s |
| 0,5 CPU, aproximação do Starter | 0,94 s | 1,81 s | 0,74 s | 0,53 s | 0,61 s | 11,79 s |

O Free é candidato para o piloto. O ensaio indica que a CPU e o despertar do serviço podem ditar a experiência. A passagem para Starter deve ser avaliada pelo tempo observado no Render, especialmente com consultas pesadas e cache frio. O ensaio local não inclui o despertar do provedor, sua rede ou a distribuição de CPU do Linux.

- **Paridade.** Na série comparativa sem o teto do Windows, as 786 requisições de carga retornaram 200. Os hashes do catálogo, das quatro rotas e dos pares M&A coincidiram entre a configuração de referência e as duas variantes de 192 MiB com um e dois slots. Os replays coincidiram com o preenchimento do cache. O perfil de um slot limita a simultaneidade analítica e deixa mais folga operacional para 512 MB.
- **Regressões focalizadas.** Os 47 testes analíticos e HTTP passaram com os ajustes econômicos. Os quatro testes de provisionamento cobriram manifesto, pacote determinístico, hash inválido, entradas inesperadas no arquivo compactado, destino público e erros de download com valores privados omitidos. A sequência de empacotar, verificar e instalar também passou com o snapshot real de nove Parquets.
- **Preparação de deploy.** A leitura YAML local confirmou os campos principais, os caminhos dos scripts e o segredo sem valor no Blueprint. O pipeline Python foi exercitado no Windows. O mapa público e o inventário Git atual foram conferidos na etapa de geometria. Os comandos de build e start permanecem por executar no runtime Linux do Render. [Paridade do mapa público](./PARIDADE_MAPA_PUBLICO.md)
