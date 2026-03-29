---
title: Robotaxi OpenEnv
emoji: 🚕
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Robotaxi OpenEnv

A lightweight, deterministic evaluation environment for robotaxi fleet dispatch controllers.

## Overview

Robotaxi OpenEnv provides a reproducible simulation of a multi-vehicle taxi fleet operating across a zoned city grid. It exposes a standard `reset / step / observe` interface and ships with three graded tasks of increasing difficulty:

| Task | Description |
|---|---|
| `basic_dispatch` | Baseline dispatch, light demand, full battery headroom |
| `energy_constrained_dispatch` | Medium demand with low initial battery on several vehicles |
| `urban_stress_test` | High demand burst with tight wait windows and depleted batteries |

Each episode produces a deterministic score in `[0, 1]` based on service rate, wait time, battery management, and fleet efficiency.

## Environment

```
env/
├── environment.py   # RobotaxiEnv — core step/reset logic
├── models.py        # Pydantic observation and action types
├── config.py        # Simulation constants
├── api.py           # FastAPI REST wrapper
└── utils.py         # Request schedule generation, action validation

tasks/
├── grader.py        # Deterministic scoring function
├── task_easy.py     # basic_dispatch config
├── task_medium.py   # energy_constrained_dispatch config
└── task_hard.py     # urban_stress_test config
```

**Action space** — each step, the controller submits one of:
- `assign(taxi_id, request_id)` — assign an idle taxi to an active ride request
- `charge(taxi_id)` — send an idle taxi to its zone's charging station
- `wait` — take no action this step

**Observation** — current taxi states (zone, battery, status), active ride requests (pickup zone, drop zone, waiting time), charging station occupancy, and current time step.

## Run Locally

**Prerequisites:** Python 3.10+

```bash
git clone https://github.com/retroranger04/robotaxi-openenv.git
cd robotaxi-openenv
pip install -r requirements.txt
```

Copy the example env file and fill in your values:

```bash
cp .env.example .env
# edit .env with your OPENAI_API_KEY, MODEL_NAME, API_BASE_URL
```

### Run all three tasks with the built-in rule-based policy

```bash
python inference.py
```

### Start the REST API server

```bash
uvicorn env.api:app --host 0.0.0.0 --port 7860
```

### Demo script

```bash
python scripts/demo.py
```

## Run with Docker

```bash
docker build -t robotaxi-openenv .
docker run -p 7860:7860 --env-file .env robotaxi-openenv
```

The API is then available at `http://localhost:7860`.

## Run Inference

`inference.py` executes all three tasks using a simple rule-based greedy policy and prints per-task scores and a one-sentence LLM summary (requires `OPENAI_API_KEY`).

```
$ python inference.py

==================================================
Robotaxi OpenEnv — Inference Run
==================================================

basic_dispatch: 0.82
  completed=14  missed=2  idle=87  battery_failures=0
  summary: The fleet handled most requests efficiently with minimal idle time.

energy_constrained_dispatch: 0.71
  ...

urban_stress_test: 0.58
  ...
```

To skip the LLM summary, remove or leave `OPENAI_API_KEY` unset — it degrades gracefully.

## Configuration

See `openenv.yaml` for full environment and task configuration.

## License

MIT