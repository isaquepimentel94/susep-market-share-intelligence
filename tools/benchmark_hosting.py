"""Measure isolated loopback Waitress profiles. Windows requires psutil in
the benchmark interpreter; Linux reads process counters from /proc.

Use --python for the server interpreter when its dependencies are in a venv.
The final stdout document is JSON; progress is sent to stderr.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from hashlib import sha256
from http.client import HTTPConnection, HTTPException
from itertools import islice, product
import json
import os
from pathlib import Path
import socket
from statistics import median
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Barrier
from time import perf_counter, sleep
from urllib.parse import urlencode


APP_DIR = Path(__file__).resolve().parents[1]
RECENT_CASES = (
    ("202601", "202609"), ("202601", "202608"), ("202602", "202609"),
    ("202501", "202509"), ("202511", "202603"), ("202401", "202512"),
    ("202201", "202609"), ("201901", "202609"),
)
REFERENCES = ("05631", "05886", "05177", "06238")


@dataclass(frozen=True)
class Profile:
    name: str
    memory_limit: str | None
    threads: int
    slots: int


@dataclass
class Response:
    status: int
    elapsed_ms: float
    body: bytes

    @property
    def digest(self):
        return sha256(self.body).hexdigest()


def parse_profile(value):
    try:
        name, memory, threads, slots = value.split(":")
        threads, slots = int(threads), int(slots)
        if not name or not memory or min(threads, slots) < 1:
            raise ValueError
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "Use NOME:MEMÓRIA:THREADS:SLOTS, como principal:192MiB:1:1."
        ) from error
    return Profile(name, None if memory == "default" else memory, threads, slots)


def loopback_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def get(port, route, params, timeout):
    client = HTTPConnection("127.0.0.1", port, timeout=timeout)
    if params:
        route += "?" + urlencode(params, doseq=True)
    started = perf_counter()
    try:
        client.request("GET", route)
        reply = client.getresponse()
        body = reply.read()
        return Response(reply.status, (perf_counter() - started) * 1000, body)
    except (OSError, HTTPException) as error:
        return Response(0, (perf_counter() - started) * 1000, str(error).encode("utf-8"))
    finally:
        client.close()


def wait_ready(server, port, timeout):
    deadline = perf_counter() + timeout
    while perf_counter() < deadline and server.poll() is None:
        if get(port, "/healthz", {}, .4).status == 200:
            return
        sleep(.05)
    raise RuntimeError("Waitress não respondeu em /healthz no prazo de inicialização.")


def process_counters(pid):
    mib = 1024 * 1024
    if sys.platform == "win32":
        import psutil

        launcher = psutil.Process(pid)
        # Windows venv python.exe can launch the real interpreter as a child.
        processes = [launcher, *launcher.children(recursive=True)]
        memory = [process.memory_info() for process in processes]
        cpu = [process.cpu_times() for process in processes]
        return {
            "processes": len(processes),
            "rss_mib": round(sum(item.rss for item in memory) / mib, 2),
            "rss_peak_mib": round(max(item.peak_wset for item in memory) / mib, 2),
            "rss_peak_tree_upper_bound_mib": round(sum(item.peak_wset for item in memory) / mib, 2),
            "private_commit_mib": round(sum(item.private for item in memory) / mib, 2),
            "private_commit_peak_mib": round(max(item.peak_pagefile for item in memory) / mib, 2),
            "private_commit_peak_tree_upper_bound_mib": round(sum(item.peak_pagefile for item in memory) / mib, 2),
            "cpu_s": round(sum(item.user + item.system for item in cpu), 3),
        }
    proc = Path("/proc") / str(pid)
    status = dict(line.split(":", 1) for line in (proc / "status").read_text().splitlines())
    stat = (proc / "stat").read_text().rsplit(")", 1)[1].split()
    return {
        "rss_mib": round(int(status["VmRSS"].split()[0]) / 1024, 2),
        "rss_peak_mib": round(int(status["VmHWM"].split()[0]) / 1024, 2),
        "cpu_s": round((int(stat[11]) + int(stat[12])) / os.sysconf("SC_CLK_TCK"), 3),
    }


def cache_requests(entries):
    for (start, end), insurer in islice(product(RECENT_CASES, REFERENCES), entries):
        common = {"entity": insurer, "start": start, "end": end}
        yield "raio_x", {**common, "metric": "margem"}
        yield "uf", common
        yield "sim", {**common, "reference_growth": 18, "competitor_growth": 0, "goal": -3}
        yield "ma", {**common, "company_a": "05177", "company_b": "06238"}


def stats(results):
    elapsed = [item.elapsed_ms for item in results]
    signatures = [(item.status, item.digest) for item in results]
    status_codes = sorted({item.status for item in results})
    return {
        "requests": len(results),
        "http": {str(code): sum(item.status == code for item in results) for code in status_codes},
        "ms_min": round(min(elapsed), 2),
        "ms_median": round(median(elapsed), 2),
        "ms_max": round(max(elapsed), 2),
        "bytes_total": sum(len(item.body) for item in results),
        "sha256": sha256(json.dumps(signatures).encode()).hexdigest(),
    }


def stress_requests(port, catalog, count, timeout):
    entities = sorted(item["code"] for item in catalog["entities"])
    months = catalog["months"]
    context = {"entity": entities, "start": months[0]["code"], "end": months[-1]["code"]}
    pairs = (("05177", "06238"), ("05886", "06190"), ("06190", "06238"),
             ("05177", "05886"), ("06238", "05886"), ("06190", "05177"))
    results = []
    pair_times = []
    with ThreadPoolExecutor(max_workers=2) as workers:
        for index in range(count):
            gate = Barrier(2)

            def request(pair):
                gate.wait()
                return get(
                    port, "/api/fusao-aquisicao",
                    {**context, "company_a": pair[0], "company_b": pair[1]}, timeout,
                )

            started = perf_counter()
            results.extend(workers.map(request, pairs[index * 2:index * 2 + 2]))
            pair_times.append(round((perf_counter() - started) * 1000, 2))
    return results, {
        "entities": len(entities), "months": len(months), "requests_per_pair": 2,
        "pair_ms": pair_times,
    }


def stop_server(server):
    if server.poll() is None:
        if sys.platform == "win32":
            import psutil

            try:
                children = psutil.Process(server.pid).children(recursive=True)
            except psutil.NoSuchProcess:
                children = []
            for child in reversed(children):
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            _, alive = psutil.wait_procs(children, timeout=3)
            for child in alive:
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
            psutil.wait_procs(alive, timeout=3)
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()


def benchmark(args, profile):
    routes = {"raio_x": "/api/raio-x", "uf": "/api/visao-uf", "sim": "/api/simulacoes", "ma": "/api/fusao-aquisicao"}
    requests = list(cache_requests(args.cache_entries))
    stages = {}
    snapshots = {}
    env = os.environ.copy()
    env.update(SUSEP_DUCKDB_THREADS=str(profile.threads), SUSEP_QUERY_SLOTS=str(profile.slots))
    env.pop("SUSEP_PBIX_URL", None)
    if profile.memory_limit is None:
        env.pop("SUSEP_DUCKDB_MEMORY_LIMIT", None)
    else:
        env["SUSEP_DUCKDB_MEMORY_LIMIT"] = profile.memory_limit
    with TemporaryDirectory(prefix="susep-benchmark-") as scratch:
        temp = Path(scratch)
        env["SUSEP_DUCKDB_TEMP_DIR"] = str(temp / "spill")
        port = loopback_port()
        command = [str(args.python), "-B", str(APP_DIR / "server.py"), "--host", "127.0.0.1",
                   "--port", str(port), "--data-dir", str(args.data_dir)]
        with (temp / "waitress.log").open("w+b") as log:
            started = perf_counter()
            server = subprocess.Popen(command, cwd=temp, env=env, stdout=log, stderr=subprocess.STDOUT)
            try:
                wait_ready(server, port, args.timeout)
                boot_ms = round((perf_counter() - started) * 1000, 2)
                startup = get(port, "/api/catalog", {}, args.timeout)
                if startup.status != 200:
                    raise RuntimeError(f"Catálogo retornou HTTP {startup.status}.")
                catalog = json.loads(startup.body)
                snapshots["boot"] = process_counters(server.pid)
                for phase in ("fill", "replay"):
                    print(f"{profile.name}: {phase} ({len(requests)} GETs)", file=sys.stderr, flush=True)
                    results = {name: [] for name in routes}
                    for name, params in requests:
                        results[name].append(get(port, routes[name], params, args.timeout))
                    stages[phase] = {name: stats(rows) for name, rows in results.items()}
                    snapshots[phase] = process_counters(server.pid)
                print(f"{profile.name}: {args.pairs} pares de M&A", file=sys.stderr, flush=True)
                results, stress = stress_requests(port, catalog, args.pairs, args.timeout)
                stages["stress"] = stats(results)
                snapshots["stress"] = process_counters(server.pid)
            except (RuntimeError, OSError) as error:
                stop_server(server)
                log.seek(0)
                detail = log.read().decode("utf-8", errors="replace").strip()
                raise RuntimeError(f"{profile.name}: {error}\n{detail}") from error
            finally:
                stop_server(server)
            summaries = [row for phase in ("fill", "replay") for row in stages[phase].values()]
            summaries.append(stages["stress"])
            http_ok = all(row["http"] == {"200": row["requests"]} for row in summaries)
            diagnostics = None
            if not http_ok:
                log.seek(0)
                diagnostics = log.read().decode("utf-8", errors="replace").splitlines()[-24:]
    return {
        "profile": profile.__dict__, "boot_ms": boot_ms, "catalog_sha256": startup.digest,
        "stages": stages, "stress": stress, "process": snapshots, "http_ok": http_ok,
        "server_diagnostics": diagnostics,
        "replay_matches_fill": all(
            stages["replay"][name]["sha256"] == stages["fill"][name]["sha256"] for name in routes
        ),
    }


def compare(baseline, candidate):
    return {
        "catalog": baseline["catalog_sha256"] == candidate["catalog_sha256"],
        "fill": {
            name: row["sha256"] == candidate["stages"]["fill"][name]["sha256"]
            for name, row in baseline["stages"]["fill"].items()
        },
        "concurrent_ma": baseline["stages"]["stress"]["sha256"] == candidate["stages"]["stress"]["sha256"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True, help="Pasta dos Parquets canônicos.")
    parser.add_argument("--python", type=Path, default=Path(sys.executable), help="Interpretador com as dependências do app.")
    parser.add_argument("--profile", action="append", type=parse_profile, help="NOME:MEMÓRIA:THREADS:SLOTS. Pode ser repetido.")
    parser.add_argument("--cache-entries", type=int, choices=range(1, 33), default=32, metavar="1..32")
    parser.add_argument("--pairs", type=int, choices=range(1, 4), default=3, metavar="1..3")
    parser.add_argument("--timeout", type=float, default=30, help="Prazo em segundos por GET e para o boot.")
    args = parser.parse_args()
    args.python = args.python.resolve()
    args.data_dir = args.data_dir.resolve()
    if args.timeout <= 0:
        parser.error("--timeout deve ser positivo.")
    if sys.platform == "win32":
        try:
            import psutil  # noqa: F401
        except ImportError:
            parser.error("Use um Python com psutil para executar o benchmark no Windows.")
    elif not Path("/proc/self/status").is_file():
        parser.error("O benchmark requer Windows ou Linux com /proc.")
    profiles = args.profile or [Profile("baseline", None, 4, 2), Profile("principal", "192MiB", 1, 1)]
    if len({profile.name for profile in profiles}) != len(profiles):
        parser.error("Dê nomes distintos aos perfis.")
    results = []
    for profile in profiles:
        print(f"{profile.name}: inicializando Waitress", file=sys.stderr, flush=True)
        results.append(benchmark(args, profile))
    print(json.dumps({
        "platform": sys.platform,
        "cache_entries_per_endpoint": args.cache_entries,
        "profiles": results,
        "comparison_to_first": {item["profile"]["name"]: compare(results[0], item) for item in results[1:]},
    }, indent=2))
    if not all(item["http_ok"] and item["replay_matches_fill"] for item in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
