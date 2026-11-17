# Publicação do dashboard — sem ETL

1. Extraia o ZIP no seu computador. Não envie o ZIP inteiro para o GitHub.
2. Na página do repositório vazio, clique em **uploading an existing file**.
3. Envie `README.md`, `index.html`, `.gitignore`, `INSTRUCOES.md` e, se possível, a pasta `assets/` já com suas capturas de tela mais recentes.
4. Em **Commit changes**, salve os arquivos na branch `main`.
5. Em **Settings → Pages → Build and deployment**, escolha `Deploy from a branch` e a branch `main`, pasta `/(root)`. Clique em **Save**.
6. O endereço público será `https://isaquepimentel94.github.io/susep-market-share-intelligence/` após o primeiro deploy.

## Capturas de tela

Salve suas capturas do relatório após a atualização de setembro de 2026, na pasta `assets/`, com nomes exatos:

- `raio-x-market-share.png`
- `raio-x-sinistralidade.png`
- `raio-x-margem.png`
- `competitividade-uf.png`
- `guia-indicadores.png`

A página detecta automaticamente as imagens existentes. Sem imagens, mostrará as descrições e a metodologia, mas não as capturas.

## Privacidade

Não envie `.pbix`, notebooks `.ipynb`, Parquet, CSV, DuckDB, credenciais ou arquivos de extração. O `.gitignore` ajuda a prevenir envios por Git local, mas **não impede uploads manuais feitos pelo site do GitHub**.
