"""History and portfolio diagnosis from the Raio-X DAX measures."""

from decimal import Decimal


CENT = Decimal("0.01")


def _reference(insurers, group):
    if insurers:
        return "p.coenti = ANY(?::VARCHAR[])", [insurers]
    if group:
        return "p.cogrupo_historico = ?", [group]
    return "FALSE", []


def _sum_present(values):
    present = [value for value in values if value is not None]
    return sum(present) if present else None


def _percent(numerator, denominator):
    if numerator is None or not denominator:
        return None
    return float(100 * numerator / denominator)


def _technical_percent(metric, earned, claims, expenses, *, strict_margin=False):
    if metric == "sinistralidade":
        return _percent(claims, earned)
    if not earned or (strict_margin and (claims is None or expenses is None)):
        return None
    return _percent(earned - (claims or 0) - (expenses or 0), earned)


def _months(start, end):
    first = int(start[:4]) * 12 + int(start[4:]) - 1
    last = int(end[:4]) * 12 + int(end[4:]) - 1
    return [f"{index // 12:04}{index % 12 + 1:02}" for index in range(first, last + 1)]


def _prior_month(month):
    return f"{int(month[:4]) - 1:04}{month[4:]}"


def _portfolio(connection, start, end, condition, reference_parameters):
    # Both the current totals and the basket come from [Prêmios Referência].
    return connection.execute(
        f"""
        SELECT p.gracodigo, p.ramo, SUM(p.premio_direto)
        FROM fato_premios_uf p
        WHERE p.damesano BETWEEN ? AND ? AND ({condition})
        GROUP BY p.gracodigo, p.ramo
        """,
        [start, end, *reference_parameters],
    ).fetchall()


def _evolution(connection, months, basket, metric, condition, reference_parameters):
    if not months or not basket:
        return []

    previous = [_prior_month(month) for month in months]
    if metric == "share":
        observations = connection.execute(
            f"""
            SELECT p.damesano, SUM(p.premio_direto) FILTER (WHERE {condition}),
                   SUM(p.premio_direto)
            FROM fato_premios_uf p
            WHERE p.damesano = ANY(?::VARCHAR[]) AND p.ramo = ANY(?::VARCHAR[])
            GROUP BY p.damesano
            """,
            [*reference_parameters, months + previous, basket],
        ).fetchall()
        values = {month: _percent(ref, market) for month, ref, market in observations}
    else:
        # The technical base measures intersect the historical month with the
        # current period through KEEPFILTERS, leaving the prior series blank.
        observations = connection.execute(
            f"""
            SELECT p.damesano, SUM(p.premio_ganho), SUM(p.sinistro_ocorrido),
                   SUM(p.despesa_comercial)
            FROM fato_premios_nacional p
            WHERE p.damesano = ANY(?::VARCHAR[]) AND p.ramo = ANY(?::VARCHAR[])
              AND ({condition})
            GROUP BY p.damesano
            """,
            [months, basket, *reference_parameters],
        ).fetchall()
        values = {month: _technical_percent(metric, *amounts) for month, *amounts in observations}

    if months[0][:4] != months[-1][:4]:
        return [
            {"year": int(month[:4]), "month": int(month[4:]), "value": values.get(month),
             "axis": axis, "series": series}
            for series, dates in (("previous", previous), ("current", months))
            for axis, month in zip(months, dates, strict=True)
        ]
    return [
        {"year": int(month[:4]), "month": int(month[4:]), "value": values.get(month)}
        for month in previous + months
    ]


def _prior_premiums(connection, start, end, basket, group_codes, condition, reference_parameters):
    if start[:4] != end[:4] or not basket or not group_codes:
        return {}
    # [Prêmios Referência AA Carteira] retains the filter on the group of
    # branches and evaluates the earlier period with the current basket.
    totals = connection.execute(
        f"""
        SELECT p.gracodigo, SUM(p.premio_direto)
        FROM fato_premios_uf p
        WHERE p.damesano BETWEEN ? AND ? AND p.ramo = ANY(?::VARCHAR[])
          AND p.gracodigo = ANY(?::VARCHAR[])
          AND ({condition})
        GROUP BY GROUPING SETS ((p.gracodigo), ())
        """,
        [_prior_month(start), _prior_month(end), basket, group_codes, *reference_parameters],
    ).fetchall()
    return dict(totals)


