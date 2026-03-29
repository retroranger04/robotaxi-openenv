"""
task_medium.py — energy_constrained_dispatch

Dispatch task with battery depletion and charging enabled.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from env.environment import RobotaxiEnv
from env.models import RobotaxiAction
from tasks.grader import grade


def get_config() -> dict:
    return {
        "task_name": "energy_constrained_dispatch",
        "battery_enabled": True,
        "charging_enabled": True,
        "seed": 123,
        "max_steps": 35,
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
    print(f"energy_constrained_dispatch score: {score:.4f}")
