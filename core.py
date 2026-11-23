"""Cards and competitive ranking derived from the Raio-X TMDL measures."""

from decimal import Decimal


_PORTFOLIO_SQL = """
WITH premiums AS MATERIALIZED (
    SELECT
        damesano BETWEEN $start AND $end AS current_period,
        ramo,
        coenti,
        SUM(premio_direto) AS premium,
        SUM(premio_direto) FILTER (
            WHERE CASE WHEN len($entities::VARCHAR[]) > 0
                       THEN list_contains($entities::VARCHAR[], coenti)
                       ELSE cogrupo_historico = $group_code
                  END
        ) AS reference_premium
    FROM fato_premios_uf
    WHERE ($branch_group IS NULL OR gracodigo = $branch_group)
      AND (damesano BETWEEN $start AND $end
        OR damesano BETWEEN $prior_start AND $prior_end)
    GROUP BY current_period, ramo, coenti
),
portfolio AS (
    SELECT ramo
    FROM premiums
    WHERE current_period
    GROUP BY ramo
    HAVING ABS(SUM(reference_premium)) > 0.01
),
matching_premiums AS (
    SELECT p.*
    FROM premiums p JOIN portfolio USING (ramo)
),
market_by_insurer AS (
    SELECT p.coenti, d.seguradora AS name, SUM(p.premium) AS premium
    FROM matching_premiums p
    JOIN dim_seguradora d USING (coenti)
    WHERE p.current_period
    GROUP BY p.coenti, d.seguradora
    HAVING COUNT(p.premium) > 0
)
SELECT
    (SELECT SUM(reference_premium) FROM premiums WHERE current_period),
    (SELECT SUM(premium) FROM matching_premiums WHERE current_period),
    (SELECT SUM(reference_premium) FROM matching_premiums WHERE NOT current_period),
    (SELECT SUM(premium) FROM matching_premiums WHERE NOT current_period),
    ARRAY(SELECT ramo FROM portfolio ORDER BY ramo),
    ARRAY(
        SELECT {id: coenti, name: name, premium: premium}
        FROM market_by_insurer
        ORDER BY premium DESC NULLS LAST, coenti
    )
"""

_TECHNICAL_SQL = """
SELECT
    coenti,
    SUM(premio_ganho),
    SUM(sinistro_ocorrido),
    SUM(despesa_comercial)
FROM fato_premios_nacional
WHERE damesano BETWEEN $start AND $end
  AND list_contains($branches::VARCHAR[], ramo)
  AND list_contains($insurers::VARCHAR[], coenti)
GROUP BY coenti
"""

_METRICS = ("share", "sinistralidade", "margem")


def _divide(numerator, denominator):
    if numerator is None or not denominator:
        return None
    return numerator / denominator


def _reference_label(con, entities, group):
    if len(entities) > 1:
        return f"{len(entities)} seguradoras selecionadas"
    if entities:
        result = con.execute(
            "SELECT seguradora FROM dim_seguradora WHERE coenti = ?", [entities[0]]
        ).fetchone()
        if result:
            return result[0]
    elif group is not None:
        result = con.execute(
            "SELECT grupo_segurador FROM dim_grupo_segurador WHERE cogrupo = ?", [group]
        ).fetchone()
        if result:
            return f"Grupo: {result[0]}"
    return "Nenhuma referência selecionada"


def load_context(con, start, end, entities, group, *, branch_group=None):
    """Resolve the interval and retrieve the monetary context for the cards."""
    entities = list(dict.fromkeys(entities))
    prior_start = prior_end = None
    if start and end and start <= end and start[:4] == end[:4]:
        prior_year = int(end[:4]) - 1
        prior_start = f"{prior_year:04}{start[-2:]}"
        prior_end = f"{prior_year:04}{end[-2:]}"
    if not start or not end:
        first, last = con.execute(
            "SELECT MIN(damesano), MAX(damesano) FROM dim_calendario"
        ).fetchone()
        start, end = start or first, end or last

    values = (None, None, None, None, [], [])
    if (entities or group) and start and end and start <= end:
        values = con.execute(
            _PORTFOLIO_SQL,
            {
                "start": start,
                "end": end,
                "prior_start": prior_start,
                "prior_end": prior_end,
                "entities": entities,
                "group_code": group,
                "branch_group": branch_group,
            },
        ).fetchone()
    premium, market, prior_premium, prior_market, branches, competitors = values
    return {
        "start": start,
        "end": end,
        "entities": entities,
        "reference": _reference_label(con, entities, group),
        "premium": premium,
        "market": market,
        "prior_premium": prior_premium,
        "prior_market": prior_market,
        "branches": branches,
        "competitors": competitors,
    }


