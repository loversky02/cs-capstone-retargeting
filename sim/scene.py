"""Scene building, inverse kinematics and rendering shared by the MuJoCo demos."""

from dataclasses import dataclass

import mujoco
import numpy as np

from sim.fetch_models import ensure_models

PANDA_ARM_JOINTS = [f"joint{i}" for i in range(1, 8)]
UR5E_JOINTS = ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint",
               "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"]
GRIPPER_OPEN, GRIPPER_CLOSED = 255.0, 0.0
DOWN = np.array([0.0, 1.0, 0.0, 0.0])  # tool z-axis pointing at the table


@dataclass
class Cube:
    x: float = 0.55
    y: float = 0.0
    yaw: float = 0.0
    half: float = 0.022
    friction: float = 1.0
    mass: float = 0.08


def panda_scene(cube: Cube, ghost=True):
    """Panda on the menagerie floor with one free cube and a tool-centre site."""
    root = ensure_models()
    spec = mujoco.MjSpec.from_file(str(root / "franka_emika_panda" / "scene.xml"))
    spec.body("hand").add_site(name="tcp", pos=[0, 0, 0.1034], size=[0.006] * 3, rgba=[1, 0.6, 0, 1])
    body = spec.worldbody.add_body(name="cube", pos=[cube.x, cube.y, cube.half],
                                   quat=yaw_quat(cube.yaw))
    body.add_freejoint()
    body.add_geom(type=mujoco.mjtGeom.mjGEOM_BOX, size=[cube.half] * 3, rgba=[0.85, 0.2, 0.25, 1],
                  friction=[cube.friction, 0.005, 0.0001], mass=cube.mass)
    if ghost:  # where the robot *believes* the cube is, drawn without collision
        marker = spec.worldbody.add_body(name="belief", mocap=True, pos=[cube.x, cube.y, cube.half])
        marker.add_geom(type=mujoco.mjtGeom.mjGEOM_BOX, size=[cube.half * 1.02] * 3,
                        rgba=[0.2, 0.7, 1, 0.35], contype=0, conaffinity=0)
    model = spec.compile()
    data = mujoco.MjData(model)
    mujoco.mj_resetDataKeyframe(model, data, model.key("home").id)
    mujoco.mj_forward(model, data)
    return model, data


def ur5e_scene(cube: Cube | None = None):
    """UR5e (no gripper) with its flange site renamed to tcp; optionally a static marker cube."""
    root = ensure_models()
    spec = mujoco.MjSpec.from_file(str(root / "universal_robots_ur5e" / "scene.xml"))
    spec.site("attachment_site").name = "tcp"
    if cube is not None:
        marker = spec.worldbody.add_body(name="cube", pos=[cube.x, cube.y, cube.half], quat=yaw_quat(cube.yaw))
        marker.add_geom(type=mujoco.mjtGeom.mjGEOM_BOX, size=[cube.half] * 3, rgba=[0.85, 0.2, 0.25, 1],
                        contype=0, conaffinity=0)
    model = spec.compile()
    data = mujoco.MjData(model)
    mujoco.mj_resetDataKeyframe(model, data, model.key("home").id)
    mujoco.mj_forward(model, data)
    return model, data


def yaw_quat(yaw):
    return [np.cos(yaw / 2), 0.0, 0.0, np.sin(yaw / 2)]


def down_quat(yaw):
    """Tool pointing down, rotated about the world z-axis by yaw."""
    out = np.zeros(4)
    mujoco.mju_mulQuat(out, np.array(yaw_quat(yaw)), DOWN)
    return out


def solve_ik(model, data, joints, target_pos, target_quat=None, iters=200, damping=1e-3):
    """Damped least-squares IK on a scratch copy. Returns (joint values, position error in metres)."""
    scratch = mujoco.MjData(model)
    scratch.qpos[:] = data.qpos
    site = model.site("tcp").id
    dofs = [model.joint(j).dofadr[0] for j in joints]
    qadr = [model.joint(j).qposadr[0] for j in joints]
    ranges = np.array([model.joint(j).range for j in joints])
    limited = np.array([model.jnt_limited[model.joint(j).id] for j in joints], dtype=bool)
    jacp, jacr = np.zeros((3, model.nv)), np.zeros((3, model.nv))
    for _ in range(iters):
        mujoco.mj_kinematics(model, scratch)
        mujoco.mj_comPos(model, scratch)
        err = target_pos - scratch.site_xpos[site]
        if target_quat is not None:
            current = np.zeros(4)
            mujoco.mju_mat2Quat(current, scratch.site_xmat[site])
            conj, diff, rot = np.zeros(4), np.zeros(4), np.zeros(3)
            mujoco.mju_negQuat(conj, current)
            mujoco.mju_mulQuat(diff, target_quat, conj)
            mujoco.mju_quat2Vel(rot, diff, 1.0)
            err = np.concatenate([err, 0.5 * rot])
        if np.linalg.norm(err[:3]) < 5e-4 and (len(err) == 3 or np.linalg.norm(err[3:]) < 5e-3):
            break
        mujoco.mj_jacSite(model, scratch, jacp, jacr, site)
        jac = (jacp if target_quat is None else np.vstack([jacp, jacr]))[:, dofs]
        step = jac.T @ np.linalg.solve(jac @ jac.T + damping * np.eye(len(err)), err)
        q = scratch.qpos[qadr] + step
        q[limited] = np.clip(q[limited], ranges[limited, 0], ranges[limited, 1])
        scratch.qpos[qadr] = q
    mujoco.mj_kinematics(model, scratch)
    return scratch.qpos[qadr].copy(), float(np.linalg.norm(target_pos - scratch.site_xpos[site]))


class Recorder:
    """Offscreen frames with an optional caption bar, written to MP4."""

    def __init__(self, model, width=640, height=480, camera=None):
        self.renderer = mujoco.Renderer(model, height, width)
        self.camera = camera or mujoco.MjvCamera()
        if camera is None:
            self.camera.lookat[:] = [0.35, 0.0, 0.3]
            self.camera.distance, self.camera.azimuth, self.camera.elevation = 1.9, 140, -22
        self.frames = []

    def snap(self, data, caption="", color=(255, 255, 255)):
        self.renderer.update_scene(data, self.camera)
        self.frames.append(caption_frame(self.renderer.render(), caption, color))


def caption_frame(pixels, caption, color=(255, 255, 255)):
    if not caption:
        return pixels
    from PIL import Image, ImageDraw, ImageFont
    image = Image.fromarray(pixels)
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, image.width, 34], fill=(15, 23, 42))
    draw.text((10, 7), caption, fill=color, font=ImageFont.load_default(size=17))
    return np.asarray(image)


def write_video(frames, path, fps=30):
    import imageio.v2 as imageio
    path.parent.mkdir(parents=True, exist_ok=True)
    imageio.mimwrite(path, frames, fps=fps, codec="libx264", quality=7, macro_block_size=8)
