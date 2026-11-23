"""Fetch Franka Panda and UR5e models from mujoco_menagerie at a pinned commit."""

import subprocess
from pathlib import Path

REPO = "https://github.com/google-deepmind/mujoco_menagerie.git"
COMMIT = "f054586a8e90465d49ee5be15335c4a0c7f57caf"
ROBOTS = ("franka_emika_panda", "universal_robots_ur5e")
CACHE = Path(__file__).resolve().parent.parent / ".cache" / "menagerie"


def ensure_models():
    """Return the menagerie directory, cloning only the two robot folders on first use."""
    if all((CACHE / robot).is_dir() for robot in ROBOTS):
        return CACHE
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    if not (CACHE / ".git").is_dir():
        subprocess.run(["git", "clone", "--filter=blob:none", "--no-checkout", REPO, str(CACHE)], check=True)
    subprocess.run(["git", "-C", str(CACHE), "sparse-checkout", "set", *ROBOTS], check=True)
    subprocess.run(["git", "-C", str(CACHE), "checkout", "--quiet", COMMIT], check=True)
    return CACHE


if __name__ == "__main__":
    print(ensure_models())
