from typing import List, Optional
from pydantic import BaseModel


class Taxi(BaseModel):
    id: int
    zone: int
    battery: float
    status: str  # "idle", "serving", "charging"
    time_to_available: int


class Request(BaseModel):
    id: int
    pickup_zone: int
    drop_zone: int
    reward: float
    waiting_time: int
    max_wait: int


class ChargingStation(BaseModel):
    zone: int
    capacity: int
    occupied: int


class RobotaxiObservation(BaseModel):
    taxis: List[Taxi]
    requests: List[Request]
    charging_stations: List[ChargingStation]
    time_step: int


class RobotaxiAction(BaseModel):
    action_type: str  # "assign", "charge", "wait"
    taxi_id: Optional[int] = None
    request_id: Optional[int] = None
