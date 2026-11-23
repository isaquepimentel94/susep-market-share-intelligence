# Revisão do repositório GitHub

Este é o registro da Etapa 9, referente ao commit local `28206de` e ao estado do repositório naquela etapa. A integração posterior ao repositório existente usa uma árvore separada. Para o estado atual e as instruções de envio, consulte o [relatório de integração](./INTEGRACAO_GITHUB.md).

## Arquivos incluídos e excluídos

Os **57 candidatos** da etapa anterior foram conferidos. A inclusão deste relatório levou a árvore inicial a **58 arquivos de texto**. A lista daquele commit pode ser consultada com `git ls-tree -r --name-only 28206de` no repositório local onde ele foi criado.

| Grupo | Arquivos | Conteúdo |
|---|---:|---|
| Aplicação Python | 6 | `server.py` e cinco módulos analíticos |
| Frontend | 13 | HTML, CSS, módulos JavaScript, Guia e mapa IBGE em `dist/` |
| Testes e consultas de referência | 14 | Testes Python/JavaScript e consultas DAX de paridade |
| Ferramentas | 6 | Provisionamento, validação e geração de ativos, dependências opcionais do gerador e benchmark |
| Configuração e deploy | 8 | `.gitignore`, `.gitattributes`, `.python-version`, `requirements.txt`, `render.yaml`, scripts e manifesto em `deploy/` |
| Documentação | 11 | README, evolução, paridade, plano, checklist e esta revisão |

O índice exclui os PBIX e backups, os arquivos de projeto e modelo do Power BI, os nove Parquets e outros dados, CSVs brutos, notebooks de trabalho, pacotes de dados, ambientes, caches, arquivos de configuração privada, chaves e a geometria anterior do Power BI. A verificação de `.gitignore` usou 11 caminhos representativos, cobrindo também `work/`, `powerbi/`, `notebooks/` e arquivos `.env`.

O ativo canônico `dist/uf-map.json` coincide com o SHA-256 homologado `d7c6a05f3ee985a87d7ca0f108c50d8820fed15ef10c5c4c02e376fa8808aac4`. O validador conferiu a proveniência IBGE BR_UF_2023 e os 27 pares oficiais de código e sigla. `.gitattributes` fixa LF no JSON, nos scripts de deploy e no manifesto, preservando o hash da geometria após checkout no Windows. A atribuição e os termos compatíveis com CC BY 4.0 são específicos da cartografia. A licença geral do software segue a decisão do titular. [Paridade do mapa público](./PARIDADE_MAPA_PUBLICO.md) · [Licenças no GitHub](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)

## Dados sensíveis e configuração de deploy

A revisão dos arquivos textuais no índice procurou padrões de chaves privadas, credenciais de serviços, tokens, URLs assinadas, endereços de e-mail e caminhos pessoais absolutos. A inspeção dos fixtures DAX, dos dois JSON de frontend e da documentação complementou a varredura. Nenhum valor de credencial, arquivo `.env`, caminho pessoal absoluto ou material privado foi encontrado na árvore preparada. O teste de provisionamento usa apenas valores sintéticos para verificar a ocultação de segredos.