def _cards(context, whole_portfolio, selected_insurer):
    competitors = context["competitors"]
    entities = context["entities"]
    single = entities[0] if len(entities) == 1 else None
    own = next((row["premium"] for row in competitors if row["id"] == single), None)
    position = next_distance = leader_distance = None
    if own is not None:
        greater = [row for row in competitors if row["premium"] > own]
        if own > 0:
            # ALL(dim_seguradora[coenti]) retains the chart filter on the name.
            position = 1 + sum(
                selected_insurer is None or row["id"] == selected_insurer for row in greater
            )
        if greater:
            # The monetary sources used here have already been stored to cent precision.
            next_distance = min(row["premium"] for row in greater) - own
            leader_distance = max(row["premium"] for row in greater) - own

    share = _divide(context["premium"], context["market"])
    # Variação Contribuição MS removes the group-of-branches filter only from
    # the market denominator in both the current and the prior period.
    contribution = _divide(context["premium"], whole_portfolio["market"])
    prior_contribution = _divide(context["prior_premium"], whole_portfolio["prior_market"])
    change = None
    if contribution is not None and prior_contribution is not None:
        change = (contribution - prior_contribution) * 100

    if position is None:
        next_label = "Distância para a posição acima"
    elif position == 1:
        next_label = "Líder de mercado"
    else:
        next_label = f"Distância para a {position - 1}ª posição"
    return {
        "share": share,
        "premium": context["premium"],
        "market_premium": context["market"],
        "share_change_pp": change,
        "position": position,
        "competitor_count": sum(row["premium"] > 0 for row in competitors) or None,
        "next_distance": next_distance,
        "leader_distance": leader_distance,
        "next_label": next_label,
    }


def _indicator_values(con, context, metric, premiums):
    if metric == "share":
        return {code: _divide(premium, Decimal(1_000_000_000)) for code, premium in premiums.items()}
    if not premiums or not context["branches"]:
        return {}
    values = {}
    for code, earned, claims, expenses in con.execute(
        _TECHNICAL_SQL,
        {
            "start": context["start"],
            "end": context["end"],
            "branches": context["branches"],
            "insurers": list(premiums),
        },
    ).fetchall():
        numerator = claims
        if metric == "margem":
            numerator = None if earned is None else earned - (claims or 0) - (expenses or 0)
        values[code] = _divide(numerator, earned)
    return values


def _ranking(con, context, metric):
    if len(context["entities"]) != 1:
        return []
    reference = context["entities"][0]
    ranked = []
    previous = None
    rank = 0
    for row in context["competitors"]:
        premium = row["premium"]
        if premium <= 0:
            break
        if premium != previous:
            previous = premium
            rank += 1
        selected = row["id"] == reference
        if rank <= 5 or selected:
            ranked.append({**row, "rank": rank, "selected": selected})
    values = _indicator_values(
        con, context, metric, {row["id"]: row["premium"] for row in ranked}
    )
    for row in ranked:
        row["value"] = values.get(row["id"])
    # Power BI applies its saved descending visual sort after the premium-based filter.
    visible = [row for row in ranked if row["value"] is not None]
    return sorted(visible, key=lambda row: (-row["value"], row["name"]))


def dashboard_core(
    con, start, end, entities, group, metric,
    *, selected_insurer=None, selected_branch_group=None,
):
    """Return cards and ranking. Share is a fraction, change is in percentage points."""
    if metric not in _METRICS:
        raise ValueError(f"Indicador desconhecido: {metric}")
    whole = load_context(con, start, end, entities, group)
    context = whole
    ranking = _ranking(con, whole, metric)
    if selected_branch_group is not None:
        context = load_context(con, start, end, entities, group, branch_group=selected_branch_group)
        premiums = {row["id"]: row["premium"] for row in context["competitors"]}
        shown = {row["id"]: premiums.get(row["id"]) for row in ranking}
        # The national technical measure uses the visible branch basket; the
        # company may have a technical value even without a UF amount in it.
        values = _indicator_values(con, context, metric, shown)
        for row in ranking:
            row["highlight_premium"] = shown[row["id"]]
            row["highlight_value"] = values.get(row["id"])
    return {
        "reference": context["reference"],
        "cards": _cards(context, whole, selected_insurer),
        "ranking": ranking,
    }
