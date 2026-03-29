"""
grader.py — Deterministic scoring for all robotaxi tasks.

score = weighted sum of:
  service_rate  = completed / total_requests
  wait_score    = 1 - (avg_wait_time / max_wait)
  battery_score = 1 - min(1, battery_failures / 3)
  efficiency    = 1 - (idle_time / max_possible_idle)

Weights differ by task_name:
  basic_dispatch               : 0.5 / 0.3 / —   / 0.2
  energy_constrained_dispatch  : 0.4 / 0.2 / 0.2 / 0.2
  urban_stress_test            : 0.4 / 0.2 / 0.2 / 0.2
"""

MAX_WAIT = 8          # maximum possible per-request wait (from generate_request_schedule)
NUM_TAXIS = 10        # matches env config


def grade(metrics: dict, config: dict) -> float:
    """
    Compute a deterministic score in [0, 1].

    Parameters
    ----------
    metrics   : info dict returned by the last env.step() call
    config    : task config dict (contains task_name, max_steps, …)
    """
    task_name = config.get("task_name", "basic_dispatch")
    max_steps = config.get("max_steps", 40)

    completed = metrics.get("completed", 0)
    missed = metrics.get("missed", 0)
    total_wait_time = metrics.get("total_wait_time", 0)
    battery_failures = metrics.get("battery_failures", 0)
    idle_time = metrics.get("idle_time", 0)

    total_requests = completed + missed
    max_possible_idle = NUM_TAXIS * max_steps

    # --- service_rate ---
    service_rate = completed / total_requests if total_requests > 0 else 0.0

    # --- wait_score ---
    avg_wait_time = total_wait_time / completed if completed > 0 else 0.0
    wait_score = 1.0 - (avg_wait_time / MAX_WAIT)
    wait_score = max(0.0, min(1.0, wait_score))

    # --- battery_score ---
    battery_score = 1.0 - min(1.0, battery_failures / 3)

    # --- efficiency ---
    efficiency = 1.0 - (idle_time / max_possible_idle) if max_possible_idle > 0 else 0.0
    efficiency = max(0.0, min(1.0, efficiency))

    # --- weighted score ---
    if task_name == "basic_dispatch":
        score = (
            0.5 * service_rate
            + 0.3 * wait_score
            + 0.2 * efficiency
        )
    else:
        # energy_constrained_dispatch and urban_stress_test
        score = (
            0.4 * service_rate
            + 0.2 * wait_score
            + 0.2 * battery_score
            + 0.2 * efficiency
        )

    return float(max(0.0, min(1.0, score)))