As referências a PBIX e backups permanecem como evidência documental, com os links para caminhos locais removidos. Os binários estão fora do histórico. No `render.yaml`, `SUSEP_PARQUETS_ARTIFACT_URL` está declarado com `sync: false` sem valor. O Blueprint mantém o plano Free, o deploy automático desligado e o health check em `/healthz`. O build verifica o mapa e provisiona o snapshot fora de `dist/`. [Checklist do deploy](./CHECKLIST_DEPLOY.md) · [Segredos no Blueprint do Render](https://render.com/docs/blueprint-spec#prompting-for-secret-values)

Para preparar o commit, foram removidas duas linhas vazias finais de arquivos Python, com igualdade da árvore sintática conferida. O instalador de dados também passou a fechar o corpo de uma resposta HTTP de erro, com teste específico. As medidas e as consultas analíticas mantêm o comportamento homologado.

## Git local

A branch inicial é `main`. O primeiro commit usa a identidade técnica **Market Share Intelligence Web** e um endereço reservado de exemplo. Essa escolha evita gravar no histórico o e-mail pessoal configurado no Git. O repositório local não tem `origin` e a árvore foi validada com `git diff --cached --check`, `git ls-tree` e `git fsck`.

Para inspecionar a branch, o commit e a lista de arquivos:

```sh
git status --short --branch
git log -1 --oneline
git ls-tree -r --name-only HEAD
git remote -v
```

## Testes de empacotamento

| Teste | Resultado |
|---|---|
| Cópia limpa exportada do índice no Windows | Instalação de dependências fixadas em ambiente virtual novo e `pip check` aprovados. O SHA-256 do mapa permaneceu igual. |
| Manifesto e provisão offline | Empacotamento e instalação de nove Parquets verificados em área temporária separada do checkout. A aplicação iniciou com a configuração econômica e os scripts, caminhos e variáveis do Blueprint foram conferidos. |
| Testes direcionados | Seis testes de implantação e provisionamento passaram. A repetição com `ResourceWarning` tratado como erro confirmou o fechamento da resposta HTTP rejeitada. |
| Servidor Waitress em loopback | `/healthz`, catálogo, seis rotas de navegação no HTML, 13 ativos e quatro endpoints analíticos foram conferidos. O período inválido retornou 400. Parquet, geometria legada e arquivos operacionais fora de `dist/` retornaram 404. O catálogo veio sem URL de PBIX. |

O ensaio executou `server.py` com as variáveis correspondentes ao Blueprint no Windows. A validação do build nativo do Render e da inicialização após hibernação fazem parte da implantação autorizada. As auditorias e suítes analíticas anteriores foram preservadas como referência.

## Conectar o remoto quando autorizado

1. Escolher a conta ou organização e criar um repositório **vazio** no GitHub, mantendo a visibilidade privada enquanto a publicação estiver pendente. Copiar a URL HTTPS ou SSH fornecida na tela de configuração. [Importar código local para o GitHub](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github)
2. Se quiser associar o primeiro commit ao seu perfil, defina no repositório local seu nome de autoria e o endereço `noreply` fornecido pelo GitHub. Antes do primeiro envio, `git commit --amend --reset-author --no-edit` atualiza a autoria e muda o identificador do commit. [Configurar e-mail de commit](https://docs.github.com/en/account-and-profile/how-tos/email-preferences/setting-your-commit-email-address)
3. Na raiz local, conecte a URL copiada e confira o destino. A autenticação deve usar o gerenciador de credenciais ou SSH.

```powershell
$remote = Read-Host 'Cole a URL do repositório vazio'
git remote add origin $remote
git remote -v
```

4. Na etapa de envio autorizada, `git push -u origin main` publica a branch no remoto configurado. A visibilidade pública do repositório é uma decisão separada. [Gerenciar remotos](https://docs.github.com/en/get-started/git-basics/managing-remote-repositories)

## Pendências antes da publicação

- Autorizar o repositório remoto, a visibilidade e o envio do código, dos textos do Guia e da documentação. Se houver intenção de disponibilizar o projeto como código aberto, aprovar a licença geral.
- Autorizar separadamente o provisionamento do snapshot em armazenamento privado e o primeiro deploy no Render. Fornecer no painel a URL de leitura do artefato e verificar build, saúde e comportamento após ociosidade. [Checklist de deploy](./CHECKLIST_DEPLOY.md)
- Autorizar separadamente a publicação do PBIX de posição estável, após revisar o modelo importado e os metadados. Na etapa de publicação, configurar o endereço real da Release para habilitar o botão. [Plano de publicação](./PLANO_PUBLICACAO.md#geometria-e-pbix)
