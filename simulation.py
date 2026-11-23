"""Simulações estratégicas, translated from Crescimento Concorrentes.tmdl."""

from decimal import Decimal, ROUND_HALF_UP

from core import _divide, load_context


CENT = Decimal("0.01")
ZERO = Decimal(0)


def _at_cent(amount):
    """DAX ROUND breaks a half-cent tie away from zero."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def _dense_positions(premiums):
    """RANKX DENSE operates only over positive premiums for table rows."""
    return {
        premium: rank
        for rank, premium in enumerate(
            sorted({premium for premium in premiums if premium is not None and premium > 0}, reverse=True),
            1,
        )
    }


def _goal_cards(current_position, reference_premium, competitors, goal):
    """The two NoFilter cards evaluate both growth parameter measures at 0%."""
    if not goal or current_position is None or reference_premium is None or reference_premium <= 0:
        return None, None
    target = current_position - goal
    if not 1 <= target <= len(competitors) + 1:
        return None, None
    order = target if goal > 0 else target - 1
    if not 1 <= order <= len(competitors):
        return None, None
    cutoff = _at_cent(competitors[order - 1]["premium"])
    if goal > 0:
        return max(ZERO, (cutoff + CENT) / reference_premium - 1), None
    return None, max(ZERO, reference_premium - max(ZERO, cutoff - CENT))


def _simulate(context, reference_growth, competitor_growth, goal, *, selected_insurer=None):
    premium = context["premium"]
    market = context["market"]
    entities = context["entities"]
    reference = entities[0] if len(entities) == 1 else None
    reference_factor = Decimal(100 + reference_growth) / 100
    competitor_factor = Decimal(100 + competitor_growth) / 100
    simulated_reference = premium * reference_factor if premium is not None else None
    simulated_competitors = (market - premium) * competitor_factor if market is not None and premium is not None else None
    simulated_market = None
    if simulated_reference is not None or simulated_competitors is not None:
        simulated_market = (simulated_reference or ZERO) + (simulated_competitors or ZERO)
    current_share = _divide(premium, market)
    simulated_share = _divide(simulated_reference, simulated_market)

    rows = [
        {**row, "simulated": row["premium"] * (
            reference_factor if row["id"] == reference else competitor_factor
        ) if reference else None}
        for row in sorted(context["competitors"], key=lambda row: (-row["premium"], row["id"]))
    ]
    own = next((row for row in rows if row["id"] == reference), None)
    current_position = simulated_position = None
    if own and own["premium"] > 0:
        # The position cards remove the code filter but retain the selected
        # insurer name. The table's dense ranks use the unfiltered universe.
        position_rows = [row for row in rows if selected_insurer is None or row["id"] == selected_insurer]
        current_position = 1 + sum(row["premium"] > own["premium"] for row in position_rows)
        simulated_cutoff = _at_cent(own["simulated"])
        simulated_position = 1 + sum(_at_cent(row["simulated"]) > simulated_cutoff for row in position_rows)

    current_dense = _dense_positions(row["premium"] for row in rows)
    simulated_dense = _dense_positions(row["simulated"] for row in rows)
    positive = [row for row in rows if row["premium"] > 0]
    simulated_positive = sorted(
        (row for row in rows if row["simulated"] is not None and row["simulated"] > 0),
        key=lambda row: (-row["simulated"], row["id"]),
    )
    top = {row["id"] for row in positive[:10] + simulated_positive[:10]}
    if own:
        top.add(reference)
    additional, safety = _goal_cards(
        current_position, premium, [row for row in positive if row["id"] != reference], goal
    )

    return {
        "reference": context["reference"],
        "cards": {
            "currentShare": current_share,
            "simulatedShare": simulated_share,
            "impactPp": (simulated_share - current_share) * 100
                if current_share is not None and simulated_share is not None else None,
            "currentPosition": current_position,
            "simulatedPosition": simulated_position,
            "positionChange": current_position - simulated_position if current_position is not None else None,
            "additionalGrowth": additional,
            "safetyMargin": safety,
        },
        "chart": [
            {
                "id": row["id"],
                "name": row["name"],
                "currentPremium": row["premium"],
                "simulatedPremium": row["simulated"],
                "selected": row["id"] == reference,
            }
            for row in rows if row["id"] in top
        ],
        "ranking": [
            {
                "id": row["id"],
                "name": row["name"],
                "currentPosition": current_dense[row["premium"]],
                "simulatedPosition": simulated_dense.get(row["simulated"]),
                "positionChange": current_dense[row["premium"]] - simulated_dense[row["simulated"]]
                    if row["simulated"] in simulated_dense else None,
                "selected": row["id"] == reference,
            }
            for row in positive
        ],
    }


def get_simulation(
    connection, *, start, end, insurers, group, reference_growth, competitor_growth, goal, selected_insurer=None,
):
    """Return the simulation visuals for the shared entity and time context."""
    context = load_context(connection, start, end, list(insurers), group)
    return _simulate(context, reference_growth, competitor_growth, goal, selected_insurer=selected_insurer)
