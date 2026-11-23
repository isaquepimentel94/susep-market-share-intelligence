"""Focused checks for the private Parquet artifact."""

from hashlib import sha256
from io import BytesIO
from pathlib import Path
import tarfile
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from server import TABLES
from tools.snapshot import (
    ROOT, SnapshotError, install_snapshot, load_manifest, pack_snapshot, verify_archive,
)


class SnapshotProvisioning(unittest.TestCase):
    def setUp(self):
        workspace = TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.root = Path(workspace.name)
        self.content = b"PAR1"
        self.name = "example.parquet"
        self.checksums = {self.name: sha256(self.content).hexdigest()}
        self.archive = self.root / "snapshot.tar.gz"
        self.target = self.root / "curated"

    def write_archive(self, entries):
        with tarfile.open(self.archive, "w:gz") as tar:
            for name, content, entry_type in entries:
                member = tarfile.TarInfo(name)
                member.size = len(content)
                member.type = entry_type
                tar.addfile(member, BytesIO(content))

    def test_runtime_manifest_and_reproducible_offline_install(self):
        self.assertEqual(set(load_manifest()), {f"{name}.parquet" for name in TABLES})
        source = self.root / "source"
        source.mkdir()
        (source / self.name).write_bytes(self.content)
        (source / "intermediate.parquet").write_bytes(b"excluded")
        copy = self.root / "snapshot-copy.tar.gz"
        pack_snapshot(source, self.archive, self.checksums)
        pack_snapshot(source, copy, self.checksums)
        self.assertEqual(self.archive.read_bytes(), copy.read_bytes())
        install_snapshot(self.archive, self.target, self.checksums)
        install_snapshot(self.archive, self.target, self.checksums)
        self.assertEqual([p.name for p in self.target.iterdir()], [self.name])
        self.assertEqual((self.target / self.name).read_bytes(), self.content)
        extra = self.target / "intermediate.parquet"
        extra.write_bytes(b"excluded")
        with self.assertRaisesRegex(SnapshotError, "destino existente"):
            install_snapshot(self.archive, self.target, self.checksums)
        self.assertTrue(extra.is_file())

    def test_rejects_traversal_symlinks_and_duplicate_members(self):
        regular = (self.name, self.content, tarfile.REGTYPE)
        for entries in (
            [regular, ("../outside.parquet", self.content, tarfile.REGTYPE)],
            [(self.name, b"", tarfile.SYMTYPE)],
            [regular, regular],
        ):
            with self.subTest(entries=entries):
                self.write_archive(entries)
                with self.assertRaisesRegex(SnapshotError, "entrada inesperada"):
                    install_snapshot(self.archive, self.target, self.checksums)
                self.assertFalse(self.target.exists())

    def test_rejects_bad_checksum_public_path_and_insecure_artifact(self):
        self.write_archive([(self.name, b"mismatched", tarfile.REGTYPE)])
        with self.assertRaisesRegex(SnapshotError, "SHA-256 divergente"):
            verify_archive(self.archive, self.checksums)
        with self.assertRaisesRegex(SnapshotError, "pasta pública"):
            install_snapshot(self.archive, ROOT / "dist" / "curated", self.checksums)
        with patch.dict("os.environ", {"SUSEP_PARQUETS_ARTIFACT_URL": "http://localhost/dummy?token=SENSITIVE"}):
            with self.assertRaises(SnapshotError) as refused:
                install_snapshot(None, self.target, self.checksums)
        self.assertNotIn("SENSITIVE", str(refused.exception))
        self.assertFalse(self.target.exists())

    def test_build_can_install_from_https_and_sanitizes_download_errors(self):
        self.write_archive([(self.name, self.content, tarfile.REGTYPE)])
        url = "https://localhost/dummy?token=SENSITIVE"
        with (
            patch.dict("os.environ", {"SUSEP_PARQUETS_ARTIFACT_URL": url}),
            patch("tools.snapshot.build_opener") as opener,
        ):
            fetch = opener.return_value.open
            fetch.return_value = BytesIO(self.archive.read_bytes())
            install_snapshot(None, self.target, self.checksums)
            fetch.assert_called_once_with(url, timeout=30)
            self.assertEqual((self.target / self.name).read_bytes(), self.content)

            denied_body = BytesIO()
            fetch.side_effect = HTTPError(url, 403, "denied", {}, denied_body)
            with self.assertRaisesRegex(SnapshotError, "HTTP 403") as refused:
                install_snapshot(None, self.root / "denied", self.checksums)
            self.assertTrue(denied_body.closed)
        self.assertNotIn("SENSITIVE", str(refused.exception))
        self.assertFalse((self.root / "denied").exists())


if __name__ == "__main__":
    unittest.main()
