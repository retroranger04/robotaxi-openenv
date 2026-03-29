"""
scripts/demo.py — Demo run of basic_dispatch task with step-by-step output.

Usage:
    python scripts/demo.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from env.environment import RobotaxiEnv
from inference import select_action, strategy, run_episode
from tasks.task_easy import get_config


def main():
    config = get_config()
    env = RobotaxiEnv(seed=config["seed"])

    print("=" * 50)
    print("Demo: basic_dispatch")
    print(f"  seed={config['seed']}  max_steps={config['max_steps']}")
    print("=" * 50)

    score, metrics = run_episode(env, config, strategy, verbose=True)

    print()
    print(f"Final score : {score:.4f}")
    print(f"Completed   : {metrics['completed']}")
    print(f"Missed      : {metrics['missed']}")
    print(f"Idle time   : {metrics['idle_time']}")
    print(f"Battery fail: {metrics['battery_failures']}")


if __name__ == "__main__":
    main()
