"""
scripts/run_env.py — Manual environment test runner for debugging.

Steps through the environment with wait actions, printing observation
at each step so you can inspect state transitions.

Usage:
    python scripts/run_env.py [--steps N] [--seed S]
"""

import sys
import os
import argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from env.environment import RobotaxiEnv
from env.models import RobotaxiAction


def main():
    parser = argparse.ArgumentParser(description="Manual env test runner")
    parser.add_argument("--steps", type=int, default=10, help="Number of steps to run (default: 10)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    args = parser.parse_args()

    env = RobotaxiEnv(seed=args.seed)
    obs = env.reset()

    print(f"Env initialized | seed={args.seed} | taxis={len(obs.taxis)} | stations={len(obs.charging_stations)}")
    print("-" * 60)

    for step in range(args.steps):
        action = RobotaxiAction(action_type="wait")
        obs, reward, done, info = env.step(action)

        idle = sum(1 for t in obs.taxis if t.status == "idle")
        serving = sum(1 for t in obs.taxis if t.status == "serving")
        charging = sum(1 for t in obs.taxis if t.status == "charging")
        min_bat = min(t.battery for t in obs.taxis)

        print(
            f"step {obs.time_step:02d} | "
            f"idle={idle} serving={serving} charging={charging} | "
            f"requests={len(obs.requests)} | "
            f"min_battery={min_bat:.0f} | "
            f"completed={info['completed']} missed={info['missed']} | "
            f"reward={reward:.2f}"
        )

        if done:
            print("Episode done.")
            break

    print("-" * 60)
    state = env.state()
    print("Final metrics:", state["metrics"])


if __name__ == "__main__":
    main()
