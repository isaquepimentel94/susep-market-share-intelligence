"""Medidas da Visão por UF recuperadas do modelo semântico do Power BI."""

from collections import defaultdict
from decimal import Decimal

from core import _reference_label


_CENT = Decimal("0.01")
_MAP_NAMES = {
    "SP": "Sao Paulo",
    "GO": "Goias",
    "ES": "Espirito Santo",
    "CE": "Ceara",
    "PA": "Para",
    "PB": "Paraiba",
    "PI": "Piaui",
    "PR": "Parana",
    "RO": "Rondonia",
    "AP": "Amapa",
    "MA": "Maranhao",
}

_UF_SQL = """
WITH portfolio AS (
    SELECT f.ramo
    FROM fato_premios_uf f
    JOIN dim_ramo d ON f.ramo = d.ramo
    WHERE f.damesano BETWEEN $start AND $end
      AND CASE
            WHEN len($insurers::VARCHAR[]) > 0
              THEN list_contains($insurers::VARCHAR[], coenti)
            ELSE cogrupo_historico = $group
          END
    GROUP BY f.ramo
    HAVING SUM(premio_direto) > 0.01
)
SELECT
    f.uf,
    f.coenti,
    SUM(f.premio_reportado_uf)
        FILTER (WHERE f.damesano BETWEEN $start AND $end) AS premium,
    SUM(f.premio_reportado_uf)
        FILTER (WHERE f.damesano BETWEEN $prior_start AND $prior_end) AS prior
FROM fato_premios_uf f
JOIN portfolio p USING (ramo)
WHERE (f.damesano BETWEEN $start AND $end)
   OR (f.damesano BETWEEN $prior_start AND $prior_end)
GROUP BY f.uf, f.coenti
"""


def _year_ago(month):
    return f"{int(month[:4]) - 1:04}{month[4:]}"


def _market_share(own, market, *, allow_nonpositive_own=False):
    if own is None or not market or market <= 0:
        return None
    if not allow_nonpositive_own and own <= 0:
        return None
    return 100 * own / market


def _regions(con, rows, single):
    current = defaultdict(dict)
    previous = defaultdict(dict)
    for uf, code, premium, prior in rows:
        if premium is not None:
            current[uf][code] = premium
        if prior is not None:
            previous[uf][code] = prior

    states = []
    coverage = leadership = top3 = 0
    for uf, name in con.execute("SELECT uf, estado FROM dim_uf ORDER BY uf").fetchall():
        premiums = current[uf]
        prior_premiums = previous[uf]
        market = sum(premiums.values()) if premiums else None
        prior_market = sum(prior_premiums.values()) if prior_premiums else None
        own = premiums.get(single)
        share = _market_share(own, market)
        previous_share = _market_share(
            prior_premiums.get(single), prior_market, allow_nonpositive_own=True
        )
        position = None
        if own is not None and own > 0:
            coverage += 1
            leadership += own >= max(premiums.values()) - _CENT
            top3 += sum(premium > own + _CENT for premium in premiums.values()) <= 2
            position = 1 + sum(premium > own for premium in premiums.values())

        states.append({
            "uf": uf, "name": name, "mapName": _MAP_NAMES.get(uf, name),
            "premium": own, "marketPremium": market, "share": share,
            "previousShare": previous_share,
            "changePp": share - previous_share
            if share is not None and previous_share is not None else None,
            "position": position,
            # The shape map groups Estado Mapa, outside ISINSCOPE(uf).
            "mapPosition": None,
        })

    positive = [state for state in states if state["share"] is not None]
    best = min(positive, key=lambda state: (-state["share"], state["uf"])) if positive else None
    cards = {
        "coverage": coverage or None,
        "leadership": leadership or None,
        "top3": top3,
        "bestUf": best["uf"] if best else None,
        "bestShare": best["share"] if best else None,
    }
    return states, cards, current


def _ranking(names, current, single, selected_uf, selected_insurer, highlighted_uf=None):
    totals = {}
    slices = [current.get(selected_uf, {})] if selected_uf else current.values()
    for premiums in slices:
        for code, premium in premiums.items():
            totals[code] = totals.get(code, Decimal(0)) + premium

    rows = [
        {"id": code, "name": names[code], "premium": premium,
         "selected": code == single, "active": code == selected_insurer}
        for code, premium in sorted(
            totals.items(), key=lambda pair: (-pair[1], names.get(pair[0], ""), pair[0])
        )
        if code in names
    ]
    if highlighted_uf:
        state_premiums = current.get(highlighted_uf, {})
        for row in rows:
            row["highlighted"] = True
            row["highlightPremium"] = state_premiums.get(row["id"])
    return rows


def get_uf_analysis(con, *, start, end, insurers, group, selected_uf=None, selected_insurer=None):
    """Return the state visuals, keeping the reference basket independent of a UF selection."""
    insurers = list(dict.fromkeys(insurers))
    single = insurers[0] if len(insurers) == 1 else None
    rows = []
    if start and end and start <= end and (insurers or group):
        rows = con.execute(_UF_SQL, {
            "start": start,
            "end": end,
            # Without a single entity, DAX has no previous-year share.
            "prior_start": _year_ago(start) if single else None,
            "prior_end": _year_ago(end) if single else None,
            "insurers": insurers,
            "group": group,
        }).fetchall()

    states, cards, current = _regions(con, rows, single)
    selected_state = next((state for state in states if state["uf"] == selected_uf), None)
    title = selected_state["mapName"] if selected_state else "Brasil"
    names = dict(con.execute("SELECT coenti, seguradora FROM dim_seguradora").fetchall())
    ranking = _ranking(names, current, single, selected_uf, selected_insurer)
    # Shape-map and variation clicks keep the national bars and overlay
    # only the amounts belonging to the selected UF.
    base_ranking = (
        _ranking(names, current, single, None, selected_insurer, highlighted_uf=selected_uf)
        if selected_uf else ranking
    )
    return {
        "reference": _reference_label(con, insurers, group),
        "cards": cards,
        "states": states,
        "ranking": ranking,
        "rankingTitle": f"Ranking Competitivo | {title}",
        "baseRanking": base_ranking,
        "baseRankingTitle": "Ranking Competitivo | Brasil",
        "selection": selected_uf,
    }
