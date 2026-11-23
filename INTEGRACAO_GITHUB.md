# Integração ao GitHub existente

A branch local `integracao/market-share-web` está na pasta `market-share-web-integracao`. Ela parte da `main` remota e incorpora o conteúdo da aplicação revisada. O checkout e o commit local da Etapa 9 permanecem em `market-share-web`.

## Histórico e escopo

| Referência | Evidência |
|---|---|
| Repositório GitHub | Público, com branch padrão `main`. [Metadados do repositório](https://api.github.com/repos/isaquepimentel94/susep-market-share-intelligence) |
| Base da integração | `806b569a40b2dcb0a77edcad63e1449568c9c548`, o segundo commit do histórico remoto. [Commit no GitHub](https://github.com/isaquepimentel94/susep-market-share-intelligence/commit/806b569a40b2dcb0a77edcad63e1449568c9c548) |
| Release anterior | A tag `1.0` aponta para `ffa5792d95055bdbdebed48ee6af9967feadee2b`, ancestral da base. A Release mantém o ativo `Susep.-.Market.Share.pbix`, de 113.245.378 bytes. [Release 1.0](https://github.com/isaquepimentel94/susep-market-share-intelligence/releases/tag/1.0) · [Metadados do ativo](https://api.github.com/repos/isaquepimentel94/susep-market-share-intelligence/releases/assets/757605631) |
| Aplicação da Etapa 9 | `28206de0acf98085cf04eff5f8723e60cd6f5c73`, com 58 arquivos. Continua na `main` do checkout local original. |

Os históricos local e remoto não tinham ancestral em comum. A integração importou os arquivos selecionados do commit local em um novo commit descendente de `806b569`. Os dois commits remotos continuam na ancestralidade, e a comparação da branch de integração com a base mostra **57 adições, duas modificações e zero exclusões**, com **62 arquivos** na árvore final. O remoto `origin` foi configurado localmente para o repositório informado.

## Diferenças reconciliadas

| Caminho | Decisão |
|---|---|
| `README.md` | Passa a descrever a aplicação interativa, as fontes, a arquitetura e a execução local. Identifica a apresentação antiga e a Release existente sem anunciar hospedagem da aplicação. |
| `.gitignore` | Combina as proteções revisadas da aplicação com as exclusões legadas de ETL, notebooks, planilhas, bancos locais e arquivos compactados. |
| `index.html` da raiz | Preservado byte a byte como a apresentação estática anterior. |
| `INSTRUCOES.md` e `COLOQUE_CAPTURAS_AQUI.txt` | Preservados byte a byte como material da apresentação estática. |
| `dist/index.html` e módulos da aplicação | Copiados do commit local com os mesmos blobs. O Waitress continua servindo a entrada em `dist/`. |
| `CHECKLIST_DEPLOY.md` e `REVISAO_GITHUB.md` | O checklist lista a nova árvore. A revisão anterior identifica o estado da Etapa 9. [Inventário](./CHECKLIST_DEPLOY.md#4-arquivos-candidatos-ao-primeiro-envio) |

O GitHub informou `has_pages=false` no momento da consulta. As instruções antigas mencionam `main` e `/(root)` como fonte pretendida para a apresentação. GitHub Pages serve arquivos estáticos. A aplicação interativa depende dos endpoints Python/DuckDB e mantém o fluxo de hospedagem separado. [Instruções legadas](./INSTRUCOES.md) · [Como funciona o GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)

A Release `1.0` permanece com o PBIX anterior. A integração mantém `SUSEP_PBIX_URL` sem valor e reserva a publicação da cópia de posição estável para uma revisão separada.

## Dados e validação local

- O inventário verificou 62 arquivos e os caminhos dos dois commits remotos. A árvore de integração exclui Parquets, PBIX, CSVs, extrações, notebooks, arquivos de ambiente e chaves. A varredura dos textos não encontrou padrões de tokens, credenciais, URLs assinadas ou caminhos pessoais absolutos.
- Foram conferidos os blobs dos três arquivos legados e **54 arquivos** idênticos aos do commit da Etapa 9. Dessa forma, cálculos, JavaScript, dados do Guia, mapa e scripts de execução foram preservados. O mapa público mantém o SHA-256 homologado e o validador confirmou os 27 códigos do IBGE. [Paridade do mapa público](./PARIDADE_MAPA_PUBLICO.md)
- **Sete testes** passaram em uma árvore limpa exportada do índice, usando os Parquets autorizados por caminho externo. O conjunto inclui implantação, provisionamento e integração HTTP da Visão por UF. `pip check` aprovou o ambiente.
- O Waitress serviu `dist/index.html` em `/` e `/index.html`, entregou os 13 ativos e retornou 200 nos quatro endpoints analíticos, no catálogo e em `/healthz`. A competência inválida retornou 400. Parquet, mapa legado e documentos na raiz retornaram 404 por HTTP. O catálogo não trouxe URL de PBIX.

## Revisar e publicar após autorização

Na pasta `market-share-web-integracao`, confira a branch e as diferenças locais.

```powershell
git status --short --branch
git log --oneline --graph -3
git diff --name-status origin/main...HEAD
git diff origin/main...HEAD -- README.md .gitignore
```

Antes de qualquer envio, atualize a referência remota e confirme que ela continua ancestral da integração. Se a verificação falhar, examine os novos commits da `main` e revise a integração antes de enviá-la.

```powershell
git fetch --no-tags origin refs/heads/main:refs/remotes/origin/main
if ($LASTEXITCODE -ne 0) { throw 'Falha ao consultar a main remota.' }
git merge-base --is-ancestor origin/main HEAD
if ($LASTEXITCODE -ne 0) { throw 'A main remota mudou. Revise a integração.' }
git diff --name-status origin/main...HEAD
```

Com autorização para publicar o código no repositório público, envie a branch de integração e abra um pull request para `main`.

```powershell
git push -u origin integracao/market-share-web
```

Antes de mesclar o pull request, confira o estado de **Settings → Pages**. Caso a apresentação legada venha a ser publicada pela raiz, avalie o conteúdo que essa fonte estática incluirá. O primeiro deploy da aplicação interativa no Render, o provisionamento dos Parquets e a publicação de outro PBIX são etapas separadas. [Configuração de origem do Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) · [Checklist de deploy](./CHECKLIST_DEPLOY.md)
