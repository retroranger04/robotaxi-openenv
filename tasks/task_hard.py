"""
task_hard.py — urban_stress_test

High-demand dispatch with battery constraints, demand spikes,
and strict wait enforcement.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from env.environment import RobotaxiEnv
from env.models import RobotaxiAction
from tasks.grader import grade


def get_config() -> dict:
    return {
        "task_name": "urban_stress_test",
        "battery_enabled": True,
        "charging_enabled": True,
        "demand_spike": True,
        "strict_wait": True,
        "seed": 999,
        "max_steps": 40,
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
    print(f"urban_stress_test score: {score:.4f}")
