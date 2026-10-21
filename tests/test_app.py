import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
ROSTER = [
    "Neya", "Lieh-Shan Yen", "Urag", "Emrys", "Forondil", "Tobin",
    "Bakshi", "Theodore", "Mardok", "Freya", "Thanatil", "Shang Ying",
]


class LegionTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
        self.assertFalse(self.app.exception)

    def select_roster(self, roster):
        self.app.multiselect[0].set_value(roster).run()

    def optimize(self):
        next(button for button in self.app.button if button.label == "Optimize").click().run()
        self.assertFalse(self.app.exception)
        self.assertFalse(self.app.error)
        return self.app.session_state.optimization_results

    def assert_legions(self, results, count, heroes):
        self.assertTrue(results)
        for _, marches in results:
            self.assertEqual(len(marches), count)
            used_heroes = [hero for march in marches for hero in (march.main, march.deputy)]
            self.assertCountEqual(used_heroes, heroes)
            self.assertEqual(len(used_heroes), len(set(used_heroes)))

    def test_toggle_updates_slots_and_clears_results(self):
        self.assertFalse(self.app.toggle[0].value)
        self.assertEqual(len(self.app.selectbox), 10)
        self.select_roster(ROSTER[:10])
        self.assert_legions(self.optimize(), 5, ROSTER[:10])

        self.app.toggle[0].set_value(True).run()
        self.assertEqual(len(self.app.selectbox), 12)
        self.assertFalse(self.app.session_state.optimization_results)
        self.select_roster(ROSTER)
        self.assert_legions(self.optimize(), 6, ROSTER)

        self.app.toggle[0].set_value(False).run()
        self.assertEqual(len(self.app.selectbox), 10)
        self.assertFalse(self.app.session_state.optimization_results)
        self.assertTrue(self.app.button[0].disabled)

    def test_capacity_includes_generic_deputies(self):
        self.select_roster(ROSTER[:10])
        self.app.number_input[1].set_value(2).run()
        self.assertTrue(self.app.button[0].disabled)
        self.assertIn("at most 10 heroes", self.app.warning[0].value)

        self.app.toggle[0].set_value(True).run()
        self.assertFalse(self.app.button[0].disabled)
        self.assert_legions(self.optimize(), 6, ROSTER[:10] + ["Generic 1", "Generic 2"])

        self.app.number_input[1].set_value(3).run()
        self.assertTrue(self.app.button[0].disabled)
        self.assertIn("at most 12 heroes", self.app.warning[0].value)
        self.assertFalse(self.app.session_state.optimization_results)

    def test_sixth_pair_can_be_forced(self):
        self.app.toggle[0].set_value(True).run()
        self.select_roster(ROSTER)
        self.app.selectbox(key="fp6m").select("Thanatil")
        self.app.selectbox(key="fp6d").select("Shang Ying").run()
        results = self.optimize()
        self.assert_legions(results, 6, ROSTER)
        for _, marches in results:
            self.assertIn(("Thanatil", "Shang Ying"), [(m.main, m.deputy) for m in marches])

        self.app.selectbox(key="fp6d").select("None").run()
        for _, marches in self.optimize():
            self.assertIn("Thanatil", [m.main for m in marches])

    def test_all_six_forced_pairs_and_duplicate_validation(self):
        self.app.toggle[0].set_value(True).run()
        self.select_roster(ROSTER)
        pairs = list(zip(ROSTER[::2], ROSTER[1::2]))
        for slot, (main, deputy) in enumerate(pairs, 1):
            self.app.selectbox(key=f"fp{slot}m").select(main)
            self.app.selectbox(key=f"fp{slot}d").select(deputy)
        self.app.run()
        results = self.optimize()
        self.assert_legions(results, 6, ROSTER)
        self.assertEqual([(m.main, m.deputy) for m in results[0][1]], pairs)

        self.app.selectbox(key="fp6m").select(ROSTER[0]).run()
        next(button for button in self.app.button if button.label == "Optimize").click().run()
        self.assertIn("Duplicate heroes", self.app.error[0].value)
        self.assertFalse(self.app.session_state.optimization_results)

    def test_new_heroes_skill_levels_and_main_talents(self):
        self.select_roster(["Thanatil", "Shang Ying"])
        for main, deputy, talent, bonus in [
            ("Thanatil", "Shang Ying", "Mighty Power", 0.0),
            ("Shang Ying", "Thanatil", "Shield of Stability", -2.0),
        ]:
            self.app.selectbox(key="fp1m").select(main)
            self.app.selectbox(key="fp1d").select(deputy).run()
            for level, speed in enumerate([0.0, 2.0, 4.0, 6.0, 8.0, 10.0]):
                with self.subTest(main=main, level=level):
                    self.app.number_input(key=f"lvl_{main}").set_value(level)
                    self.app.number_input(key=f"lvl_{deputy}").set_value(level).run()
                    march = self.optimize()[0][1][0]
                    self.assertEqual(
                        march.skill_breakdown,
                        f"Main({speed}) + Dep({speed}) + {talent}({bonus})",
                    )

    def test_new_heroes_talent_trees_reach_expected_speed(self):
        self.select_roster(["Thanatil", "Shang Ying"])
        for main, deputy, target, speed_tree in [
            ("Thanatil", "Shang Ying", 55.0, "Pvp(20%)"),
            ("Shang Ying", "Thanatil", 53.0, "Tank(20%)"),
        ]:
            with self.subTest(main=main):
                self.app.selectbox(key="fp1m").select(main)
                self.app.selectbox(key="fp1d").select(deputy)
                self.app.number_input[0].set_value(target).run()
                march = self.optimize()[0][1][0]
                self.assertEqual(march.total_speed, target)
                self.assertIn("Cavalry(15%)", march.talent_config)
                self.assertIn(speed_tree, march.talent_config)


if __name__ == "__main__":
    unittest.main()
