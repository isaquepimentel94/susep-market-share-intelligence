"""Package and provision the versioned SUSEP snapshot outside the web root."""

import argparse
import gzip
import hashlib
from http.client import HTTPException
import os
from pathlib import Path
import re
import shutil
import tarfile
import tempfile
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, build_opener
from zlib import error as CompressionError


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "deploy" / "parquets-201901-202609.sha256"
DATA_DIR = ROOT / "data" / "curated"
MAX_BYTES = 64 * 1024 * 1024
BLOCK_BYTES = 1024 * 1024


class SnapshotError(Exception):
    pass


class LimitedReader:
    """Bound the expanded tar stream, including headers and padding."""

    def __init__(self, stream):
        self.stream = stream
        self.remaining = MAX_BYTES

    def read(self, size):
        data = self.stream.read(min(size, self.remaining + 1))
        self.remaining -= len(data)
        if self.remaining < 0:
            raise SnapshotError("Arquivo expandido ultrapassa 64 MiB.")
        return data


def load_manifest():
    checksums = {}
    for line in MANIFEST.read_text(encoding="ascii").splitlines():
        record = re.fullmatch(r"([0-9a-f]{64})  ([a-z0-9_]+\.parquet)", line)
        if not record or record[2] in checksums:
            raise SnapshotError("O manifesto contém uma entrada inválida ou repetida.")
        checksums[record[2]] = record[1]
    if len(checksums) != 9:
        raise SnapshotError("O manifesto deve conter os nove Parquets.")
    return checksums


def verify_directory(source, checksums):
    total = 0
    for name, expected in checksums.items():
        path = source / name
        if path.is_symlink() or not path.is_file():
            raise SnapshotError(f"Parquet regular ausente em {source}: {name}.")
        total += path.stat().st_size
        if total > MAX_BYTES:
            raise SnapshotError("Os Parquets ultrapassam 64 MiB.")
        with path.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != expected:
                raise SnapshotError(f"SHA-256 divergente para {name}.")


def verify_archive(archive, checksums, staging=None):
    if archive.stat().st_size > MAX_BYTES:
        raise SnapshotError("Arquivo compactado ultrapassa 64 MiB.")
    verified = set()
    with gzip.open(archive, "rb") as compressed:
        with tarfile.open(fileobj=LimitedReader(compressed), mode="r|", ignore_zeros=True) as tar:
            for member in tar:
                name = member.name
                if (
                    name not in checksums
                    or name in verified
                    or member.type not in {tarfile.REGTYPE, tarfile.AREGTYPE}
                    or member.issparse()
                    or not 0 < member.size <= MAX_BYTES
                ):
                    raise SnapshotError("O pacote contém uma entrada inesperada, repetida ou não regular.")
                with tar.extractfile(member) as source:
                    if staging is None:
                        actual = hashlib.file_digest(source, "sha256").hexdigest()
                    else:
                        with (staging / name).open("xb") as target:
                            digest = hashlib.sha256()
                            while block := source.read(BLOCK_BYTES):
                                target.write(block)
                                digest.update(block)
                            actual = digest.hexdigest()
                if actual != checksums[name]:
                    raise SnapshotError(f"SHA-256 divergente para {name}.")
                verified.add(name)
    if verified != checksums.keys():
        raise SnapshotError("O pacote não contém todos os arquivos do manifesto.")


def outside_web_root(path):
    resolved = path.resolve()
    public_dir = ROOT / "dist"
    if Path(os.path.abspath(path)).is_relative_to(public_dir) or resolved.is_relative_to(public_dir.resolve()):
        raise SnapshotError("Escolha um caminho fora da pasta pública dist.")
    return resolved