def _technical_groups(
    connection, start, end, group_codes, condition, reference_parameters, insurer, selected_insurer
):
    if insurer:
        market_condition = "p.coenti <> ?"
        market_parameters = [insurer]
    else:
        market_condition = "FALSE"
        market_parameters = []
    # The selected ranking insurer constrains VALUES(fato_premios_uf[ramo]).
    # The national measures remove that insurer filter before summing.
    rows = connection.execute(
        f"""
        WITH group_branches AS (
            SELECT DISTINCT gracodigo, ramo
            FROM fato_premios_uf
            WHERE gracodigo = ANY(?::VARCHAR[]) AND (? IS NULL OR coenti = ?)
        ),
        amounts AS (
            SELECT g.gracodigo, p.premio_ganho AS earned,
                   p.sinistro_ocorrido AS claims, p.despesa_comercial AS expenses,
                   ({condition}) AS reference, ({market_condition}) AS competitor
            FROM fato_premios_nacional p
            JOIN group_branches g USING (ramo)
            WHERE p.damesano BETWEEN ? AND ?
        )
        SELECT gracodigo,
               SUM(earned) FILTER (WHERE reference),
               SUM(claims) FILTER (WHERE reference),
               SUM(expenses) FILTER (WHERE reference),
               SUM(earned) FILTER (WHERE competitor),
               SUM(claims) FILTER (WHERE competitor),
               SUM(expenses) FILTER (WHERE competitor)
        FROM amounts
        GROUP BY GROUPING SETS ((gracodigo), ())
        """,
        [
            group_codes, selected_insurer, selected_insurer,
            *reference_parameters, *market_parameters, start, end,
        ],
    ).fetchall()
    return {code: amounts for code, *amounts in rows}


def _diagnosis(
    connection, start, end, metric, insurers, condition, reference_parameters,
    portfolio, basket, selected_insurer,
):
    names = dict(connection.execute("SELECT gracodigo, grupo_ramo FROM dim_grupo_ramo").fetchall())
    grouped = {
        code: _sum_present(premium for group, _, premium in portfolio if group == code)
        for code in names
    }
    visible_groups = [
        (code, premium)
        for code, premium in sorted(grouped.items(), key=lambda item: (-(item[1] or 0), item[0]))
        if premium is not None and abs(premium) > CENT
    ]
    group_codes = [code for code, _ in visible_groups]
    # The report's visual-level [Grupo com Produção] filter restricts the
    # grand total. The weight measure explicitly removes that group filter.
    prior = _prior_premiums(connection, start, end, basket, group_codes, condition, reference_parameters)
    visible_total = _sum_present(premium for _, premium in visible_groups)
    total = _sum_present(premium for _, _, premium in portfolio)
    market_premium = None
    technical = {}
    if metric == "share" and basket:
        market_premium = connection.execute(
            """
            SELECT SUM(premio_direto) FROM fato_premios_uf
            WHERE damesano BETWEEN ? AND ? AND ramo = ANY(?::VARCHAR[])
            """,
            [start, end, basket],
        ).fetchone()[0]
    elif metric != "share" and group_codes:
        insurer = insurers[0] if len(insurers) == 1 else None
        technical = _technical_groups(
            connection, start, end, group_codes, condition,
            reference_parameters, insurer, selected_insurer,
        )

    def row(code, label, premium):
        prior_premium = prior.get(code)
        premium_delta = None
        if premium is not None and prior_premium is not None and prior_premium > 0:
            premium_delta = _percent(premium - prior_premium, prior_premium)
        market = None
        if metric == "share":
            indicator = _percent(premium, market_premium)
        else:
            amounts = technical.get(code, [None] * 6)
            indicator = _technical_percent(metric, *amounts[:3], strict_margin=True)
            market = _technical_percent(metric, *amounts[3:])
        return {
            "code": code,
            "label": label,
            "premium": premium,
            "weightPct": _percent(premium, total),
            "premiumDeltaPct": premium_delta,
            "indicatorPct": indicator,
            "marketPct": market,
            "deviationPp": indicator - market if indicator is not None and market is not None else None,
        }

    rows = [row(code, names[code], premium) for code, premium in visible_groups]
    return {
        "rows": rows,
        "total": row(None, "Total", visible_total) if visible_total is not None else None,
    }


def _eligible_branches(portfolio):
    branch_totals = {}
    for _, branch, premium in portfolio:
        if premium is not None:
            branch_totals[branch] = branch_totals.get(branch, Decimal(0)) + premium
    return [branch for branch, premium in branch_totals.items() if abs(premium) > CENT]


def get_analysis(
    connection, *, start: str, end: str, insurers: list[str], group: str | None, metric: str,
    selected_insurer: str | None = None, selected_branch_group: str | None = None,
):
    """Return historical series and group diagnosis with percentages in points."""
    if start > end or not (insurers or group):
        return {"evolution": [], "diagnosis": {"rows": [], "total": None}}

    condition, reference_parameters = _reference(insurers, group)
    portfolio = _portfolio(connection, start, end, condition, reference_parameters)
    basket = _eligible_branches(portfolio)
    evolution_basket = basket
    if selected_branch_group is not None:
        evolution_basket = _eligible_branches(
            row for row in portfolio if row[0] == selected_branch_group
        )
    months = _months(start, end) if metric == "share" or start[:4] == end[:4] else []
    return {
        "evolution": _evolution(
            connection, months, evolution_basket, metric, condition, reference_parameters
        ),
        "diagnosis": _diagnosis(
            connection, start, end, metric, insurers, condition, reference_parameters,
            portfolio, basket, selected_insurer,
        ),
    }
