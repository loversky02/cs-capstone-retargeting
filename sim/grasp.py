"""Scripted top-down Panda grasp that acts on a *believed* cube pose, not the true one."""

import mujoco
import numpy as np

from sim.scene import GRIPPER_CLOSED, GRIPPER_OPEN, PANDA_ARM_JOINTS, down_quat, panda_scene, solve_ik

LIFT_SUCCESS_M = 0.08


def _move(model, data, joints, target, gripper, seconds, recorder=None, caption="", color=(255, 255, 255)):
    """Interpolate joint position targets and step physics, snapping frames at ~30 fps."""
    act = [model.actuator(f"actuator{i}").id for i in range(1, 8)]
    start = data.ctrl[act].copy()
    steps = max(1, int(seconds / model.opt.timestep))
    every = max(1, int(1 / 30 / model.opt.timestep))
    for k in range(steps):
        alpha = min(1.0, (k + 1) / (0.7 * steps))
        data.ctrl[act] = start + alpha * (target - start)
        data.ctrl[model.actuator("actuator8").id] = gripper
        mujoco.mj_step(model, data)
        if recorder is not None and k % every == 0:
            recorder.snap(data, caption, color)


def run_grasp(cube, belief, recorder=None, caption="", color=(255, 255, 255)):
    """Execute approach, descend, close, lift toward the believed pose (x, y, yaw).

    Returns a dict with success (cube lifted above LIFT_SUCCESS_M) and the final cube height.
    """
    model, data = panda_scene(cube)
    bx, by, byaw = belief
    data.mocap_pos[0] = [bx, by, cube.half]
    data.mocap_quat[0] = [np.cos(byaw / 2), 0, 0, np.sin(byaw / 2)]
    quat = down_quat(byaw + np.pi / 4)  # hand frame is rotated 45 degrees from the finger axis
    joints = PANDA_ARM_JOINTS
    plan = [
        ([bx, by, cube.half + 0.12], GRIPPER_OPEN, 1.2, "approach"),
        ([bx, by, cube.half + 0.002], GRIPPER_OPEN, 0.9, "descend"),
        ([bx, by, cube.half + 0.002], GRIPPER_CLOSED, 0.6, "close"),
        ([bx, by, cube.half + 0.20], GRIPPER_CLOSED, 1.2, "lift"),
    ]
    for pos, gripper, seconds, phase in plan:
        q, _ = solve_ik(model, data, joints, np.array(pos), quat)
        label = f"{caption} | {phase}" if caption else phase
        _move(model, data, joints, q, gripper, seconds, recorder, label, color)
    height = float(data.body("cube").xpos[2] - cube.half)
    return {"success": height > LIFT_SUCCESS_M, "lift_m": height}


if __name__ == "__main__":
    from sim.scene import Cube
    print(run_grasp(Cube(), (0.55, 0.0, 0.0)))
    print(run_grasp(Cube(), (0.55, 0.035, 0.0)))
