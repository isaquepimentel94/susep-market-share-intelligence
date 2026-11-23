"""Checks for the local guide content and its TMDL extraction."""

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import unittest

from tools.build_guide import _entries


class GuideData(unittest.TestCase):
    def test_asset_matches_the_audited_content(self):
        path = Path(__file__).resolve().parents[1] / "dist" / "guide-data.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["defaults"], {
            "category": "Desempenho Técnico",
            "indicator": "Margem Técnica Parcial",
        })
        entries = payload["entries"]
        self.assertEqual([entry["order"] for entry in entries], list(range(1, 39)))
        self.assertEqual(Counter(entry["status"] for entry in entries), {
            "Implementado": 35,
            "Planejado": 3,
        })
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.assertEqual(
            sha256(canonical.encode("utf-8")).hexdigest(),
            "da68aa1e67068ae0c1037680380e2f91d1cf947199bd33ede75f1250d06e66ce",
        )

    def test_extraction_preserves_escaped_quotes_and_literal_whitespace(self):
        source = '''DATATABLE(
            "Ordem", INTEGER, "Categoria", STRING, "Indicador", STRING,
            "Definicao", STRING, "Calculo", STRING, "Interpretacao", STRING,
            "Fonte", STRING,
            { {1, "Dados", "A", "Texto ""citado"" com {chaves}, intacto",
                "A / B", "linha 1
linha 2", "Fonte"} }
        )'''
        self.assertEqual(_entries(source, inherited_status="Implementado"), [{
            "order": 1,
            "category": "Dados",
            "indicator": "A",
            "definition": 'Texto "citado" com {chaves}, intacto',
            "formula": "A / B",
            "interpretation": "linha 1\nlinha 2",
            "source": "Fonte",
            "status": "Implementado",
        }])


if __name__ == "__main__":
    unittest.main()
