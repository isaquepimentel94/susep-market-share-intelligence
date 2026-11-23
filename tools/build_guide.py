"""Extract the indicator guide from the Power BI TMDL and PBIX."""

import argparse
import json
from pathlib import Path
import re
from zipfile import ZipFile


_STRING = r'"(?:[^"]|"")*"'
_ROW = re.compile(
    rf"\{{\s*(\d+)\s*,\s*({_STRING}(?:\s*,\s*{_STRING})*)\s*\}}"
)
_ENTRY_FIELDS = ("category", "indicator", "definition", "formula", "interpretation", "source", "status")
_FALLBACK_FIELDS = {"Definicao", "Calculo", "Interpretacao", "Fonte"}
_GUIDE_PAGE = "Report/definition/pages/7aaac082eac32520176c/visuals"
_GUIDE_SLICERS = {
    "category": "c590c86a970c1d898a91",
    "indicator": "57a4a11b3000052ea7cc",
}


def _dax_string(literal):
    return literal[1:-1].replace('""', '"')


def _entries(source, *, inherited_status=None):
    datatable = re.split(r"\bDATATABLE\s*\(", source, maxsplit=1)[1]
    entries = []
    for order, literals in _ROW.findall(datatable):
        values = [_dax_string(literal) for literal in re.findall(_STRING, literals)]
        if inherited_status is not None:
            values.append(inherited_status)
        if len(values) != len(_ENTRY_FIELDS):
            raise ValueError(f"Quantidade de campos inesperada na ordem {order}.")
        entries.append({"order": int(order), **dict(zip(_ENTRY_FIELDS, values))})
    if not entries:
        raise ValueError("Nenhuma entrada encontrada em DATATABLE.")
    return entries


def _fallback(source):
    matches = re.findall(
        rf"SELECTEDVALUE\s*\(\s*Guia_Conteudo\[(\w+)\]\s*,\s*({_STRING})\s*\)",
        source,
    )
    values = {_dax_string(value) for field, value in matches if field in _FALLBACK_FIELDS}
    if {field for field, _ in matches} != _FALLBACK_FIELDS or len(values) != 1:
        raise ValueError("Os quatro cartões devem declarar o mesmo texto alternativo.")
    return values.pop()


def _defaults(pbix):
    defaults = {}
    with ZipFile(pbix) as archive:
        for key, visual_id in _GUIDE_SLICERS.items():
            visual = json.loads(archive.read(f"{_GUIDE_PAGE}/{visual_id}/visual.json"))
            general = visual["visual"]["objects"]["general"][0]["properties"]
            where = general["filter"]["filter"]["Where"]
            values = where[0]["Condition"]["In"]["Values"]
            literal = values[0][0]["Literal"]["Value"]
            if len(values) != 1 or len(values[0]) != 1 or not literal.startswith("'") or not literal.endswith("'"):
                raise ValueError(f"Seleção inicial inválida em {key}.")
            defaults[key] = literal[1:-1].replace("''", "'")
    return defaults


def build_guide(tables_dir, pbix):
    indicators = (tables_dir / "Guia_Indicadores.tmdl").read_text(encoding="utf-8-sig")
    content = (tables_dir / "Guia_Conteudo.tmdl").read_text(encoding="utf-8-sig")
    status = re.search(rf'"Status"\s*,\s*({_STRING})', content)
    if status is None:
        raise ValueError("Status das entradas originais ausente em Guia_Conteudo.")
    entries = _entries(indicators, inherited_status=_dax_string(status[1])) + _entries(content)
    entries.sort(key=lambda row: row["order"])
    if [row["order"] for row in entries] != list(range(1, len(entries) + 1)):
        raise ValueError("A ordem das entradas deve ser consecutiva e única.")
    if len({row["indicator"] for row in entries}) != len(entries):
        raise ValueError("Os indicadores devem ter nomes únicos.")
    defaults = _defaults(pbix)
    if not any(all(row[key] == value for key, value in defaults.items()) for row in entries):
        raise ValueError("A seleção inicial deve corresponder a uma entrada.")
    return {"fallback": _fallback(indicators), "defaults": defaults, "entries": entries}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tables_dir", type=Path, help="Pasta definition/tables do modelo TMDL")
    parser.add_argument("pbix", type=Path, help="PBIX que contém a definição do relatório")
    parser.add_argument(
        "--output", type=Path, default=Path(__file__).resolve().parents[1] / "dist" / "guide-data.json"
    )
    args = parser.parse_args()
    payload = build_guide(args.tables_dir, args.pbix)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