def pack_snapshot(source, archive, checksums):
    archive = outside_web_root(archive)
    if archive.exists():
        raise SnapshotError("Já existe um arquivo no caminho do pacote. Escolha outro nome.")
    verify_directory(source, checksums)
    archive.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".snapshot-", dir=archive.parent) as work:
        staged = Path(work) / "snapshot.tar.gz"
        with staged.open("xb") as raw:
            os.chmod(staged, 0o600)
            with gzip.GzipFile(filename="", mode="wb", compresslevel=1, fileobj=raw, mtime=0) as compressed:
                with tarfile.open(fileobj=compressed, mode="w", format=tarfile.USTAR_FORMAT) as tar:
                    for name in checksums:
                        path = source / name
                        info = tarfile.TarInfo(name)
                        info.size = path.stat().st_size
                        with path.open("rb") as stream:
                            tar.addfile(info, stream)
        verify_archive(staged, checksums)
        staged.rename(archive)


def valid_https_url(value):
    try:
        parsed = urlsplit(value)
        return parsed.scheme == "https" and bool(parsed.hostname) and parsed.username is None and not parsed.fragment
    except ValueError:
        return False


class HttpsRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, reason, headers, new_url):
        if not valid_https_url(new_url):
            raise SnapshotError("Redirecionamento para destino sem HTTPS recusado.")
        return super().redirect_request(request, response, code, reason, headers, new_url)


def download_snapshot(destination):
    url = os.environ.get("SUSEP_PARQUETS_ARTIFACT_URL", "")
    if not valid_https_url(url):
        raise SnapshotError("Configure SUSEP_PARQUETS_ARTIFACT_URL com uma URL HTTPS privada válida.")
    try:
        with build_opener(HttpsRedirects()).open(url, timeout=30) as source, destination.open("xb") as target:
            total = 0
            while block := source.read(BLOCK_BYTES):
                total += len(block)
                if total > MAX_BYTES:
                    raise SnapshotError("O download ultrapassa 64 MiB.")
                target.write(block)
    except HTTPError as error:
        error.close()
        raise SnapshotError(f"O armazenamento respondeu HTTP {error.code}. Verifique a validade da URL privada.") from None
    except (HTTPException, OSError, ValueError):
        raise SnapshotError("Falha ao baixar o pacote privado. Confira a conectividade e a URL.") from None


def install_snapshot(archive, target, checksums):
    target = outside_web_root(target)
    if target.exists():
        if not target.is_dir() or {path.name for path in target.iterdir()} != checksums.keys():
            raise SnapshotError("O destino existente deve conter exatamente os arquivos do manifesto.")
        verify_directory(target, checksums)
        if archive is not None:
            verify_archive(archive, checksums)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".snapshot-", dir=target.parent) as work:
        staging = Path(work) / "curated"
        staging.mkdir()
        if archive is None:
            archive = Path(work) / "snapshot.tar.gz"
            download_snapshot(archive)
        verify_archive(archive, checksums, staging)
        staging.rename(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    pack = commands.add_parser("pack")
    pack.add_argument("--source", type=Path, required=True)
    pack.add_argument("--archive", type=Path, required=True)
    verify = commands.add_parser("verify")
    inputs = verify.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--source", type=Path)
    inputs.add_argument("--archive", type=Path)
    install = commands.add_parser("install")
    install.add_argument("--archive", type=Path, help="Sem este argumento, usa a URL privada do ambiente.")
    install.add_argument("--target", type=Path, default=DATA_DIR)
    args = parser.parse_args()

    try:
        checksums = load_manifest()
        if args.command == "pack":
            pack_snapshot(args.source, args.archive, checksums)
        elif args.command == "install":
            install_snapshot(args.archive, args.target, checksums)
        elif args.source is not None:
            verify_directory(args.source, checksums)
        else:
            verify_archive(args.archive, checksums)
    except SnapshotError as error:
        parser.exit(1, f"{error}\n")
    except (CompressionError, EOFError, OSError, tarfile.TarError):
        parser.exit(1, "Falha ao ler, validar ou gravar o snapshot. Confira o arquivo e as permissões.\n")
    print("Nove Parquets verificados pelo manifesto SHA-256.")


if __name__ == "__main__":
    main()
