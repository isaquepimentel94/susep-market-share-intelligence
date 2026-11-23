"""Serve the SUSEP dashboard and Parquet queries on a single origin."""

import argparse
import errno
import json
import logging
import os
import re
import threading
from collections import defaultdict
from contextlib import contextmanager
from decimal import Decimal
from functools import lru_cache
from http import HTTPStatus
from pathlib import Path
from urllib.parse import parse_qs

import duckdb
from waitress import serve
from werkzeug.exceptions import NotFound
from werkzeug.utils import send_from_directory
from werkzeug.wrappers import Request, Response

from analysis_views import get_analysis
from core import dashboard_core
from ma_views import get_ma
from simulation import get_simulation
from uf_views import get_uf_analysis


ROOT = Path(__file__).resolve().parent
LOGGER = logging.getLogger(__name__)
TABLES = (
    "dim_calendario", "dim_grupo_ramo", "dim_grupo_segurador", "dim_ramo",
    "dim_seguradora", "dim_uf", "fato_premios_nacional", "fato_premios_uf",
    "ponte_seguradora_grupo_mes",
)
MONTHS = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")
METRICS = {"share", "sinistralidade", "margem"}
DEFAULTS = {
    "entities": ["05631"], "group": "00230",
    "start": "202601", "end": "202609", "metric": "margem",
    "ma": {"companyA": "05177", "companyB": "06238"},
}


def find_data_dir(explicit=None):
    configured = explicit or os.environ.get("SUSEP_DATA_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    candidates = (
        ROOT / "data" / "curated",
        ROOT.parent / "data" / "curated",
        Path.home() / "Downloads" / "SUSEP Projeto" / "susep_market_share" / "data" / "curated",
    )
    return next((path for path in candidates if path.is_dir()), candidates[0])


def positive_env(name, default):
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"{name} deve ser um inteiro positivo.") from None
    if value < 1:
        raise ValueError(f"{name} deve ser um inteiro positivo.")
    return value


