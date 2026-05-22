# nfl_lms

NFL **Last Man Standing** game — product planning lives in [`Game_rules.md`](Game_rules.md) and [`todo.md`](todo.md).

## Current implementation

This repo includes a **Python domain layer**, a **FastAPI** HTTP API, and **Firebase** (Auth + Realtime Database) persistence. A minimal **Vite/TypeScript** frontend lives in [`web/`](web/).

| Module | Description |
|--------|-------------|
| [`user.py`](user.py) | `User`: `id`, `name`, optional `email`; Firebase Auth signup via `create_with_email_password()`; Realtime Database CRUD |
| [`league.py`](league.py) | `League`: `id`, `name`, list of `User`, `Settings`; Realtime Database CRUD |
| [`settings.py`](settings.py) | `Settings`: rule toggles (elimination, division rotation, comeback + streak length), multipliers |
| [`team.py`](team.py) | `Team`: ESPN id, abbreviation, names, division + conference |
| [`espn_nfl.py`](espn_nfl.py) | `fetch_nfl_teams()`: loads 32 teams + divisions from ESPN HTTP APIs |
| [`firebase_store.py`](firebase_store.py) | Firebase Admin SDK (lazy init, `.env` loading, Auth + Realtime Database) |
| [`app/main.py`](app/main.py) | FastAPI: health, demo league, NFL teams, user signup, user/league database routes |

Tests live under [`test/`](test/) (domain models, API, database mocks, optional live Firebase/ESPN integration).

## Firebase configuration (backend)

Copy [`.env.example`](.env.example) to `.env` at the repo root:

```bash
cp .env.example .env
```

| Variable | Purpose |
|----------|---------|
| `FIREBASE_PROJECT_ID` | Firebase / GCP project id (default `nfl-lms`) |
| `FIREBASE_DATABASE_URL` | Realtime Database URL (default `https://nfl-lms-default-rtdb.firebaseio.com`) |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to credentials JSON (optional; see below) |

The API loads `.env` automatically on first Firebase access.

**Credentials**

- **Service account JSON** (`type: service_account`) — recommended for production and for creating Auth users via the Admin SDK. Download from Firebase console → Project settings → Service accounts.
- **Application Default Credentials** — from `gcloud auth application-default login`. Supported for local database access; creating Auth users may require a service account with the right IAM roles.

If `GOOGLE_APPLICATION_CREDENTIALS` is unset, the Admin SDK falls back to Application Default Credentials.

## HTTP API (local)

Install dependencies (includes FastAPI, Firebase Admin, and uvicorn):

```bash
pip install -e ".[dev]"
# or: uv sync --extra dev
```

Run the server from the repo root:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- `GET /` returns a JSON map of useful paths.
- Optional CORS allowlist (comma-separated origins; default `*`): env var `CORS_ORIGINS`, e.g. `http://localhost:5173`

### Key routes

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/users` | Sign up: creates Firebase Auth user (email/password) and RTDB node at `users/{uid}` |
| `GET` | `/api/v1/users/{user_id}` | Load user profile from Realtime Database |
| `PUT` | `/api/v1/users/{user_id}` | Update user name in Realtime Database (does not create Auth users) |
| `GET` / `PUT` | `/api/v1/leagues/{league_id}` | Read / write league in Realtime Database |
| `GET` | `/api/v1/nfl/teams` | All NFL teams (live ESPN) |

**Sign up example**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com","password":"your-secure-password"}'
```

Response `201`: `{ "id": "<firebase-uid>", "name": "Alice", "email": "alice@example.com" }`

## Frontend

See [`web/README.md`](web/README.md) for the Vite app (Firebase client config, local dev).

## Deploy on Render

[`render.yaml`](render.yaml) defines a **Web Service** that runs:

`uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Set `FIREBASE_PROJECT_ID` and provide a service account via Render env vars (or secret file). In the [Render](https://render.com/) dashboard, create a **Blueprint** from this repo or add a **Web Service** with the same build/start commands.

## Development environment

- **Python 3.10+** and a virtual environment (e.g. `python -m venv .venv`, or [uv](https://github.com/astral-sh/uv)).
- **Install (includes test + lint tools):** `pip install -e ".[dev]"` or `uv sync --extra dev`.
- **Editor:** [`.editorconfig`](.editorconfig) sets spacing and line endings.
- **Lint & format** ([Ruff](https://docs.astral.sh/ruff/), configured in `pyproject.toml`):

  ```bash
  ruff check .
  ruff format .
  ```

  With uv: `uv run ruff check .` and `uv run ruff format .`

- **Package build:** `uv build` or `python -m build` after `pip install build`.

## Setup & tests

From the repository root, with dev dependencies installed:

```bash
pytest
```

`pyproject.toml` sets `pythonpath = ["."]` so imports like `from user import User` resolve during tests.

**Optional integration tests**

| Env | Command |
|-----|---------|
| `NFL_LMS_LIVE_ESPN=1` | Live ESPN fetch: `pytest test/test_espn_nfl.py -k live` |
| `FIREBASE_TEST=1` plus credentials or `FIREBASE_DATABASE_EMULATOR_HOST` | Live Realtime Database roundtrips: `pytest test/test_firebase_integration.py` |

### End-to-end API tests

Under [`test/e2e/`](test/e2e/), scenarios exercise multiple routes via `TestClient` (NFL data mocked for CI):

```bash
pytest -m e2e
```

On push/PR, [`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs **ruff** and **pytest**.

## Docs

- **[Game_rules.md](Game_rules.md)** — gameplay rules (picks, points equation, optional modes).
- **[todo.md](todo.md)** — roadmap (what’s done vs still planned).
