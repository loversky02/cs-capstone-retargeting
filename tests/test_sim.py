"""MuJoCo demo checks. Skipped when the optional sim requirements are not installed."""

import unittest

try:
    import mujoco  # noqa: F401
    HAVE_SIM = True
except ImportError:
    HAVE_SIM = False


@unittest.skipUnless(HAVE_SIM, "pip install -r requirements-sim.txt")
class SimTest(unittest.TestCase):
    def test_grasp_succeeds_on_true_pose_and_fails_when_offset(self):
        from sim.grasp import run_grasp
        from sim.scene import Cube
        self.assertTrue(run_grasp(Cube(), (0.55, 0.0, 0.0))["success"])
        self.assertFalse(run_grasp(Cube(), (0.55, 0.035, 0.0))["success"])

    def test_episode_sampling_is_deterministic(self):
        from sim.teleguide import sample_episode
        self.assertEqual(sample_episode(7)[2], sample_episode(7)[2])

    def test_auroc_extremes(self):
        import numpy as np

        from sim.teleguide import auroc
        pos = np.array([False, False, True, True])
        self.assertEqual(auroc(np.array([0.1, 0.2, 0.8, 0.9]), pos), 1.0)
        self.assertEqual(auroc(np.array([0.9, 0.8, 0.2, 0.1]), pos), 0.0)

    def test_ur5e_ik_reaches_inside_and_not_outside_workspace(self):
        import numpy as np

        from sim.retarget import retarget
        from sim.scene import down_quat
        near = retarget([(np.array([0.45, 0.1, 0.15]), down_quat(0.3))], restarts=8)[1][0]
        far = retarget([(np.array([1.3, 0.0, 0.1]), down_quat(0.0))], restarts=2)[1][0]
        self.assertLess(near["err_mm"], 5)
        self.assertGreater(far["err_mm"], 100)


if __name__ == "__main__":
    unittest.main()