def open_database(folder):
    paths = {table: (folder / f"{table}.parquet").resolve() for table in TABLES}
    missing = [path.name for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Parquets ausentes em {folder}: {', '.join(missing)}")
    config = {"threads": positive_env("SUSEP_DUCKDB_THREADS", 4)}
    for setting, env_name in (
        ("memory_limit", "SUSEP_DUCKDB_MEMORY_LIMIT"),
        ("temp_directory", "SUSEP_DUCKDB_TEMP_DIR"),
    ):
        if value := os.environ.get(env_name):
            config[setting] = value
    db = duckdb.connect(config=config)
    try:
        for name, path in paths.items():
            db.read_parquet(str(path)).create_view(name)
    except Exception:
        db.close()
        raise
    return db


def build_catalog(db):
    entities = db.execute(
        "SELECT coenti, seguradora FROM dim_seguradora ORDER BY seguradora, coenti"
    ).fetchall()
    groups = db.execute("""
        SELECT g.cogrupo, g.grupo_segurador
        FROM dim_grupo_segurador g
        WHERE EXISTS (SELECT 1 FROM ponte_seguradora_grupo_mes p WHERE p.cogrupo = g.cogrupo)
        ORDER BY g.grupo_segurador, g.cogrupo
    """).fetchall()
    linked = db.execute("""
        SELECT DISTINCT p.cogrupo, p.coenti
        FROM ponte_seguradora_grupo_mes p
        JOIN dim_seguradora s USING (coenti)
        ORDER BY p.cogrupo, p.coenti
    """).fetchall()
    months = db.execute("SELECT damesano FROM dim_calendario ORDER BY data_mes").fetchall()

    memberships = defaultdict(list)
    for group, entity in linked:
        memberships[group].append(entity)

    return {
        "entities": [{"code": code, "name": name} for code, name in entities],
        "groups": [{"code": code, "name": name} for code, name in groups],
        "memberships": dict(memberships),
        "months": [
            {"code": code, "label": f"{MONTHS[int(code[4:]) - 1]}/{code[:4]}"}
            for (code,) in months
        ],
        "defaults": dict(DEFAULTS),
    }


def single_filter(params, key, fallback=None):
    values = params.get(key, [fallback])
    if len(values) != 1:
        raise ValueError(f"Filtro repetido: {key}.")
    return values[0] or fallback


class Service:
    def __init__(self, db):
        self.db = db
        self.catalog = build_catalog(db)
        self.entities = {item["code"] for item in self.catalog["entities"]}
        self.groups = {item["code"] for item in self.catalog["groups"]}
        self.months = [item["code"] for item in self.catalog["months"]]
        self.branch_groups = {code for (code,) in db.execute("SELECT gracodigo FROM dim_grupo_ramo").fetchall()}
        self.states = {code for (code,) in db.execute("SELECT uf FROM dim_uf").fetchall()}
        self._slots = threading.BoundedSemaphore(positive_env("SUSEP_QUERY_SLOTS", 2))
        self._connection_lock = threading.Lock()
        self._cached_query = lru_cache(maxsize=32)(self._query)
        self._cached_uf_query = lru_cache(maxsize=32)(self._query_uf)
        self._cached_simulation = lru_cache(maxsize=32)(self._query_simulation)
        self._cached_ma = lru_cache(maxsize=32)(self._query_ma)

    @contextmanager
    def connection(self):
        # DuckDB cursors are independent connections. Serialize cursor creation.
        with self._slots:
            with self._connection_lock:
                cursor = self.db.cursor()
            try:
                yield cursor
            finally:
                cursor.close()

    def reference_filters(self, params):
        start = single_filter(params, "start", self.months[0])
        end = single_filter(params, "end", self.months[-1])
        entities = tuple(sorted(set(filter(None, params.get("entity", [])))))
        group = single_filter(params, "group")
        if start not in self.months or end not in self.months:
            raise ValueError("Competência fora do calendário disponível.")
        if any(entity not in self.entities for entity in entities):
            raise ValueError("Seguradora desconhecida.")
        if group and group not in self.groups:
            raise ValueError("Grupo econômico desconhecido.")
        return start, end, entities, group

    def analyze(self, params):
        start, end, entities, group = self.reference_filters(params)
        metric = single_filter(params, "metric", DEFAULTS["metric"])
        selected_insurer = single_filter(params, "selected_insurer")
        selected_branch_group = single_filter(params, "selected_branch_group")
        if metric not in METRICS:
            raise ValueError("Indicador desconhecido.")
        if selected_insurer and selected_insurer not in self.entities:
            raise ValueError("Seguradora do ranking desconhecida.")
        if selected_branch_group and selected_branch_group not in self.branch_groups:
            raise ValueError("Grupo de ramos desconhecido.")
        if selected_insurer and selected_branch_group:
            raise ValueError("Selecione apenas um visual por vez.")
        return self._cached_query(start, end, entities, group, metric, selected_insurer, selected_branch_group)

    def _query(self, start, end, entities, group, metric, selected_insurer, selected_branch_group):
        selection = {}
        if selected_insurer:
            selection["selected_insurer"] = selected_insurer
        if selected_branch_group:
            selection["selected_branch_group"] = selected_branch_group
        with self.connection() as db:
            core = dashboard_core(db, start, end, list(entities), group, metric, **selection)
            analysis = get_analysis(
                db, start=start, end=end, insurers=list(entities), group=group, metric=metric, **selection
            )
        return {**core, **analysis}

    def analyze_uf(self, params):
        context = self.reference_filters(params)
        state = single_filter(params, "uf")
        insurer = single_filter(params, "selected_insurer")
        if state and state not in self.states:
            raise ValueError("UF desconhecida.")
        if insurer and insurer not in self.entities:
            raise ValueError("Seguradora do ranking desconhecida.")
        return self._cached_uf_query(*context, state, insurer)

    def _query_uf(self, start, end, entities, group, state, insurer):
        with self.connection() as db:
            return get_uf_analysis(
                db, start=start, end=end, insurers=entities, group=group,
                selected_uf=state, selected_insurer=insurer,
            )

    def analyze_simulation(self, params):
        context = self.reference_filters(params)
        reference_growth = self.scenario_integer(params, "reference_growth", 18, -30, 100)
        competitor_growth = self.scenario_integer(params, "competitor_growth", 0, -30, 100)
        goal = self.scenario_integer(params, "goal", -3, -5, 5)
        insurer = single_filter(params, "selected_insurer")
        if insurer and insurer not in self.entities:
            raise ValueError("Seguradora do ranking desconhecida.")
        return self._cached_simulation(*context, reference_growth, competitor_growth, goal, insurer)

    @staticmethod
    def scenario_integer(params, name, default, minimum, maximum):
        raw = single_filter(params, name, str(default))
        try:
            value = int(raw)
        except ValueError:
            raise ValueError(f"Parâmetro inteiro inválido: {name}.") from None
        if not minimum <= value <= maximum:
            raise ValueError(f"Parâmetro fora do intervalo: {name}.")
        return value

    def _query_simulation(self, start, end, entities, group, reference_growth, competitor_growth, goal, insurer):
        with self.connection() as db:
            return get_simulation(
                db, start=start, end=end, insurers=entities, group=group,
                reference_growth=reference_growth, competitor_growth=competitor_growth, goal=goal,
                selected_insurer=insurer,
            )

    def analyze_ma(self, params):
        context = self.reference_filters(params)
        company_a = single_filter(params, "company_a")
        company_b = single_filter(params, "company_b")
        state = single_filter(params, "uf")
        branch_group = single_filter(params, "selected_branch_group")
        if any(code and code not in self.entities for code in (company_a, company_b)):
            raise ValueError("Seguradora da operação desconhecida.")
        if state and state not in self.states:
            raise ValueError("UF desconhecida.")
        if branch_group and branch_group not in self.branch_groups:
            raise ValueError("Grupo de ramos desconhecido.")
        if state and branch_group:
            raise ValueError("Selecione apenas uma tabela por vez.")
        return self._cached_ma(*context, company_a, company_b, state, branch_group)

    def _query_ma(self, start, end, entities, group, company_a, company_b, state, branch_group):
        with self.connection() as db:
            return get_ma(
                db, start=start, end=end, insurers=entities, group=group,
                company_a=company_a, company_b=company_b,
                selected_uf=state, selected_branch_group=branch_group,
            )


def json_default(value):
    if isinstance(value, Decimal):
        # Preserve cents through the API; the UI converts numbers for formatting.
        return str(value)
    raise TypeError(f"Valor sem representação JSON: {type(value).__name__}")


def release_url(value):
    if not re.fullmatch(
        r"https://github\.com/[A-Za-z0-9-]+/[A-Za-z0-9_.-]+/releases/download/"
        r"[A-Za-z0-9_.%+-]+/[A-Za-z0-9_.%+-]+\.pbix",
        value,
    ):
        raise ValueError("SUSEP_PBIX_URL deve ser o link HTTPS de um anexo .pbix por tag do GitHub Releases.")
    return value


def json_response(status, payload):
    return Response(
        json.dumps(payload, ensure_ascii=False, default=json_default).encode("utf-8"),
        status=status,
        content_type="application/json; charset=utf-8",
        headers={"Cache-Control": "no-store"},
    )


def create_app(service, pbix_url=None):
    queries = {
        "/api/raio-x": service.analyze,
        "/api/visao-uf": service.analyze_uf,
        "/api/simulacoes": service.analyze_simulation,
        "/api/fusao-aquisicao": service.analyze_ma,
    }
    catalog = dict(service.catalog)
    if pbix_url:
        catalog["pbixUrl"] = release_url(pbix_url)
    dist = ROOT / "dist"

    @Request.application
    def app(request):
        if request.method not in {"GET", "HEAD"}:
            return Response(status=HTTPStatus.METHOD_NOT_ALLOWED, headers={"Allow": "GET, HEAD"})
        path = request.path.rstrip("/")
        if path == "/api/catalog":
            return json_response(HTTPStatus.OK, catalog)
        if path == "/healthz":
            return json_response(HTTPStatus.OK, {"status": "ok"})
        if path in queries:
            try:
                params = parse_qs(request.query_string.decode("latin-1"), keep_blank_values=True, max_num_fields=200)
                result = queries[path](params)
            except ValueError as error:
                return json_response(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            except duckdb.Error:
                LOGGER.exception("Falha na consulta %s", path)
                return json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Falha ao consultar os dados SUSEP."})
            return json_response(HTTPStatus.OK, result)
        if path == "/api" or path.startswith("/api/"):
            return json_response(HTTPStatus.NOT_FOUND, {"error": "Consulta não encontrada."})

        name = request.path[1:] or "index.html"
        asset = dist / name
        if asset.parent != dist or name.startswith(".") or asset.suffix not in {".html", ".css", ".js", ".json"}:
            raise NotFound()
        if asset.is_symlink():
            raise NotFound()
        return send_from_directory(dist, name, request.environ)

    return app


def main():
    parser = argparse.ArgumentParser(description="SUSEP | Market Share Intelligence — servidor web")
    parser.add_argument("--data-dir", help="Pasta com os Parquets de data/curated")
    parser.add_argument("--host", default=os.environ.get("SUSEP_HOST") or "127.0.0.1")
    parser.add_argument("--port", type=int, default=os.environ.get("PORT") or 8000)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("A porta deve estar entre 1 e 65535.")

    try:
        db = open_database(find_data_dir(args.data_dir))
    except FileNotFoundError as error:
        parser.exit(1, f"{error}\nInforme o caminho correto com --data-dir.\n")
    except (duckdb.Error, ValueError) as error:
        parser.exit(1, f"{error}\n")

    try:
        app = create_app(Service(db), os.environ.get("SUSEP_PBIX_URL"))
        logging.basicConfig(level=logging.INFO)
        serve(
            app, host=args.host, port=args.port, threads=8, connection_limit=64,
            channel_timeout=30, max_request_header_size=16_384, max_request_body_size=1_024,
        )
    except ValueError as error:
        parser.exit(1, f"{error}\n")
    except OSError as error:
        if error.errno != errno.EADDRINUSE and getattr(error, "winerror", None) != 10048:
            raise
        parser.exit(1, f"A porta {args.port} já está em uso. Encerre o servidor anterior com Ctrl+C ou escolha outra porta.\n")
    finally:
        db.close()


if __name__ == "__main__":
    main()
