"""Parity checks for the Visão por UF measures, using the audited SUSEP snapshot."""

from decimal import Decimal
import json
from threading import Thread
import unittest
from urllib.request import urlopen
from wsgiref.simple_server import make_server

from server import Service, create_app, find_data_dir, open_database
from tools.check_uf_map import DEFAULT_MAP, UF_CODES, check_asset
from uf_views import get_uf_analysis


def by_uf(result, code):
    return next(state for state in result["states"] if state["uf"] == code)


class MapAssetParity(unittest.TestCase):
    def test_build_requires_provenance_and_all_official_codes(self):
        asset = json.loads(DEFAULT_MAP.read_text(encoding="utf-8"))
        check_asset(asset)
        with self.assertRaisesRegex(ValueError, "Proveniência"):
            check_asset({**asset, "metadata": {}})
        paths = asset["paths"]
        with self.assertRaisesRegex(ValueError, "Código de UF"):
            check_asset({**asset, "paths": [paths[1], *paths[1:]]})


class StateParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = open_database(find_data_dir())
        cls.addClassCleanup(cls.database.close)

    def analyze(self, *, start="202601", end="202609", insurers=("05631",),
                group="00230", selected_uf=None, selected_insurer=None):
        return get_uf_analysis(
            self.database, start=start, end=end, insurers=list(insurers),
            group=group, selected_uf=selected_uf, selected_insurer=selected_insurer,
        )

    def assert_measure(self, result, numerator, denominator):
        expected = Decimal(numerator) / Decimal(denominator) * 100
        self.assertAlmostEqual(result, expected, places=12)

    def test_http_route_and_map_for_browser_parameters(self):
        with make_server("127.0.0.1", 0, create_app(Service(self.database))) as server:
            worker = Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                origin = f"http://127.0.0.1:{server.server_port}"
                query = "start=202601&end=202609&group=00230&entity=05631"
                with urlopen(f"{origin}/api/visao-uf?{query}", timeout=10) as response:
                    result = json.load(response)
                with urlopen(f"{origin}/uf-map.json", timeout=10) as response:
                    geometry = json.load(response)
            finally:
                server.shutdown()
                worker.join()
        self.assertEqual(result["cards"]["coverage"], 27)
        self.assertIsNone(result["cards"]["leadership"])
        self.assertEqual(result["cards"]["top3"], 0)
        self.assertEqual(result["cards"]["bestUf"], "PI")
        self.assertTrue(result["baseRanking"])
        self.assertTrue(any(state["changePp"] is not None for state in result["states"]))
        self.assertEqual(len(geometry["paths"]), 27)
        self.assertEqual({path["code"]: path["uf"] for path in geometry["paths"]}, UF_CODES)
        self.assertEqual({path["uf"] for path in geometry["paths"]},
                         {state["uf"] for state in result["states"]})
        self.assertEqual(geometry["metadata"]["dataset"], "BR_UF_2023")

    def test_caixa_headline_values_and_map_scope(self):
        result = self.analyze()
        self.assertEqual(len(result["states"]), 27)
        self.assertEqual(len({state["uf"] for state in result["states"]}), 27)
        cards = result["cards"]
        self.assertEqual(cards["coverage"], 27)
        self.assertEqual(cards["top3"], 0)
        self.assertIsNone(cards["leadership"])
        self.assertEqual(cards["bestUf"], "PI")
        self.assertEqual(f'{cards["bestShare"]:.2f}', "8.67")

        piaui = by_uf(result, "PI")
        self.assertEqual(piaui["premium"], Decimal("18837475.83"))
        self.assertEqual(piaui["marketPremium"], Decimal("217156983.25"))
        self.assert_measure(piaui["share"], "18837475.83", "217156983.25")
        self.assert_measure(piaui["previousShare"], "18479651.77", "207588306.12")
        self.assertAlmostEqual(piaui["changePp"], Decimal("-0.227478784675945"), places=12)
        self.assertEqual(piaui["position"], 5)
        # The PBIR groups the map by Estado Mapa, while the DAX position
        # requires ISINSCOPE on dim_uf[uf] or fato_premios_uf[uf].
        self.assertIsNone(piaui["mapPosition"])
        self.assertEqual(cards["bestShare"], piaui["share"])

    def test_uf_selection_scopes_ranking_without_refitting_basket(self):
        brazil = self.analyze()
        selected = self.analyze(selected_uf="PI")
        self.assertEqual(selected["cards"], brazil["cards"])
        self.assertEqual(selected["states"], brazil["states"])
        self.assertEqual(selected["selection"], "PI")
        self.assertEqual(selected["rankingTitle"], "Ranking Competitivo | Piaui")
        self.assertEqual(brazil["rankingTitle"], "Ranking Competitivo | Brasil")

        self.assertEqual(brazil["ranking"][0]["id"], "05886")
        self.assertEqual(brazil["ranking"][0]["premium"], Decimal("14019076032.30"))
        self.assertEqual(selected["ranking"][0]["id"], "05177")
        self.assertEqual(selected["ranking"][0]["premium"], Decimal("35628216.56"))
        self.assertEqual(selected["ranking"][4]["id"], "05631")
        self.assertEqual(selected["ranking"][4]["premium"], Decimal("18837475.83"))
        self.assertTrue(selected["ranking"][4]["selected"])
        # Porto operates in only a subset of the reference's positive branches.
        # Its negative state premium stays on the signed-ranking axis.
        self.assertEqual(
            next(row["premium"] for row in selected["ranking"] if row["id"] == "05886"),
            Decimal("-535.00"),
        )
        self.assertTrue(any(row["premium"] == 0 for row in selected["ranking"]))

    def test_visual_selections_keep_national_ranking_and_overlay_state_values(self):
        brazil = self.analyze()
        piaui = self.analyze(selected_uf="PI")
        state_premiums = {row["id"]: row["premium"] for row in piaui["ranking"]}

        self.assertEqual(piaui["baseRankingTitle"], "Ranking Competitivo | Brasil")
        self.assertEqual(len(piaui["baseRanking"]), len(brazil["ranking"]))
        for base_row, highlighted in zip(brazil["ranking"], piaui["baseRanking"], strict=True):
            self.assertEqual(highlighted, {
                **base_row,
                "highlighted": True,
                "highlightPremium": state_premiums.get(base_row["id"]),
            })
        self.assertEqual(piaui["baseRanking"][0]["id"], "05886")
        self.assertEqual(piaui["baseRanking"][0]["highlightPremium"], Decimal("-535.00"))

        selected = self.analyze(selected_insurer="05886")
        self.assertEqual(selected["cards"], brazil["cards"])
        self.assertEqual(selected["states"], brazil["states"])
        self.assertEqual(selected["baseRankingTitle"], brazil["baseRankingTitle"])
        self.assertEqual(selected["baseRanking"], [
            {**row, "active": row["id"] == "05886"} for row in brazil["ranking"]
        ])

    def test_brasilprev_ma_distinguishes_nationwide_cesta_from_notebook(self):
        result = self.analyze(start="202510", end="202609", insurers=("04707",),
                              group=None, selected_uf="MA")
        cards = result["cards"]
        self.assertEqual((cards["coverage"], cards["leadership"], cards["top3"]), (27, 24, 27))
        self.assertEqual(cards["bestUf"], "RR")
        self.assertEqual(f'{cards["bestShare"]:.2f}', "75.44")
        maranhao = by_uf(result, "MA")
        self.assertEqual(maranhao["premium"], Decimal("848160081.08"))
        self.assertEqual(maranhao["marketPremium"], Decimal("1702204861.86"))
        self.assert_measure(maranhao["share"], "848160081.08", "1702204861.86")
        self.assert_measure(maranhao["previousShare"], "769186933.11", "1638211428.01")
        self.assertEqual(f'{maranhao["changePp"]:.2f}', "2.87")
        self.assertEqual(maranhao["position"], 1)
        self.assertEqual(result["ranking"][0]["id"], "04707")

    def test_missing_history_leaves_prior_and_change_blank(self):
        result = self.analyze(start="201901", end="201901", insurers=("04707",), group=None)
        cards = result["cards"]
        self.assertEqual((cards["coverage"], cards["leadership"], cards["top3"]), (27, 21, 27))
        self.assertTrue(all(state["previousShare"] is None for state in result["states"]))
        self.assertTrue(all(state["changePp"] is None for state in result["states"]))
        self.assert_measure(by_uf(result, "PI")["share"], "23792725.12", "39614005.14")

    def test_overlapping_previous_and_current_ranges_keep_both_sums(self):
        result = self.analyze(start="202401", end="202609")
        piaui = by_uf(result, "PI")
        self.assertEqual(piaui["premium"], Decimal("69181733.83"))
        self.assertEqual(piaui["marketPremium"], Decimal("743652928.16"))
        self.assert_measure(piaui["previousShare"], "70308733.16", "747539440.82")

    def test_signed_and_zero_reference_premiums_have_distinct_prior_rules(self):
        result = self.analyze(start="202603", end="202603", insurers=("06122",), group=None)
        amapa = by_uf(result, "AP")
        self.assert_measure(amapa["share"], "167659.26", "1308078.73")
        self.assert_measure(amapa["previousShare"], "-1914.53", "403260.96")
        self.assertLess(amapa["previousShare"], 0)
        self.assertEqual(amapa["changePp"], amapa["share"] - amapa["previousShare"])

        acre = by_uf(result, "AC")
        self.assert_measure(acre["share"], "1851.84", "1710405.84")
        self.assertEqual(acre["previousShare"], 0)
        self.assertEqual(acre["changePp"], acre["share"])

        rio_grande_do_norte = by_uf(result, "RN")
        self.assertEqual(rio_grande_do_norte["premium"], Decimal("-11650.97"))
        self.assertIsNone(rio_grande_do_norte["share"])
        self.assertIsNone(rio_grande_do_norte["position"])
        self.assertIsNone(rio_grande_do_norte["changePp"])
        self.assertGreater(rio_grande_do_norte["previousShare"], 0)

    def test_group_uses_historical_membership_and_single_owner_cards(self):
        august = self.analyze(start="202608", end="202608", insurers=(), selected_uf="PI")
        september = self.analyze(start="202609", end="202609", insurers=(), selected_uf="PI")
        self.assertEqual(august["ranking"][0]["id"], "04707")
        self.assertEqual(august["ranking"][0]["premium"], Decimal("51086366.91"))
        self.assertEqual(september["ranking"], [])
        for result in (august, september):
            self.assertIsNone(result["cards"]["coverage"])
            self.assertIsNone(result["cards"]["leadership"])
            self.assertEqual(result["cards"]["top3"], 0)
            self.assertIsNone(result["cards"]["bestShare"])
            self.assertTrue(all(state["share"] is None for state in result["states"]))
        self.assertEqual(self.analyze(group=None), self.analyze())
        self.assertGreater(self.analyze(start="202609")["cards"]["coverage"], 0)

    def test_multi_selection_and_no_reference_do_not_invent_share(self):
        multiple = self.analyze(insurers=("05631", "04707"), group=None)
        self.assertTrue(multiple["ranking"])
        no_reference = self.analyze(insurers=(), group=None)
        self.assertEqual(no_reference["ranking"], [])
        for result in (multiple, no_reference):
            self.assertIsNone(result["cards"]["coverage"])
            self.assertIsNone(result["cards"]["leadership"])
            self.assertEqual(result["cards"]["top3"], 0)
            self.assertIsNone(result["cards"]["bestUf"])
            self.assertTrue(all(state["share"] is None for state in result["states"]))
            self.assertTrue(all(state["changePp"] is None for state in result["states"]))

    def test_inverted_period_preserves_blank_measures(self):
        result = self.analyze(start="202609", end="202601")
        self.assertEqual(result["ranking"], [])
        self.assertEqual(result["cards"], {
            "coverage": None, "leadership": None, "top3": 0, "bestUf": None, "bestShare": None,
        })
        self.assertTrue(all(state["premium"] is None for state in result["states"]))


if __name__ == "__main__":
    unittest.main()
