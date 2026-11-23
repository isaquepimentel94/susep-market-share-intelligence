"""Measures from the Power BI Fusão e Aquisição page."""

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP

from core import _divide, _reference_label


_CENT = Decimal("0.01")
_ZERO = Decimal(0)
_COLLECTION_SQL = """
WITH by_location AS MATERIALIZED (
    SELECT uf, gracodigo, ramo, coenti,
           SUM(premio_direto) AS premium,
           SUM(premio_direto) FILTER (
               WHERE CASE WHEN len($insurers::VARCHAR[]) > 0
                          THEN list_contains($insurers::VARCHAR[], coenti)
                          ELSE cogrupo_historico = $group_code
                     END
           ) AS reference_premium
    FROM fato_premios_uf
    WHERE damesano BETWEEN $start AND $end
    GROUP BY uf, gracodigo, ramo, coenti
),
scoped AS MATERIALIZED (
    SELECT COALESCE(uf, '') AS uf, COALESCE(gracodigo, '') AS gracodigo, ramo, coenti,
           SUM(premium) AS premium, SUM(reference_premium) AS reference_premium
    FROM by_location
    GROUP BY GROUPING SETS ((ramo, coenti), (uf, ramo, coenti), (gracodigo, ramo, coenti))
    UNION ALL
    SELECT uf, gracodigo, ramo, coenti, premium, reference_premium
    FROM by_location
    WHERE uf = $selected_uf OR gracodigo = $selected_branch_group
),
baskets AS (
    SELECT uf, gracodigo, ramo, ABS(SUM(reference_premium)) > 0.01 AS eligible
    FROM scoped
    GROUP BY uf, gracodigo, ramo
)
SELECT s.uf, s.gracodigo, s.coenti,
       SUM(s.reference_premium) AS reference_premium,
       SUM(s.premium) FILTER (WHERE local.eligible) AS local_premium,
       SUM(s.premium) FILTER (WHERE without_uf.eligible) AS fixed_premium
FROM scoped s
JOIN baskets local USING (uf, gracodigo, ramo)
JOIN baskets without_uf
  ON without_uf.uf = '' AND without_uf.gracodigo = s.gracodigo AND without_uf.ramo = s.ramo
GROUP BY s.uf, s.gracodigo, s.coenti
HAVING reference_premium IS NOT NULL OR local_premium IS NOT NULL OR fixed_premium IS NOT NULL
ORDER BY s.uf, s.gracodigo, s.coenti
"""


@dataclass
class _Scope:
    reference: Decimal | None = None
    local: dict[str, Decimal] = field(default_factory=dict)
    fixed: dict[str, Decimal] = field(default_factory=dict)


def _collect(connection, start, end, insurers, group, selected_uf, selected_branch_group):
    scopes = defaultdict(_Scope)
    if not start or not end:
        first, last = connection.execute(
            "SELECT MIN(damesano), MAX(damesano) FROM dim_calendario"
        ).fetchone()
        start, end = start or first, end or last
    if not (insurers or group) or not start or not end or start > end:
        return scopes

    rows = connection.execute(_COLLECTION_SQL, {
        "start": start, "end": end, "insurers": insurers, "group_code": group,
        "selected_uf": selected_uf, "selected_branch_group": selected_branch_group,
    }).fetchall()
    for uf, group_code, company, reference, local, fixed in rows:
        scope = scopes[uf, group_code]
        if reference is not None:
            scope.reference = (scope.reference or _ZERO) + reference
        if local is not None:
            scope.local[company] = local
        if fixed is not None:
            scope.fixed[company] = fixed
    return scopes


def _at_cent(value):
    return value.quantize(_CENT, rounding=ROUND_HALF_UP)


def _positive(value):
    return value is not None and value > 0


def _combined(premium_a, premium_b, valid_pair):
    if not valid_pair or (premium_a is None and premium_b is None):
        return None
    return (premium_a or _ZERO) + (premium_b or _ZERO)


def _delta_hhi(premium_a, premium_b, market, valid_pair, *, allow_zero):
    if not valid_pair or not _positive(market):
        return None
    if allow_zero:
        premium_a, premium_b = premium_a or _ZERO, premium_b or _ZERO
        if premium_a < 0 or premium_b < 0:
            return None
    elif not (_positive(premium_a) and _positive(premium_b)):
        return None
    return 2 * (premium_a / market * 100) * (premium_b / market * 100)


def _table_measures(scope, company_a, company_b, valid_pair):
    premium_a, premium_b = scope.local.get(company_a), scope.local.get(company_b)
    combined = _combined(premium_a, premium_b, valid_pair)
    market = sum(scope.local.values()) if scope.local else None
    return {
        "combinedPremium": combined,
        "marketPremium": market,
        "combinedShare": _divide(combined, market) if _positive(market) else None,
        "hhiImpact": _delta_hhi(premium_a, premium_b, market, valid_pair, allow_zero=True),
    }


