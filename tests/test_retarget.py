import unittest

from examples.retarget import forward, inverse, run


class RetargetTest(unittest.TestCase):
    def test_inverse_reconstructs_reachable_position(self):
        target = forward(-0.2, 1.3)
        joints, outside = inverse(*target)
        self.assertFalse(outside)
        for original, reconstructed in zip(target, forward(*joints)):
            self.assertAlmostEqual(original, reconstructed)

    def test_unreachable_target_is_flagged(self):
        joints, outside = inverse(1.0, 0.0)
        self.assertTrue(outside)
        self.assertAlmostEqual(forward(*joints)[0], 0.7)

    def test_oracle_search_respects_budget_and_reduces_error(self):
        cases = [run(budget) for budget in range(4)]
        self.assertEqual([case["used_segments"] for case in cases], [0, 1, 2, 3])
        self.assertGreater(cases[0]["joint_limit_violation_frames"], 0)
        for previous, current in zip(cases, cases[1:]):
            self.assertLess(current["position_rmse_m"], previous["position_rmse_m"])
        self.assertEqual(cases[-1]["position_rmse_m"], 0)
        self.assertEqual(cases[-1]["joint_limit_violation_frames"], 0)

    def test_rejects_budgets_outside_scenario(self):
        for budget in (-1, 4):
            with self.subTest(budget=budget), self.assertRaises(ValueError):
                run(budget)


class VisualizeTest(unittest.TestCase):
    def test_demo_embeds_every_budget_and_matches_cli_metrics(self):
        import json
        from examples.visualize import build_payload, render
        payload = build_payload()
        self.assertEqual([r["result"] for r in payload["runs"]], [run(b) for b in range(4)])
        html = render(payload)
        self.assertNotIn("__DATA__", html)
        self.assertNotIn("http://", html.replace("http://www.w3.org/2000/svg", ""))
        self.assertNotIn("https://", html)
        start = html.index("const DATA = ") + len("const DATA = ")
        self.assertEqual(json.loads(html[start:html.index(";\n", start)])["segments"],
                         [list(s) for s in payload["segments"]])
