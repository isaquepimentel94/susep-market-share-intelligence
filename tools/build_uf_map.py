"""Build the public SVG map from the official BR_UF_2023 shapefile archive."""

import argparse
from hashlib import file_digest
from io import BytesIO
import json
import math
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import shapefile
import shapely
from shapely.geometry import MultiPolygon, shape

from check_uf_map import SOURCE_SHA256, UF_CODES


SOURCE_URL = (
    "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/"
    "malhas_municipais/municipio_2023/Brasil/BR_UF_2023.zip"
)
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/deed.pt-br"
TERMS_URL = "https://www.ibge.gov.br/biblioteca/visualizacao/livros/liv102152.pdf#page=8"
CENTRAL_MERIDIAN = -54
PARALLELS = (-2, -22)
RADIUS_KM = 6371.007
SIMPLIFY_KM = 4
MIN_PART_KM2 = 12
MAP_SIZE = 640
PADDING = 8


def project(coordinates):
    """Apply the existing map's spherical Albers convention in km."""
    longitude, latitude = coordinates.T
    first, second = map(math.radians, PARALLELS)
    n = (math.sin(first) + math.sin(second)) / 2
    coefficient = math.cos(first) ** 2 + 2 * n * math.sin(first)
    radius = RADIUS_KM / n * np.sqrt(coefficient - 2 * n * np.sin(np.deg2rad(latitude)))
    angle = n * np.deg2rad(longitude - CENTRAL_MERIDIAN)
    return np.column_stack((radius * np.sin(angle), radius * np.cos(angle)))


def read_shapes(archive):
    with archive.open("rb") as source:
        if file_digest(source, "sha256").hexdigest() != SOURCE_SHA256:
            raise ValueError("SHA-256 diferente do ZIP oficial BR_UF_2023 conferido.")
    with ZipFile(archive) as bundle:
        files = {ext: BytesIO(bundle.read(f"BR_UF_2023.{ext}")) for ext in ("shp", "shx", "dbf")}
    geometries = {}
    with shapefile.Reader(**files, encoding="utf-8") as reader:
        for row in reader.iterShapeRecords(fields=["CD_UF", "SIGLA_UF"]):
            code, uf = row.record
            if UF_CODES.get(code) != uf or code in geometries:
                raise ValueError(f"Código ou sigla incompatível no shapefile: {code} {uf}")
            geometries[code] = shape(row.shape.__geo_interface__)
    if geometries.keys() != UF_CODES.keys():
        raise ValueError("A malha deve conter os 27 códigos oficiais de UF.")
    return geometries


def retain_visible_parts(geometry):
    # A detached part below this area covers less than one pixel at the 640-unit reference size.
    parts = [polygon for polygon in shapely.get_parts(geometry) if polygon.area >= MIN_PART_KM2]
    if not parts:
        raise ValueError("Nenhuma parte desenhável para a UF.")
    return parts[0] if len(parts) == 1 else MultiPolygon(parts)


def make_asset(archive):
    official = read_shapes(archive)
    codes = sorted(official)
    projected = shapely.transform([official[code] for code in codes], project)
    visible = [retain_visible_parts(geometry) for geometry in projected]
    if not shapely.coverage_is_valid(visible):
        raise ValueError("A cobertura reprojetada não contém fronteiras compartilhadas válidas.")
    simplified = shapely.coverage_simplify(visible, SIMPLIFY_KM)
    if not all(shapely.is_valid(simplified)) or not shapely.coverage_is_valid(simplified):
        raise ValueError("A simplificação alterou a topologia da cobertura.")

    x0, y0, x1, y1 = shapely.total_bounds(simplified)
    scale = MAP_SIZE / max(x1 - x0, y1 - y0)
    width, height = (x1 - x0) * scale + 2 * PADDING, (y1 - y0) * scale + 2 * PADDING

    def ring_path(ring):
        points = "L".join(
            f"{(x - x0) * scale + PADDING:.2f},{(y - y0) * scale + PADDING:.2f}"
            for x, y in list(ring.coords)[:-1]
        )
        return f"M{points}Z"

    paths = []
    for code, geometry in zip(codes, simplified, strict=True):
        rings = (
            ring for polygon in shapely.get_parts(geometry)
            for ring in (polygon.exterior, *polygon.interiors)
        )
        paths.append({"uf": UF_CODES[code], "code": code, "d": "".join(map(ring_path, rings))})

    return {
        "viewBox": f"0 0 {width:.2f} {height:.2f}",
        "paths": paths,
        "metadata": {
            "source": "IBGE",
            "dataset": "BR_UF_2023",
            "edition": 2023,
            "sourceUrl": SOURCE_URL,
            "sourceSha256": SOURCE_SHA256,
            "sourceCrs": "EPSG:4674",
            "license": "CC-BY-4.0",
            "licenseUrl": LICENSE_URL,
            "licenseTermsUrl": TERMS_URL,
            "transformations": {
                "projection": "Albers equal-area (spherical)",
                "centralMeridian": CENTRAL_MERIDIAN,
                "standardParallels": list(PARALLELS),
                "simplification": "Visvalingam–Whyatt (shared polygon coverage)",
                "simplificationToleranceKm": SIMPLIFY_KM,
                "minimumPolygonPartAreaKm2": MIN_PART_KM2,
                "svgCoordinateDecimals": 2,
            },
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="ZIP oficial BR_UF_2023")
    parser.add_argument(
        "--output", type=Path, default=Path(__file__).resolve().parents[1] / "dist" / "uf-map.json"
    )
    args = parser.parse_args()
    asset = make_asset(args.archive)
    args.output.write_text(
        json.dumps(asset, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    main()
