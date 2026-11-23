"""Regression cases for Fusão e Aquisição with the curated SUSEP data."""

from decimal import Decimal
import json
from threading import Thread
import unittest
from urllib.request import urlopen
from wsgiref.simple_server import make_server

from ma_views import _Scope, _cards, get_ma
from server import Service, create_app, find_data_dir, open_database


class MergerParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = open_database(find_data_dir())
        cls.addClassCleanup(cls.database.close)

    def scenario(self, **changes):
        filters = {
            "start": "202601", "end": "202609", "insurers": ("05631",), "group": "00230",
            "company_a": "05177", "company_b": "06238",
        }
        return get_ma(self.database, **{**filters, **changes})

    def test_http_delivers_shared_entrypoint_ma_assets_and_real_data(self):
        with make_server("127.0.0.1", 0, create_app(Service(self.database))) as server:
            worker = Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                origin = f"http://127.0.0.1:{server.server_port}"
                for path, expected in (
                    ("/", b'href="./ma.css"'),
                    ("/app.js", b'from "./ma.js"'),
                    ("/ma.js", b"export function mountMa"),
                    ("/ma.css", b".ma-layout"),
                ):
                    with self.subTest(path=path), urlopen(origin + path, timeout=10) as response:
                        self.assertIn(expected, response.read())
                with urlopen(origin + "/api/catalog", timeout=10) as response:
                    defaults = json.load(response)["defaults"]
                query = "start=202601&end=202609&entity=05631&company_a=05177&company_b=06238"
                with urlopen(origin + "/api/fusao-aquisicao?" + query, timeout=10) as response:
                    result = json.load(response)
            finally:
                server.shutdown()
                worker.join()
        self.assertEqual(defaults["ma"], {"companyA": "05177", "companyB": "06238"})
        self.assertEqual(result["cards"]["combinedPremium"], "9906494701.26")
        self.assertEqual((len(result["uf"]["rows"]), len(result["branches"]["rows"])), (27, 7))

    def test_saved_caixa_allianz_mapfre_matches_cards_and_totals(self):
        result = self.scenario()
        cards = result["cards"]
        self.assertEqual(
            (cards["referencePositionBefore"], cards["referencePositionAfter"],
             cards["positionImpact"], cards["combinedPosition"]),
            (12, 11, 1, 2),
        )
        self.assertEqual(cards["combinedPremium"], Decimal("9906494701.26"))
        market = Decimal("84243304989.16")
        self.assertEqual(cards["combinedShare"], cards["combinedPremium"] / market)
        self.assertEqual(format(cards["hhiBefore"], ".9f"), "691.740632158")
        self.assertEqual(format(cards["hhiImpact"], ".9f"), "62.019361200")
        self.assertEqual(cards["hhiAfter"], cards["hhiBefore"] + cards["hhiImpact"])
        self.assertEqual(format(cards["hhiAfter"], ".2f"), "753.76")

        uf = result["uf"]
        self.assertEqual(len(uf["rows"]), 27)
        self.assertEqual(uf["total"]["marketPremium"], market)
        self.assertNotEqual(uf["total"]["marketPremium"], sum(row["marketPremium"] for row in uf["rows"]))
        sp = next(row for row in uf["rows"] if row["code"] == "SP")
        self.assertEqual(sp["combinedPremium"], Decimal("3642024864.99"))
        self.assertEqual(sp["marketPremium"], Decimal("32951718234.21"))
        self.assertEqual(format(sp["hhiImpact"], ".3f"), "61.080")

        branches = result["branches"]
        self.assertEqual([row["code"] for row in branches["rows"]], ["05", "01", "13", "03", "10", "07", "08"])
        auto = branches["rows"][0]
        self.assertEqual(auto["referencePremium"], Decimal("500253789.70"))
        self.assertEqual(auto["premiumA"], Decimal("5420451903.02"))
        self.assertEqual(auto["premiumB"], Decimal("2258666623.24"))
        self.assertEqual(auto["combinedPremium"], Decimal("7679118526.26"))
        self.assertEqual(auto["marketPremium"], Decimal("40231285324.31"))
        self.assertEqual(auto["competitivePressure"], auto["combinedPremium"] / auto["referencePremium"])
        self.assertEqual(format(auto["hhiImpact"], ".3f"), "151.283")
        self.assertEqual(branches["rows"][-1]["referencePremium"], 0)
        self.assertIsNone(branches["rows"][-1]["marketPremium"])

    def test_state_click_preserves_source_table_and_uses_distinct_card_basket(self):
        baseline = self.scenario()
        selected = self.scenario(selected_uf="AC")
        self.assertEqual(selected["uf"], baseline["uf"])
        self.assertNotEqual(selected["branches"], baseline["branches"])

        cards = selected["cards"]
        ac = next(row for row in selected["uf"]["rows"] if row["code"] == "AC")
        self.assertEqual(cards["combinedPremium"], ac["combinedPremium"])
        self.assertEqual(ac["combinedPremium"], Decimal("12870084.99"))
        self.assertEqual(ac["marketPremium"], Decimal("53131403.45"))
        self.assertEqual(format(ac["combinedShare"] * 100, ".2f"), "24.22")
        self.assertEqual(format(ac["hhiImpact"], ".3f"), "0.328")
        self.assertEqual(format(cards["combinedShare"] * 100, ".2f"), "20.91")
        self.assertEqual(format(cards["hhiBefore"], ".2f"), "879.44")
        self.assertEqual(format(cards["hhiAfter"], ".2f"), "879.68")
        self.assertEqual(format(cards["hhiImpact"], ".3f"), "0.244")
        self.assertEqual(
            (cards["referencePositionBefore"], cards["referencePositionAfter"], cards["combinedPosition"]),
            (7, 6, 1),
        )
        self.assertEqual(selected["branches"]["total"]["marketPremium"], ac["marketPremium"])

    def test_branch_click_preserves_source_table_and_filters_states(self):
        baseline = self.scenario()
        selected = self.scenario(selected_branch_group="05")
        self.assertEqual(selected["branches"], baseline["branches"])
        self.assertNotEqual(selected["uf"], baseline["uf"])
        cards = selected["cards"]
        self.assertEqual(cards["combinedPremium"], Decimal("7679118526.26"))
        self.assertEqual(selected["uf"]["total"]["marketPremium"], Decimal("40231285324.31"))
        self.assertEqual(format(cards["combinedShare"] * 100, ".2f"), "19.09")
        self.assertEqual(format(cards["hhiImpact"], ".3f"), "151.283")
        self.assertEqual((cards["referencePositionBefore"], cards["referencePositionAfter"]), (10, 9))

    def test_identical_or_missing_companies_preserve_prior_cards_and_individual_premiums(self):
        for company_b in ("05177", None):
            with self.subTest(company_b=company_b):
                result = self.scenario(company_b=company_b)
                cards = result["cards"]
                self.assertEqual(cards["referencePositionBefore"], 12)
                self.assertEqual(format(cards["hhiBefore"], ".2f"), "691.74")
                self.assertTrue(all(value is None for key, value in cards.items()
                                    if key not in {"referencePositionBefore", "hhiBefore"}))
                total = result["branches"]["total"]
                self.assertEqual(total["premiumA"], Decimal("6542993339.14"))
                self.assertEqual(total["premiumB"], total["premiumA"] if company_b else None)
                self.assertIsNone(total["combinedPremium"])
                self.assertEqual(total["marketPremium"], Decimal("84243304989.16"))

    def test_blank_zero_and_negative_amounts_have_measure_specific_hhi_rules(self):
        fixtures = (
            ("01848", None, "6542993339.14", Decimal(0)),
            ("03727", Decimal(0), "6542993339.14", Decimal(0)),
            ("01864", Decimal("-103118.68"), "6542890220.46", None),
        )
        for company_b, amount_b, combined, local_delta in fixtures:
            with self.subTest(company_b=company_b):
                result = self.scenario(company_b=company_b)
                self.assertEqual(result["cards"]["combinedPremium"], Decimal(combined))
                self.assertIsNone(result["cards"]["hhiAfter"])
                self.assertIsNone(result["cards"]["hhiImpact"])
                self.assertEqual(result["branches"]["total"]["premiumB"], amount_b)
                self.assertEqual(result["branches"]["total"]["hhiImpact"], local_delta)

    def test_reference_in_merger_and_multiple_references(self):
        cards = self.scenario(company_a="05631")["cards"]
        self.assertEqual((cards["referencePositionBefore"], cards["referencePositionAfter"],
                          cards["combinedPosition"], cards["positionImpact"]), (12, 6, 6, 6))
        self.assertEqual(cards["combinedPremium"], Decimal("5567754505.37"))

        multi = self.scenario(insurers=("05631", "04707"))["cards"]
        self.assertIsNone(multi["referencePositionBefore"])
        self.assertIsNone(multi["referencePositionAfter"])
        self.assertIsNone(multi["positionImpact"])
        self.assertIsNotNone(multi["combinedPremium"])

    def test_group_without_individual_reference_keeps_merger_and_hhi_cards(self):
        cards = self.scenario(insurers=())["cards"]
        self.assertIsNone(cards["referencePositionBefore"])
        self.assertIsNone(cards["referencePositionAfter"])
        self.assertIsNone(cards["positionImpact"])
        self.assertEqual(cards["combinedPremium"], Decimal("10577242344.31"))
        self.assertEqual(format(cards["hhiImpact"], ".3f"), "9.643")
        self.assertEqual(cards["hhiAfter"], cards["hhiBefore"] + cards["hhiImpact"])

    def test_no_data_and_reversed_period(self):
        for result in (
            self.scenario(start="202609", end="202609", insurers=()),
            self.scenario(insurers=(), group=None),
            self.scenario(start="202609", end="202601"),
        ):
            self.assertTrue(all(value is None for value in result["cards"].values()))
            self.assertEqual(result["uf"]["rows"], [])
            self.assertEqual(result["branches"]["rows"], [])

    def test_combined_rank_does_not_count_tie_and_hhi_uses_signed_market(self):
        premiums = {code: Decimal(amount) for code, amount in (
            ("R", "80"), ("A", "60"), ("B", "50"), ("C", "110"), ("D", "-100"),
        )}
        cards = _cards(_Scope(reference=Decimal(80), fixed=premiums, local=premiums), "R", "A", "B", True)
        self.assertEqual(cards["combinedPosition"], 1)
        self.assertEqual((cards["referencePositionBefore"], cards["referencePositionAfter"]), (2, 3))
        self.assertEqual(cards["positionImpact"], -1)
        self.assertEqual(cards["combinedShare"], Decimal("0.55"))
        self.assertEqual(cards["hhiBefore"], Decimal(6150))
        self.assertEqual(cards["hhiImpact"], Decimal(1500))
        self.assertEqual(cards["hhiAfter"], Decimal(7650))

    def test_reference_position_before_handles_fractional_cent_ties(self):
        scope = _Scope(reference=Decimal("100.003"), fixed={
            "R": Decimal("100.003"),
            "C": Decimal("100.004"),
        })
        self.assertEqual(_cards(scope, "R", None, None, False)["referencePositionBefore"], 1)
        scope.fixed["R"] = Decimal("0.004")
        self.assertIsNone(_cards(scope, "R", None, None, False)["referencePositionBefore"])

    def test_negative_combined_premium_can_leave_reference_rank_defined(self):
        amounts = {code: Decimal(amount) for code, amount in (
            ("R", "100"), ("A", "-50"), ("B", "-30"), ("C", "160"),
        )}
        cards = _cards(_Scope(reference=Decimal(100), fixed=amounts, local=amounts), "R", "A", "B", True)
        self.assertEqual(cards["combinedPremium"], Decimal(-80))
        self.assertEqual(cards["combinedShare"], Decimal(-80) / Decimal(180))
        self.assertIsNone(cards["combinedPosition"])
        self.assertEqual((cards["referencePositionBefore"], cards["referencePositionAfter"]), (2, 2))
        self.assertIsNotNone(cards["hhiBefore"])
        self.assertIsNone(cards["hhiImpact"])
        self.assertIsNone(cards["hhiAfter"])


if __name__ == "__main__":
    unittest.main()
