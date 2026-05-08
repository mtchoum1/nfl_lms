# nfl_lms

NFL **Last Man Standing** game — product planning lives in [`Game_rules.md`](Game_rules.md) and [`todo.md`](todo.md).

## Current implementation

This repo includes an early **Python domain layer** and a **FastAPI** HTTP API (no database yet):

| Module | Description |
|--------|-------------|
| [`user.py`](user.py) | `User`: `id`, `name`, getters, string representation, equality/hash |
| [`league.py`](league.py) | `League`: `id`, `name`, list of `User`, `Settings` |
| [`settings.py`](settings.py) | `Settings`: rule toggles (elimination, division rotation, comeback + streak length), `active_multiplier` / `eliminated_multiplier`, `set_multipliers()` |
| [`app/main.py`](app/main.py) | FastAPI app: `GET /health`, `GET /api/v1/info`, `GET /api/v1/demo/league` (uses domain models) |

Tests live under [`test/`](test/) (`test_user.py`, `test_league.py`, `test_settings.py`, `test_api.py`).

## HTTP API (local)

Install dependencies (includes FastAPI and uvicorn):

```bash
pip install -e ".[dev]"
```

Run the server (from the repo root so `user` / `league` / `settings` imports resolve):

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Optional CORS allowlist (comma-separated origins; default `*`): set env var `CORS_ORIGINS`, e.g. `http://localhost:5173,https://your-frontend.example`

## Deploy on Render

[`render.yaml`](render.yaml) defines a **Web Service** that runs:

`uvicorn app.main:app --host 0.0.0.0 --port $PORT`

In the [Render](https://render.com/) dashboard, create a **Blueprint** from this repo or add a **Web Service** with the same build/start commands. Python version is controlled via the `PYTHON_VERSION` env var in the blueprint (adjust if Render’s supported runtimes change).

## Setup & tests

Python **3.10+**. Install dev dependencies and run pytest from the repository root:

```bash
pip install -e ".[dev]"
pytest
```

`pyproject.toml` sets `pythonpath = ["."]` so imports like `from user import User` resolve during tests.

## Docs

- **[Game_rules.md](Game_rules.md)** — gameplay rules (picks, points equation, optional modes).
- **[todo.md](todo.md)** — roadmap (what’s done vs still planned).
