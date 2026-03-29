"""
task_easy.py — basic_dispatch

Simple dispatch task with no battery or charging constraints.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from env.environment import RobotaxiEnv
from env.models import RobotaxiAction
from tasks.grader import grade


def get_config() -> dict:
    return {
        "task_name": "basic_dispatch",
        "battery_enabled": False,
        "charging_enabled": False,
        "seed": 42,
        "max_steps": 30,
    }


def run() -> float:
    config = get_config()
    env = RobotaxiEnv(seed=config["seed"])
    env.reset()

    info = {}
    for _ in range(config["max_steps"]):
        _, _, done, info = env.step(RobotaxiAction(action_type="wait"))
        if done:
            break

    return grade(info, config)


if __name__ == "__main__":
    score = run()
    print(f"basic_dispatch score: {score:.4f}")
