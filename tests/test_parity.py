import unittest
from decimal import Decimal

from core import load_context
from server import DEFAULTS, Service, find_data_dir, open_database


class PowerBIParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = open_database(find_data_dir())
        cls.addClassCleanup(cls.database.close)
        cls.service = Service(cls.database)

    def analyze(self, *, start="202601", end="202609", entities=("05631",),
                group="00230", metric="margem"):
        return self.service.analyze({
            "start": [start], "end": [end], "entity": list(entities),
            "group": [group or ""], "metric": [metric],
        })

    def test_default_cards_match_exported_power_bi_query(self):
        cards = self.analyze()["cards"]
        self.assertEqual(cards["premium"], Decimal("2204253143.25"))
        self.assertEqual(cards["market_premium"], Decimal("84243304989.16"))
        self.assertEqual(cards["position"], 12)
        self.assertEqual(cards["competitor_count"], 111)
        self.assertEqual(cards["next_distance"], Decimal("61653812.34"))
        self.assertEqual(cards["leader_distance"], Decimal("11814810669.58"))
        self.assertAlmostEqual(cards["share"], Decimal("0.0261653213099"), places=13)
        self.assertAlmostEqual(cards["share_change_pp"], Decimal("-0.013738334"), places=9)
        self.assertEqual(format(cards["share"] * 100, ".2f"), "2.62")
        self.assertEqual(format(cards["premium"] / 10**9, ".2f"), "2.20")
        self.assertEqual(format(cards["next_distance"] / 10**6, ".2f"), "61.65")
        self.assertEqual(format(cards["leader_distance"] / 10**9, ".2f"), "11.81")

    def test_net_reversals_keep_a_branch_in_the_basket(self):
        context = load_context(self.database, "202601", "202609", ["05631"], "00230")
        self.assertEqual(len(context["branches"]), 18)
        for branch, expected in (("0112", "-15086.47"), ("0167", "-972.81")):
            value = self.database.execute("""
                SELECT sum(premio_direto) FROM fato_premios_uf
                WHERE coenti = '05631' AND ramo = ? AND damesano BETWEEN '202601' AND '202609'
            """, [branch]).fetchone()[0]
            self.assertEqual(value, Decimal(expected))
            self.assertIn(branch, context["branches"])

    def test_market_leader_in_a_different_window(self):
        cards = self.analyze(start="201901", end="201901", entities=("04707",), group=None)["cards"]
        self.assertEqual(cards["position"], 1)
        self.assertGreater(cards["premium"], 0)
        self.assertIsNone(cards["next_distance"])
        self.assertIsNone(cards["leader_distance"])

    def test_negative_net_premium_keeps_the_amount_but_has_no_position(self):
        result = self.analyze(start="202603", end="202603", entities=("01864",), group=None)
        self.assertEqual(result["cards"]["premium"], Decimal("-24335500.92"))
        self.assertIsNone(result["cards"]["position"])
        self.assertTrue(any(row["premium"] < 0 for row in result["diagnosis"]["rows"]))

    def test_group_only_and_month_without_historical_membership(self):
        august = self.analyze(start="202608", end="202608", entities=())
        september = self.analyze(start="202609", end="202609", entities=())
        self.assertEqual(august["cards"]["premium"], Decimal("2912091664.67"))
        self.assertIsNone(august["cards"]["position"])
        self.assertIsNone(september["cards"]["premium"])
        self.assertEqual(september["ranking"], [])
        self.assertEqual(september["diagnosis"]["rows"], [])
        self.assertIsNotNone(self.analyze(start="202609", end="202609")["cards"]["premium"])

    def test_selection_precedence_and_multiple_references(self):
        selected_with_group = self.analyze()
        self.assertEqual(selected_with_group, self.analyze(group=None))
        combined = self.analyze(entities=("05631", "04707"))
        self.assertIsNotNone(combined["cards"]["premium"])
        self.assertIsNone(combined["cards"]["position"])
        self.assertEqual(combined["ranking"], [])
        self.assertTrue(all(row["marketPct"] is None for row in combined["diagnosis"]["rows"]))

    def test_blank_states_and_cross_year_history(self):
        for result in (
            self.analyze(entities=(), group=None),
            self.analyze(start="202609", end="202601"),
        ):
            self.assertIsNone(result["cards"]["share"])
            self.assertEqual(result["ranking"], [])
            self.assertEqual(result["evolution"], [])
            self.assertEqual(result["diagnosis"]["rows"], [])
        cross_year = self.analyze(start="202510", end="202609", metric="share")
        self.assertIsNotNone(cross_year["cards"]["premium"])
        self.assertIsNone(cross_year["cards"]["share_change_pp"])
        self.assertEqual(len(cross_year["evolution"]), 24)
        self.assertEqual(self.analyze(start="202510", end="202609")["evolution"], [])

    def test_continuous_market_share_across_years(self):
        cases = (
            ("202511", "202603", ["202511", "202512", "202601", "202602", "202603"]),
            ("202410", "202502", ["202410", "202411", "202412", "202501", "202502"]),
            ("202510", "202609", ["202510", "202511", "202512"]
             + [f"2026{month:02}" for month in range(1, 10)]),
        )
        for start, end, axis in cases:
            with self.subTest(start=start, end=end):
                result = self.analyze(start=start, end=end, metric="share")
                for series, offset in (("current", 0), ("previous", 1)):
                    rows = [row for row in result["evolution"] if row["series"] == series]
                    self.assertEqual([row["axis"] for row in rows], axis)
                    self.assertEqual(
                        [f'{row["year"]:04}{row["month"]:02}' for row in rows],
                        [f"{int(month[:4]) - offset:04}{month[4:]}" for month in axis],
                    )
                    self.assertTrue(all(row["value"] is not None for row in rows))
                expected = self.database.execute("""
                    WITH basket AS (
                        SELECT ramo FROM fato_premios_uf
                        WHERE coenti = '05631' AND damesano BETWEEN ? AND ?
                        GROUP BY ramo HAVING abs(sum(premio_direto)) > 0.01
                    )
                    SELECT 100 * sum(premio_direto) FILTER (WHERE coenti = '05631')
                               / sum(premio_direto)
                    FROM fato_premios_uf JOIN basket USING (ramo)
                    WHERE damesano = ?
                """, [start, end, start]).fetchone()[0]
                first = next(row for row in result["evolution"] if row["series"] == "current")
                self.assertAlmostEqual(first["value"], expected, places=10)

    def test_continuous_history_has_nulls_where_comparison_is_unavailable(self):
        result = self.analyze(start="201911", end="202002", metric="share")
        previous = [row for row in result["evolution"] if row["series"] == "previous"]
        self.assertEqual([row["value"] is None for row in previous], [True, True, False, False])
        no_data = self.analyze(start="202609", end="202609", entities=(), metric="share")
        self.assertEqual(no_data["evolution"], [])

    def test_metrics_preserve_cards_and_history_context(self):
        margin = self.analyze()
        share = self.analyze(metric="share")
        claims = self.analyze(metric="sinistralidade")
        self.assertEqual(share["cards"], margin["cards"])
        self.assertEqual(claims["cards"], margin["cards"])
        self.assertEqual(len(share["ranking"]), 6)
        self.assertTrue(any(row["selected"] for row in share["ranking"]))
        ranked = [row["rank"] for row in share["ranking"] if not row["selected"]]
        self.assertEqual(ranked, [1, 2, 3, 4, 5])
        self.assertEqual([r["value"] is None for r in margin["evolution"]],
                         [True] * 9 + [False] * 9)
        self.assertEqual(sum(r["value"] is not None for r in share["evolution"]), 18)
        jan25 = next(r["value"] for r in share["evolution"] if (r["year"], r["month"]) == (2025, 1))
        self.assertAlmostEqual(jan25, 2.68216302, places=7)
        self.assertEqual(len(margin["diagnosis"]["rows"]), 5)
        self.assertAlmostEqual(margin["diagnosis"]["total"]["weightPct"], 100)
        self.assertAlmostEqual(margin["diagnosis"]["total"]["indicatorPct"], 53.3577173, places=6)
        self.assertAlmostEqual(margin["diagnosis"]["total"]["marketPct"], 25.8441099, places=6)

    def test_catalog_and_bad_filters(self):
        catalog = self.service.catalog
        self.assertEqual(catalog["defaults"], DEFAULTS)
        self.assertEqual(catalog["months"][0]["code"], "201901")
        self.assertEqual(catalog["months"][-1]["code"], "202609")
        self.assertIn("05631", catalog["memberships"]["00230"])
        for params in ({"entity": ["UNKNOWN"]}, {"start": ["202700"]}, {"metric": ["other"]},
                       {"group": ["UNKNOWN"]}, {"end": ["202601", "202602"]}):
            with self.subTest(params=params), self.assertRaises(ValueError):
                self.service.analyze(params)

    def test_cross_filter_from_diagnosis_recalculates_other_visuals(self):
        base = self.analyze()
        result = self.service.analyze({
            "start": ["202601"], "end": ["202609"], "entity": ["05631"],
            "metric": ["margem"], "selected_branch_group": ["10"],
        })
        cards = result["cards"]
        self.assertEqual(cards["premium"], Decimal("1616402370.91"))
        self.assertEqual(cards["position"], 2)
        self.assertEqual(cards["competitor_count"], 23)
        self.assertEqual(cards["next_distance"], Decimal("148584007.27"))
        self.assertEqual(cards["leader_distance"], cards["next_distance"])
        self.assertEqual(format(cards["share"] * 100, ".2f"), "24.37")
        self.assertEqual(base["diagnosis"], result["diagnosis"])
        self.assertNotEqual(base["evolution"], result["evolution"])
        self.assertTrue(any(row.get("highlight_value") is not None for row in result["ranking"]))

    def test_cross_filter_from_rank_preserves_basket_and_source(self):
        base = self.analyze()
        result = self.service.analyze({
            "start": ["202601"], "end": ["202609"], "entity": ["05631"],
            "metric": ["margem"], "selected_insurer": ["05886"],
        })
        self.assertEqual(result["cards"]["position"], 2)
        self.assertEqual(result["cards"]["premium"], base["cards"]["premium"])
        self.assertEqual(result["cards"]["share"], base["cards"]["share"])
        self.assertEqual(result["ranking"], base["ranking"])
        self.assertEqual(result["evolution"], base["evolution"])
        self.assertAlmostEqual(result["diagnosis"]["total"]["indicatorPct"], 29.78567, places=5)
        self.assertAlmostEqual(result["diagnosis"]["total"]["marketPct"], 24.586917, places=5)


if __name__ == "__main__":
    unittest.main()
