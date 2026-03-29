import random
from typing import Any, Dict, List, Optional, Tuple

from .config import (
    NUM_TAXIS,
    NUM_ZONES,
    MAX_STEPS,
    CHARGING_TIME,
    CHARGE_AMOUNT,
    CHARGING_CAPACITY,
    INITIAL_BATTERY,
)
from .models import (
    ChargingStation,
    Request,
    RobotaxiAction,
    RobotaxiObservation,
    Taxi,
)
from .utils import generate_request_schedule, validate_action


class RobotaxiEnv:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.taxis: List[Dict] = []
        self.active_requests: List[Dict] = []
        self.request_schedule: Dict[int, List[Dict]] = {}
        self.charging_stations: List[Dict] = []
        self.time_step: int = 0
        self.metrics: Dict[str, Any] = {}
        self._rng = random.Random(seed)

    # ------------------------------------------------------------------
    # reset
    # ------------------------------------------------------------------
    def reset(self) -> RobotaxiObservation:
        self._rng = random.Random(self.seed)
        self.time_step = 0

        # Initialize taxis
        self.taxis = [
            {
                "id": i,
                "zone": self._rng.randint(0, NUM_ZONES - 1),
                "battery": float(INITIAL_BATTERY),
                "status": "idle",
                "time_to_available": 0,
            }
            for i in range(NUM_TAXIS)
        ]

        # Initialize charging stations (one per zone)
        self.charging_stations = [
            {
                "zone": z,
                "capacity": CHARGING_CAPACITY,
                "occupied": 0,
            }
            for z in range(NUM_ZONES)
        ]

        # Generate deterministic request schedule
        self.request_schedule = generate_request_schedule(self.seed)

        # Clear active requests
        self.active_requests = []

        # Reset metrics
        self.metrics = {
            "completed": 0,
            "missed": 0,
            "total_wait_time": 0,
            "battery_failures": 0,
            "idle_time": 0,
        }

        return self._make_observation()

    # ------------------------------------------------------------------
    # step
    # ------------------------------------------------------------------
    def step(self, action: RobotaxiAction) -> Tuple[RobotaxiObservation, float, bool, Dict]:
        # 1. Validate action
        error = validate_action(
            action.action_type,
            action.taxi_id,
            action.request_id,
            self.taxis,
            self.active_requests,
            self.charging_stations,
        )
        if error:
            raise ValueError(f"Invalid action: {error}")

        # 2. Apply action
        if action.action_type == "assign":
            taxi = self._get_taxi(action.taxi_id)
            req = self._get_request(action.request_id)
            trip_duration = max(1, abs(taxi["zone"] - req["drop_zone"]))
            taxi["status"] = "serving"
            taxi["zone"] = req["drop_zone"]
            taxi["time_to_available"] = trip_duration
            self.active_requests.remove(req)
            self.metrics["completed"] += 1
            self.metrics["total_wait_time"] += req["waiting_time"]

        elif action.action_type == "charge":
            taxi = self._get_taxi(action.taxi_id)
            station = self._get_station(taxi["zone"])
            taxi["status"] = "charging"
            taxi["time_to_available"] = CHARGING_TIME
            station["occupied"] += 1

        # action_type == "wait" → no-op

        # 3. Advance all taxis
        for taxi in self.taxis:
            if taxi["status"] == "idle":
                self.metrics["idle_time"] += 1
                continue

            if taxi["time_to_available"] > 0:
                taxi["time_to_available"] -= 1

            if taxi["time_to_available"] == 0:
                if taxi["status"] == "charging":
                    station = self._get_station(taxi["zone"])
                    taxi["battery"] = min(100.0, taxi["battery"] + CHARGE_AMOUNT)
                    station["occupied"] = max(0, station["occupied"] - 1)
                taxi["status"] = "idle"

        # 4. Update requests: increment waiting_time, remove expired
        updated = []
        for req in self.active_requests:
            req["waiting_time"] += 1
            if req["waiting_time"] >= req["max_wait"]:
                self.metrics["missed"] += 1
            else:
                updated.append(req)
        self.active_requests = updated

        # 5. Add new requests from schedule
        new_reqs = self.request_schedule.get(self.time_step, [])
        self.active_requests.extend([dict(r) for r in new_reqs])

        # 6. Compute reward (simple placeholder)
        reward = float(self.metrics["completed"]) - float(self.metrics["missed"]) * 0.5

        # 7. Metrics already updated above in each section

        # 8. Increment time_step
        self.time_step += 1

        # 9. Done?
        done = self.time_step >= MAX_STEPS

        # 10. Return
        info = dict(self.metrics)
        return self._make_observation(), reward, done, info

    # ------------------------------------------------------------------
    # state
    # ------------------------------------------------------------------
    def state(self) -> Dict:
        return {
            "taxis": list(self.taxis),
            "active_requests": list(self.active_requests),
            "charging_stations": list(self.charging_stations),
            "time_step": self.time_step,
            "metrics": dict(self.metrics),
        }

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _make_observation(self) -> RobotaxiObservation:
        return RobotaxiObservation(
            taxis=[Taxi(**t) for t in self.taxis],
            requests=[Request(**r) for r in self.active_requests],
            charging_stations=[ChargingStation(**s) for s in self.charging_stations],
            time_step=self.time_step,
        )

    def _get_taxi(self, taxi_id: int) -> Dict:
        taxi = next((t for t in self.taxis if t["id"] == taxi_id), None)
        if taxi is None:
            raise ValueError(f"Taxi {taxi_id} not found")
        return taxi

    def _get_request(self, request_id: int) -> Dict:
        req = next((r for r in self.active_requests if r["id"] == request_id), None)
        if req is None:
            raise ValueError(f"Request {request_id} not found")
        return req

    def _get_station(self, zone: int) -> Dict:
        station = next((s for s in self.charging_stations if s["zone"] == zone), None)
        if station is None:
            raise ValueError(f"No charging station in zone {zone}")
        return station