def _branch_measures(scope, company_a, company_b, valid_pair):
    measures = _table_measures(scope, company_a, company_b, valid_pair)
    return {
        "referencePremium": scope.reference,
        "premiumA": scope.local.get(company_a),
        "premiumB": scope.local.get(company_b),
        **measures,
        "competitivePressure": _divide(measures["combinedPremium"], scope.reference)
        if _positive(scope.reference) else None,
    }


def _cards(scope, reference, company_a, company_b, valid_pair):
    own_comparable = scope.fixed.get(reference)
    before = None
    if own_comparable is not None:
        own_comparable_cent = _at_cent(own_comparable)
        if own_comparable_cent > 0:
            before = 1 + sum(
                code != reference and _at_cent(premium) > own_comparable_cent
                for code, premium in scope.fixed.items()
            )

    premium_a, premium_b = scope.local.get(company_a), scope.local.get(company_b)
    combined = _combined(premium_a, premium_b, valid_pair)
    remaining = {
        code: premium for code, premium in scope.local.items() if code not in (company_a, company_b)
    }
    combined_position = after = None
    if _positive(combined):
        combined_cent = _at_cent(combined)
        combined_position = 1 + sum(
            premium > 0 and _at_cent(premium) > combined_cent for premium in remaining.values()
        )
    if reference is not None and combined is not None:
        if reference in (company_a, company_b):
            after = combined_position
        elif _positive(scope.reference):
            own_cent = _at_cent(scope.reference)
            after = 1 + (_at_cent(combined) > own_cent) + sum(
                _at_cent(premium) > own_cent
                for code, premium in remaining.items()
                if code != reference
            )

    # The card denominator removes the UF filter when identifying eligible
    # branches. The numerator and the shares in the tables use the local basket.
    market = sum(scope.fixed.values()) if scope.fixed else None
    hhi_before = None
    if _positive(market):
        shares = [premium / market * 100 for premium in scope.local.values() if premium > 0]
        hhi_before = sum(share ** 2 for share in shares) if shares else None
    delta = _delta_hhi(premium_a, premium_b, market, valid_pair, allow_zero=False)
    return {
        "referencePositionBefore": before,
        "referencePositionAfter": after,
        "positionImpact": before - after if before is not None and after is not None else None,
        "combinedPremium": combined,
        "combinedShare": _divide(combined, market),
        "combinedPosition": combined_position,
        "hhiBefore": hhi_before,
        "hhiAfter": hhi_before + delta if hhi_before is not None and delta is not None else None,
        "hhiImpact": delta,
    }


def get_ma(
    connection, *, start, end, insurers, group, company_a=None, company_b=None,
    selected_uf=None, selected_branch_group=None,
):
    """Return the summary and the two independently scoped M&A tables."""
    insurers = list(dict.fromkeys(insurers))
    reference = insurers[0] if len(insurers) == 1 else None
    valid_pair = bool(company_a and company_b and company_a != company_b)
    scopes = _collect(connection, start, end, insurers, group, selected_uf, selected_branch_group)
    uf_scope = selected_uf or ""
    branch_scope = selected_branch_group or ""

    # Clicking a row filters the other table and the cards, while the source
    # table, including its total, retains the context it had before the click.
    uf_rows = []
    for (code,) in connection.execute("SELECT uf FROM dim_uf ORDER BY uf").fetchall():
        measures = _table_measures(scopes[code, branch_scope], company_a, company_b, valid_pair)
        if any(value is not None for value in measures.values()):
            uf_rows.append({"code": code, **measures})
    branch_rows = []
    for code, name in connection.execute("SELECT gracodigo, grupo_ramo FROM dim_grupo_ramo").fetchall():
        measures = _branch_measures(scopes[uf_scope, code], company_a, company_b, valid_pair)
        if any(value is not None for value in measures.values()):
            branch_rows.append({"code": code, "name": name, **measures})
    branch_rows.sort(key=lambda row: (row["premiumB"] is None, -(row["premiumB"] or _ZERO), row["name"]))

    return {
        "reference": _reference_label(connection, insurers, group),
        "cards": _cards(scopes[uf_scope, branch_scope], reference, company_a, company_b, valid_pair),
        "uf": {
            "rows": uf_rows,
            "total": _table_measures(scopes["", branch_scope], company_a, company_b, valid_pair),
        },
        "branches": {
            "rows": branch_rows,
            "total": _branch_measures(scopes[uf_scope, ""], company_a, company_b, valid_pair),
        },
    }
