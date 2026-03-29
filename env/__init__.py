from .environment import RobotaxiEnv
from .models import (
    ChargingStation,
    Request,
    RobotaxiAction,
    RobotaxiObservation,
    Taxi,
)


def create_fastapi_app(env: RobotaxiEnv):
    """Create and return a FastAPI app that wraps the given environment."""
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel

    app = FastAPI(title="Robotaxi OpenEnv")

    @app.get("/")
    def root():
        return {"status": "Robotaxi OpenEnv running"}

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/reset", response_model=RobotaxiObservation)
    def reset():
        return env.reset()

    @app.post("/step")
    def step(action: RobotaxiAction):
        try:
            obs, reward, done, info = env.step(action)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {
            "observation": obs.model_dump(),
            "reward": reward,
            "done": done,
            "info": info,
        }

    @app.get("/state")
    def state():
        return env.state()

    return app


__all__ = [
    "RobotaxiEnv",
    "Taxi",
    "Request",
    "ChargingStation",
    "RobotaxiObservation",
    "RobotaxiAction",
    "create_fastapi_app",
]
