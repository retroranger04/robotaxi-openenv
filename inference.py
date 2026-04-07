"""
inference.py — Run all 3 robotaxi tasks with a simple rule-based policy.

Usage:
    python inference.py

Requires environment variables (or .env file):
    OPENAI_API_KEY   — key for the LLM client (used once per episode for summary)
    API_BASE_URL     — base URL for the OpenAI-compatible endpoint
    MODEL_NAME       — model identifier
"""

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI
import openai

load_dotenv()

# -- path setup so we can run from project root --
sys.path.insert(0, os.path.dirname(__file__))

from env.environment import RobotaxiEnv
from env.models import RobotaxiAction
from tasks.grader import grade
from tasks.task_easy import get_config as easy_config
from tasks.task_medium import get_config as medium_config
from tasks.task_hard import get_config as hard_config

# Load .env from the project directory regardless of where the script is run from
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=_env_path)

# ---------------------------------------------------------------------------
# LLM client (used once per episode for a performance summary, not for policy)
# ---------------------------------------------------------------------------
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN", "")

print(f"API KEY LOADED: {OPENAI_API_KEY is not None}", file=sys.stderr, flush=True)

try:
    llm_client = OpenAI(api_key=OPENAI_API_KEY or "sk-placeholder", base_url=API_BASE_URL)
except Exception as e:
    print(f"  [LLM init error] {type(e).__name__}: {e}", file=sys.stderr, flush=True)
    llm_client = None


def llm_summarize(task_name: str, metrics: dict, score: float) -> str:
    """Make one LLM call per episode to summarize performance."""
    prompt = (
        f"Task: {task_name}\n"
        f"Metrics: completed={metrics.get('completed')}, missed={metrics.get('missed')}, "
        f"idle_time={metrics.get('idle_time')}, battery_failures={metrics.get('battery_failures')}\n"
        f"Score: {score:.4f}\n"
        "In one sentence, summarize the fleet's performance."
    )
    if llm_client is None:
        return "LLM unavailable"
    try:
        response = llm_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
        )
        return response.choices[0].message.content.strip()
    except (openai.AuthenticationError, openai.RateLimitError, openai.APIConnectionError) as e:
        print(f"  [LLM error] {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        return "LLM unavailable"
    except Exception as e:
        print(f"  [LLM error] {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        return "LLM unavailable"


# ---------------------------------------------------------------------------
# Strategy
# ---------------------------------------------------------------------------
strategy = {
    "min_battery_threshold": 30,
    "max_assignment_distance": 4,
}


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------
def select_action(observation, strategy: dict) -> RobotaxiAction:
    """
    Simple rule-based policy:
      1. For each active request, find the closest idle taxi with sufficient battery → assign.
      2. For any idle taxi below battery threshold → charge.
      3. Otherwise → wait.
    """
    min_battery = strategy["min_battery_threshold"]
    max_dist = strategy["max_assignment_distance"]

    idle_taxis = [t for t in observation.taxis if t.status == "idle"]
    requests = list(observation.requests)

    assigned_taxi_ids = set()

    for req in requests:
        # Find closest idle taxi that hasn't been assigned yet this step
        candidates = [t for t in idle_taxis if t.id not in assigned_taxi_ids]
        if not candidates:
            break

        closest = min(candidates, key=lambda t: abs(t.zone - req.pickup_zone))
        dist = abs(closest.zone - req.pickup_zone)

        if dist <= max_dist and closest.battery > min_battery:
            assigned_taxi_ids.add(closest.id)
            return RobotaxiAction(
                action_type="assign",
                taxi_id=closest.id,
                request_id=req.id,
            )

    # Charge any idle taxi below threshold
    for taxi in idle_taxis:
        if taxi.id in assigned_taxi_ids:
            continue
        if taxi.battery < min_battery:
            return RobotaxiAction(action_type="charge", taxi_id=taxi.id)

    return RobotaxiAction(action_type="wait")


# ---------------------------------------------------------------------------
# Episode runner
# ---------------------------------------------------------------------------
def run_episode(env: RobotaxiEnv, config: dict, strategy: dict, verbose: bool = False) -> tuple:
    """
    Run one full episode.
    Returns (score, final_metrics, steps_completed).
    """
    obs = env.reset()
    info = {}
    step = 0
    max_steps = config.get("max_steps", 40)

    while True:
        action = select_action(obs, strategy)
        obs, reward, done, info = env.step(action)
        step += 1

        print(f"[STEP] step={step} reward={reward}", flush=True)

        if verbose:
            print(
                f"  step {step:02d} | action={action.action_type}"
                + (f" taxi={action.taxi_id}" if action.taxi_id is not None else "")
                + (f" req={action.request_id}" if action.request_id is not None else "")
                + f" | completed={info['completed']} missed={info['missed']}",
                file=sys.stderr,
            )

        if done or step >= max_steps:
            break

    score = grade(info, config)
    return score, info, step


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    tasks = [
        ("basic_dispatch", easy_config()),
        ("energy_constrained_dispatch", medium_config()),
        ("urban_stress_test", hard_config()),
    ]

    print("=" * 50, file=sys.stderr)
    print("Robotaxi OpenEnv — Inference Run", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    for task_name, config in tasks:
        steps_completed = 0
        print(f"[START] task={task_name}", flush=True)
        try:
            env = RobotaxiEnv(seed=config["seed"])
            score, metrics, steps_completed = run_episode(env, config, strategy)
            summary = llm_summarize(task_name, metrics, score)

            print(f"[END] task={task_name} score={score:.4f} steps={steps_completed}", flush=True)
            print(f"{task_name}: {score:.2f}", file=sys.stderr)
            print(f"  completed={metrics['completed']}  missed={metrics['missed']}"
                  f"  idle={metrics['idle_time']}  battery_failures={metrics['battery_failures']}",
                  file=sys.stderr)
            print(f"  summary: {summary}", file=sys.stderr)
        except Exception as e:
            print(f"[END] task={task_name} score=0.0 steps={steps_completed}", flush=True)
            print(f"{task_name}: ERROR — {type(e).__name__}: {e}", file=sys.stderr)

    print("=" * 50, file=sys.stderr)


if __name__ == "__main__":
    main()
