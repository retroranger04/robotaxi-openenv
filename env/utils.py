import random
from typing import Dict, List

from .config import NUM_ZONES, MAX_STEPS


# Simple distance matrix: abs difference between zone indices (zones 0-5)
def zone_distance(zone_a: int, zone_b: int) -> int:
    return abs(zone_a - zone_b)


def generate_request_schedule(seed: int, num_zones: int = NUM_ZONES, max_steps: int = MAX_STEPS) -> Dict[int, List[dict]]:
    """Generate a deterministic schedule mapping timestep -> list of request dicts."""
    rng = random.Random(seed)
    schedule: Dict[int, List[dict]] = {}
    request_id = 0

    for step in range(max_steps):
        # 0–2 new requests per timestep
        count = rng.randint(0, 2)
        if count > 0:
            requests = []
            for _ in range(count):
                pickup = rng.randint(0, num_zones - 1)
                drop = rng.randint(0, num_zones - 1)
                while drop == pickup:
                    drop = rng.randint(0, num_zones - 1)
                reward = round(rng.uniform(1.0, 10.0), 2)
                max_wait = rng.randint(3, 8)
                requests.append({
                    "id": request_id,
                    "pickup_zone": pickup,
                    "drop_zone": drop,
                    "reward": reward,
                    "waiting_time": 0,
                    "max_wait": max_wait,
                })
                request_id += 1
            schedule[step] = requests

    return schedule


def validate_action(action_type: str, taxi_id, request_id, taxis: list, active_requests: list, charging_stations: list) -> str:
    """Return error string if action is invalid, else empty string."""
    if action_type not in ("assign", "charge", "wait"):
        return f"Unknown action_type: {action_type}"

    if action_type == "wait":
        return ""

    if taxi_id is None:
        return "taxi_id is required for assign/charge actions"

    taxi = next((t for t in taxis if t["id"] == taxi_id), None)
    if taxi is None:
        return f"Taxi {taxi_id} not found"

    if taxi["status"] != "idle":
        return f"Taxi {taxi_id} is not idle (status={taxi['status']})"

    if action_type == "assign":
        if request_id is None:
            return "request_id is required for assign action"
        req = next((r for r in active_requests if r["id"] == request_id), None)
        if req is None:
            return f"Request {request_id} not found in active requests"

    if action_type == "charge":
        station = next((s for s in charging_stations if s["zone"] == taxi["zone"]), None)
        if station is None:
            return f"No charging station in zone {taxi['zone']}"
        if station["occupied"] >= station["capacity"]:
            return f"Charging station in zone {taxi['zone']} is at capacity"
        if taxi["battery"] >= 100:
            return "Taxi battery is already full"

    return ""
