"""Strategic simulation regression fixtures from the Power BI model."""

from decimal import Decimal
import unittest

from core import load_context
from server import find_data_dir, open_database
from simulation import _simulate, get_simulation


class SimulatorParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = open_database(find_data_dir())
        cls.addClassCleanup(cls.database.close)

    def scenario(self, **changes):
        filters = {
            "start": "202601", "end": "202609", "insurers": ("05631",),
            "group": "00230", "reference_growth": 18, "competitor_growth": 0, "goal": -3,
        }
        return get_simulation(self.database, **{**filters, **changes})

    def test_saved_scenario_and_unrounded_impact(self):
        result = self.scenario()
        cards = result["cards"]
        reference = Decimal("2204253143.25")
        market = Decimal("84243304989.16")
        projected = reference * Decimal("1.18")
        self.assertEqual(cards["currentShare"], reference / market)
        self.assertEqual(cards["simulatedShare"], projected / (market - reference + projected))
        self.assertEqual(cards["impactPp"], (cards["simulatedShare"] - cards["currentShare"]) * 100)
        self.assertEqual(format(cards["impactPp"], ".2f"), "0.46")
        self.assertEqual((cards["currentPosition"], cards["simulatedPosition"], cards["positionChange"]), (12, 10, 2))
        context = load_context(self.database, "202601", "202609", ["05631"], "00230")
        competitors = sorted(
            (row for row in context["competitors"] if row["id"] != "05631" and row["premium"] > 0),
            key=lambda row: (-row["premium"], row["id"]),
        )
        self.assertEqual(sum(row["premium"] > reference for row in competitors), 11)
        # A drop from 12th to 15th uses the 14th competitor's premium less a cent.
        cutoff = competitors[13]
        self.assertEqual((cutoff["id"], cutoff["premium"]), ("06564", Decimal("1369570174.25")))
        self.assertEqual(reference - cards["safetyMargin"], cutoff["premium"] - Decimal("0.01"))
        self.assertEqual(cards["safetyMargin"], Decimal("834682969.01"))
        self.assertIsNone(cards["additionalGrowth"])
        self.assertEqual(len(result["chart"]), 11)
        self.assertEqual(len(result["ranking"]), 111)
        reference_row = next(row for row in result["chart"] if row["selected"])
        self.assertEqual(reference_row["currentPremium"], reference)
        self.assertEqual(reference_row["simulatedPremium"], projected)

    def test_zero_growth_and_no_goal(self):
        result = self.scenario(reference_growth=0, competitor_growth=0, goal=0)
        cards = result["cards"]
        self.assertEqual(cards["currentShare"], cards["simulatedShare"])
        self.assertEqual(cards["impactPp"], 0)
        self.assertEqual(cards["currentPosition"], cards["simulatedPosition"])
        self.assertEqual(cards["positionChange"], 0)
        self.assertIsNone(cards["safetyMargin"])
        self.assertIsNone(cards["additionalGrowth"])
        self.assertTrue(all(row["currentPremium"] == row["simulatedPremium"] for row in result["chart"]))

    def test_boundary_growth_and_competitor_reaction(self):
        decline = self.scenario(reference_growth=-30, competitor_growth=10, goal=2)
        expansion = self.scenario(reference_growth=100, competitor_growth=-30, goal=2)
        for result, own_factor, competitor_factor, position in (
            (decline, Decimal("0.7"), Decimal("1.1"), 13),
            (expansion, Decimal("2"), Decimal("0.7"), 6),
        ):
            self.assertEqual(result["cards"]["simulatedPosition"], position)
            for row in result["chart"]:
                factor = own_factor if row["selected"] else competitor_factor
                self.assertEqual(row["simulatedPremium"], row["currentPremium"] * factor)
        self.assertLess(decline["cards"]["impactPp"], 0)
        self.assertGreater(expansion["cards"]["impactPp"], 0)

    def test_goal_cards_preserve_power_bi_no_filter_interactions(self):
        saved = self.scenario()["cards"]
        changed = self.scenario(reference_growth=-30, competitor_growth=100)["cards"]
        self.assertEqual(changed["safetyMargin"], saved["safetyMargin"])
        self.assertNotEqual(changed["simulatedShare"], saved["simulatedShare"])
        upward = self.scenario(goal=2)["cards"]
        upward_other_sliders = self.scenario(goal=2, reference_growth=100, competitor_growth=-30)["cards"]
        self.assertEqual(upward["additionalGrowth"], Decimal("0.159571621688329421870724602"))
        self.assertEqual(upward_other_sliders["additionalGrowth"], upward["additionalGrowth"])
        self.assertIsNone(upward["safetyMargin"])

    def test_chart_selection_scopes_position_cards_like_desktop(self):
        original = self.scenario()
        selected = self.scenario(selected_insurer="05886")
        cards = selected["cards"]
        self.assertEqual((cards["currentPosition"], cards["simulatedPosition"], cards["positionChange"]), (2, 2, 0))
        self.assertEqual(cards["safetyMargin"], 0)
        for key in ("currentShare", "simulatedShare", "impactPp"):
            self.assertEqual(cards[key], original["cards"][key])
        self.assertEqual(selected["chart"], original["chart"])
        self.assertEqual(selected["ranking"], original["ranking"])
        porto = next(row for row in selected["ranking"] if row["id"] == "05886")
        self.assertEqual((porto["currentPosition"], porto["simulatedPosition"]), (1, 1))

    def test_other_period_and_insurer(self):
        period = self.scenario(start="202511", end="202603")["cards"]
        self.assertEqual((period["currentPosition"], period["simulatedPosition"]), (11, 10))
        leader = self.scenario(start="202510", insurers=("04707",), group=None, goal=1)["cards"]
        self.assertEqual((leader["currentPosition"], leader["simulatedPosition"]), (1, 1))
        self.assertIsNone(leader["additionalGrowth"])

    def test_absence_and_negative_production(self):
        no_group_data = self.scenario(start="202609", end="202609", insurers=())
        for result in (no_group_data, self.scenario(start="202609", end="202601")):
            self.assertTrue(all(value is None for value in result["cards"].values()))
            self.assertEqual(result["chart"], [])
            self.assertEqual(result["ranking"], [])
        negative = self.scenario(start="202603", end="202603", insurers=("01864",), group=None)
        self.assertLess(negative["cards"]["currentShare"], 0)
        self.assertIsNone(negative["cards"]["currentPosition"])
        self.assertIsNone(negative["cards"]["simulatedPosition"])
        self.assertEqual(
            next(row for row in negative["chart"] if row["selected"])["currentPremium"],
            Decimal("-24335500.92"),
        )

    def test_simulated_card_ties_at_cent_but_table_uses_unrounded_dense_rank(self):
        context = {
            "reference": "A",
            "entities": ["A"],
            "premium": Decimal("100"),
            "market": Decimal("297.02"),
            "competitors": [
                {"id": insurer, "name": insurer, "premium": Decimal(value)}
                for insurer, value in (("A", "100"), ("B", "99.01"), ("C", "99.01"), ("D", "0"), ("E", "-1"))
            ],
        }
        result = _simulate(context, 0, 1, 0)
        self.assertEqual(result["cards"]["simulatedPosition"], 1)
        table = {row["id"]: row for row in result["ranking"]}
        self.assertEqual(table["A"]["simulatedPosition"], 2)
        self.assertEqual(table["B"]["simulatedPosition"], 1)
        self.assertEqual(table["C"]["simulatedPosition"], 1)
        self.assertEqual(set(table), {"A", "B", "C"})

    def test_reference_uses_comparable_amount_for_rank_and_is_excluded_from_goal_cutoff(self):
        context = {
            "reference": "A",
            "entities": ["A"],
            # The unscoped measure can differ from the amount for eligible branches.
            "premium": Decimal("99.99"),
            "market": Decimal("600"),
            "competitors": [
                {"id": insurer, "name": insurer, "premium": Decimal(value)}
                for insurer, value in (
                    ("A", "100"), ("B", "100"), ("C", "120"), ("D", "110"), ("E", "90"), ("F", "80"),
                )
            ],
        }
        cards = _simulate(context, 0, 0, -2)["cards"]
        self.assertEqual((cards["currentPosition"], cards["simulatedPosition"]), (3, 3))
        self.assertEqual(cards["safetyMargin"], Decimal("10.00"))

        own_row = _simulate(context, 0, 0, 0, selected_insurer="A")["cards"]
        self.assertEqual((own_row["currentPosition"], own_row["simulatedPosition"]), (1, 1))


if __name__ == "__main__":
    unittest.main()
