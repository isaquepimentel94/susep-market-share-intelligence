"""Check that the deployable map declares the approved IBGE source and all UFs."""

import argparse
import json
import math
from pathlib import Path
import re


SOURCE_SHA256 = "5273fc6a3add9f3f18dbbcf4d844a03f9ed0c76a1fe779ce03cfff313488460c"
UF_CODES = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}
PROVENANCE = {
    "source": "IBGE",
    "dataset": "BR_UF_2023",
    "license": "CC-BY-4.0",
    "sourceSha256": SOURCE_SHA256,
}
DEFAULT_MAP = Path(__file__).resolve().parents[1] / "dist" / "uf-map.json"
NUMBER = r"\d+(?:\.\d+)?"
POINT = rf"{NUMBER},{NUMBER}"
SVG_PATH = re.compile(rf"(?:M{POINT}(?:L{POINT}){{2,}}Z)+")


def check_asset(asset):
    metadata = asset.get("metadata") if isinstance(asset, dict) else None
    if not isinstance(metadata, dict) or any(metadata.get(key) != value for key, value in PROVENANCE.items()):
        raise ValueError("Proveniência do mapa ausente ou divergente da malha BR_UF_2023 do IBGE com CC BY 4.0.")

    view_box = asset.get("viewBox")
    extent = re.fullmatch(rf"0 0 ({NUMBER}) ({NUMBER})", view_box) if isinstance(view_box, str) else None
    if not extent or not all(math.isfinite(value) and value > 0 for value in map(float, extent.groups())):
        raise ValueError("Dimensões SVG da malha inválidas.")

    paths = asset.get("paths")
    if not isinstance(paths, list) or len(paths) != len(UF_CODES):
        raise ValueError("O mapa deve conter exatamente 27 registros de UF.")
    seen = set()
    for path in paths:
        if not isinstance(path, dict):
            raise ValueError("Registro de UF inválido.")
        code, uf, geometry = path.get("code"), path.get("uf"), path.get("d")
        if not isinstance(code, str) or code in seen or code not in UF_CODES or UF_CODES[code] != uf:
            raise ValueError("Código de UF ausente, repetido ou incompatível com a sigla oficial.")
        if not isinstance(geometry, str) or not SVG_PATH.fullmatch(geometry):
            raise ValueError(f"Geometria ausente ou inválida para {uf}.")
        seen.add(code)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asset", nargs="?", type=Path, default=DEFAULT_MAP)
    args = parser.parse_args()
    try:
        check_asset(json.loads(args.asset.read_text(encoding="utf-8")))
    except OSError:
        parser.exit(1, "Arquivo de geometria indisponível. Consulte CHECKLIST_DEPLOY.md.\n")
    except json.JSONDecodeError:
        parser.exit(1, "Arquivo de geometria com JSON inválido. Consulte CHECKLIST_DEPLOY.md.\n")
    except ValueError as error:
        parser.exit(1, f"{error} Consulte CHECKLIST_DEPLOY.md.\n")
    print("Malha BR_UF_2023 do IBGE validada para 27 UFs.")


if __name__ == "__main__":
    main()
