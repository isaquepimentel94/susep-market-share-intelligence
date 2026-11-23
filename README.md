# Market Share Intelligence Web

Aplicação web para analisar a posição competitiva das seguradoras no mercado brasileiro. O painel reúne participação de mercado, distribuição por UF, simulações de ranking e efeitos de fusões e aquisições. A versão de dados homologada cobre janeiro de 2019 a setembro de 2026.

A aplicação interativa está preparada para execução local e futura hospedagem. Sua entrada é `dist/index.html`, servida pela aplicação Python.

## Páginas

| Página | O que consultar |
|---|---|
| Início | Seleção de grupo econômico e seguradoras de referência |
| Raio-X Competitivo | Indicadores, ranking, evolução mensal e diagnóstico da carteira |
| Visão por UF | Participação por estado, ranking e ganhos ou perdas em pontos percentuais |
| Simulações Estratégicas | Cenários de crescimento da referência e dos concorrentes, posição e metas |
| Fusão e Aquisição | Participação e posição combinadas, concentração e detalhamento por UF e grupo de ramos |
| Guia de Indicadores | Definições, fórmulas, interpretações e fontes recuperadas do modelo |

## Arquitetura

O servidor Python usa Waitress para servir o frontend HTML/CSS/JavaScript em `dist/` e a API na mesma origem. DuckDB consulta nove Parquets fora da raiz pública. Os módulos analíticos ficam em `core.py`, `analysis_views.py`, `uf_views.py`, `simulation.py` e `ma_views.py`. A API retorna os resultados já calculados, preservando decimais monetários até a formatação. O JavaScript gerencia filtros, interação e apresentação.

`/healthz` verifica a disponibilidade do serviço. O Blueprint em `render.yaml` descreve uma implantação futura, e o diretório `deploy/` guarda os scripts de build, inicialização e o manifesto SHA-256 do snapshot. [Plano de publicação](./PLANO_PUBLICACAO.md) · [Checklist de deploy](./CHECKLIST_DEPLOY.md)

## Apresentação estática e Power BI

O [`index.html` da raiz](./index.html) preserva a apresentação estática anterior. As [instruções legadas](./INSTRUCOES.md) se referem a essa apresentação no GitHub Pages. A aplicação interativa usa a API Python/DuckDB e tem seu próprio fluxo de hospedagem. [Integração ao repositório existente](./INTEGRACAO_GITHUB.md)

A [Release 1.0](https://github.com/isaquepimentel94/susep-market-share-intelligence/releases/tag/1.0) contém o PBIX publicado anteriormente. A cópia de posição estável tem uma revisão de publicação separada.

## Fontes e metodologia

- **Mercado segurador.** Os dados vêm do Sistema de Estatísticas da SUSEP. O modelo separa prêmios nacionais e estaduais e aplica as regras de comparabilidade e ranking de cada página. As comparações usam os ramos da carteira da referência no contexto da medida. [SES/SUSEP](https://www2.susep.gov.br/menuestatistica/ses/principal.aspx) · [Paridade do Raio-X](./PARIDADE_POWER_BI.md) · [Paridade da Visão por UF](./PARIDADE_VISAO_UF.md)
- **Cartografia.** IBGE, Malha Municipal Digital 2023, `BR_UF_2023`. A geometria pública foi projetada, simplificada e convertida em caminhos SVG. A nota técnica do IBGE estabelece termos de reutilização compatíveis com CC BY 4.0, com atribuição. [Nota técnica do IBGE, p. 8](https://www.ibge.gov.br/biblioteca/visualizacao/livros/liv102152.pdf#page=8) · [Licença de referência](https://creativecommons.org/licenses/by/4.0/deed.pt-br) · [Transformações e validação](./PARIDADE_MAPA_PUBLICO.md)
- **Cenários.** O simulador recalcula participação e posição com as taxas escolhidas. Em M&A, o HHI descreve a concentração no mercado da carteira comparável. Os resultados dependem de entidade, período e filtros. [Paridade do Simulador](./PARIDADE_SIMULADOR.md) · [Paridade de M&A](./PARIDADE_MA.md)

Os termos de reutilização da cartografia se aplicam ao mapa do IBGE. A licença geral do software fica a cargo do titular do projeto.

## Execução local

Use Python 3.14 e uma cópia autorizada dos nove Parquets da versão homologada. O manifesto informa os nomes e hashes. Os Parquets e os arquivos do Power BI são mantidos fora do repositório. [Provisionamento do snapshot](./CHECKLIST_DEPLOY.md#2-provisionar-o-snapshot) · [Manifesto SHA-256](./deploy/parquets-201901-202609.sha256)

**Windows, no PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:SUSEP_DATA_DIR = 'CAMINHO_DA_PASTA_CURATED'
.\.venv\Scripts\python.exe -B tools/snapshot.py verify --source $env:SUSEP_DATA_DIR
.\.venv\Scripts\python.exe -B server.py
```

**Linux ou macOS, no terminal**

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
export SUSEP_DATA_DIR='/caminho/para/curated'
.venv/bin/python -B tools/snapshot.py verify --source "$SUSEP_DATA_DIR"
.venv/bin/python -B server.py
```

Substitua o caminho de exemplo pela pasta autorizada e abra a aplicação no navegador. O servidor usa `127.0.0.1:8000` por padrão. Para trocar a porta, acrescente `--port 8001`. [Abrir a aplicação local](http://127.0.0.1:8000/)

## Testes

Com o ambiente virtual ativo e `SUSEP_DATA_DIR` configurado para o snapshot homologado, execute:

```text
python -B tools/check_uf_map.py
python -B -m unittest tests.test_web_deployment tests.test_snapshot
```

As suítes de paridade ficam em `tests/` e podem ser executadas com `python -B -m unittest discover -s tests -v`. Node.js é usado apenas no teste opcional do Guia, com `node --test tests/test_guide.mjs`. [Validação do Guia](./PARIDADE_GUIA.md)

## Limitações

- A cobertura temporal e os vínculos entre seguradoras e grupos econômicos dependem do snapshot disponível.
- Simulações representam os parâmetros escolhidos e devem ser interpretadas no recorte da carteira. O HHI descreve concentração nesse recorte.
- A malha do IBGE foi generalizada para a visualização nacional. Alguns detalhes de costa e pequenas ilhas foram omitidos, e a interface mantém as 27 UFs. [Paridade do mapa público](./PARIDADE_MAPA_PUBLICO.md)
- O botão de download só aparece quando há uma URL de Release configurada para o PBIX autorizado. [Plano de publicação](./PLANO_PUBLICACAO.md)
