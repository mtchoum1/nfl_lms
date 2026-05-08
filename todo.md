# Last Man Standing — App/Website Todo

Todo list for building the game app/website from [Game_rules.md](Game_rules.md).

**Layer:** *Frontend* = UI/browser · *Backend* = API/server/DB · *Both* = front and back

---

## Progress (Python prototype — May 2026)

Domain models and tests exist as plain Python modules at the repo root (no API or database yet):

| Deliverable | Notes |
|-------------|--------|
| **`user.User`** | `id`, `name`; getters; `repr` / `str`; equality & hash — [`user.py`](user.py), [`test/test_user.py`](test/test_user.py) |
| **`league.League`** | `id`, `name`, `users`, `settings` — [`league.py`](league.py), [`test/test_league.py`](test/test_league.py) |
| **`settings.Settings`** | Elimination / division-rotation / comeback flags; `comeback_games_required`; `active_multiplier` & `eliminated_multiplier`; `set_multipliers()` — [`settings.py`](settings.py), [`test/test_settings.py`](test/test_settings.py) |
| **Packaging / tests** | [`pyproject.toml`](pyproject.toml): `user`, `league`, `settings` modules; optional `dev` deps (`pytest`); `pythonpath = ["."]` for test imports |
| **FastAPI scaffold** | [`app/main.py`](app/main.py): health + info + demo league JSON; [`render.yaml`](render.yaml) for Render Web Service; [`test/test_api.py`](test/test_api.py) |
| **Lint / editor defaults** | [Ruff](https://docs.astral.sh/ruff/) in `[project.optional-dependencies] dev`; `[tool.ruff]` in [`pyproject.toml`](pyproject.toml); [`.editorconfig`](.editorconfig) |
| **`team.Team` + ESPN fetch** | [`team.py`](team.py), [`espn_nfl.py`](espn_nfl.py) (`fetch_nfl_teams`), [`GET /api/v1/nfl/teams`](app/main.py); tests [`test/test_team.py`](test/test_team.py), [`test/test_espn_nfl.py`](test/test_espn_nfl.py) |

**Still outstanding for “full” models:** persistence, User email/auth, League season/week, NFL Team/Pick/Game models, and all rule/scoring logic below.

---

## Project setup

- [x] Choose stack (FastAPI API + optional separate frontend; Render for hosting) — *Both*
- [x] Initialize repo (frontend + backend or monorepo) — *Both*
- [x] Set up dev environment, linting, and basic config — *Both* (venv/uv, Ruff, `.editorconfig`, `pyproject` tool sections)
- [x] Add dependency management (Python: `pyproject.toml`, optional `[dev]` with pytest) — *Both*

**Tests**

- [x] Build succeeds (`npm run build` or equivalent) — *Both* (`uv build` / wheel + sdist)
- [x] Test script runs and exits 0 — `pytest` on `test/test_user.py`, `test/test_league.py`, `test/test_settings.py` — *Both*
- [x] Lint passes in CI or locally — *Both* (`ruff check .` / `ruff format .` after `pip install -e ".[dev]"` or `uv run ruff check .`)
- [x] API end-to-end scenarios — *Backend* ([`test/e2e/`](test/e2e/), marker `e2e`; CI in [`.github/workflows/ci.yml`](.github/workflows/ci.yml))

---

## Data & models

- [ ] Define **User** model (id, name — **done** in [`user.py`](user.py); email, auth, DB **TBD**) — *Backend*
- [ ] Define **League** model (users, settings — **done** in [`league.py`](league.py); season, week, persistence **TBD**) — *Backend*
- [x] Define **League settings** (elimination on/off, division rule on/off, comeback rule on/off, comeback games count; optional multipliers) — [`settings.py`](settings.py) — *Backend*
- [x] Define **Team** model (NFL teams + divisions) — *Backend* [`team.py`](team.py), [`espn_nfl.py`](espn_nfl.py), [`GET /api/v1/nfl/teams`](app/main.py)
- [ ] Define **Pick** model (user, league, week, team, game, result) — *Backend*
- [ ] Define **Game** model (week, home/away, odds, result, status) — *Backend*
- [x] Seed or fetch NFL schedule and divisions — *Backend* (`fetch_nfl_teams`; schedule TBD)

**Tests**

- [ ] Model validation (required fields, constraints) — unit or schema tests — *Backend*
- [ ] CRUD / DB operations for each model (create, read, update where applicable) — *Backend*
- [ ] Seed or fetch loads teams/divisions/schedule without error — *Backend*

---

## Game rules (core logic)

- [ ] **Rule 1:** Enforce “pick a team to win, can’t pick that team again” (per user per league) — *Backend*
- [ ] **Rule 2/3 (optional):** Division rule — can’t pick same division until all others used once (8-week rolling) — *Backend*
- [ ] **Rule 4:** Team points equation — (+) odds: `(1 - (100/(odd + 100))) * 100`; (-) odds: `(1 - (abs(odd)/(abs(odd) + 100))) * 100` — *Backend*
- [ ] **Rule 5:** Tie = half of total points: `((team1 points) + (team2 points)) / 2` — *Backend*
- [ ] **Rule 6 (optional):** Comeback rule — N back-to-back correct picks after elimination re-enters pool (tie = win for comeback) — *Backend*
- [ ] **Rule 7:** If eliminated and pick wins → `0.5 * (team points)` only — *Backend*
- [ ] **Rule 3/5 (optional):** Elimination mode (lose = out) vs points-only mode — *Backend*

**Tests**

- [ ] Team points equation: (+) and (-) odds produce expected values (unit tests) — *Backend*
- [ ] Tie scoring: half of (team1 + team2) points (unit test) — *Backend*
- [ ] Rule 1: Re-picking same team is rejected (unit or integration) — *Backend*
- [ ] Division rule: invalid pick when division not yet “unlocked” (if enabled) — *Backend*
- [ ] Elimination: user marked eliminated on loss when mode on — *Backend*
- [ ] Comeback: N back-to-back wins (tie = win) re-enters user (if enabled) — *Backend*
- [ ] Rule 7: Eliminated user gets 0.5 × team points on win (unit test) — *Backend*

---

## Authentication & users

- [ ] Auth flow (sign up / sign in / sign out) — *Both*
- [ ] Protected routes and session handling — *Both*
- [ ] User profile (name, email, leagues) — *Both*

**Tests**

- [ ] Sign up creates user and session (integration or e2e) — *Both*
- [ ] Sign in / sign out work and session is set/cleared — *Both*
- [ ] Protected routes redirect or deny when unauthenticated — *Both*
- [ ] Profile data loads for authenticated user — *Both*

---

## Leagues & membership

- [ ] Create league (name + game settings) — *Both*
- [ ] Join league (code or invite link) — *Both*
- [ ] League roster and roles (owner, member) — *Backend*
- [ ] League settings editable by owner (where applicable) — *Both*

**Tests**

- [ ] Create league persists and returns league + invite code/link — *Backend*
- [ ] Join league by code/link adds user to roster — *Backend*
- [ ] Non-member cannot access league; member can — *Both*
- [ ] Only owner can edit league settings (or role check) — *Both*

---

## Picks & games

- [ ] List games for current (or selected) week with odds — *Both*
- [ ] Submit pick (team per week) with validation against rules (no repeat team, division rule if on) — *Both*
- [ ] Lock picks (e.g. at game time or league deadline) — *Backend*
- [ ] Display user’s pick history and remaining teams — *Frontend*

**Tests**

- [ ] Games list returns correct week and odds — *Backend*
- [ ] Submit pick: valid pick is saved; invalid (repeat team, division rule) is rejected — *Both*
- [ ] Picks locked after deadline/game start — submit rejected or UI disabled — *Both*
- [ ] Pick history and “teams already used” match DB for user/league — *Both*

---

## Scoring & standings

- [ ] Resolve games (win/loss/tie) and compute points (team points equation + tie rule) — *Backend*
- [ ] Apply elimination (if enabled): mark user eliminated when picked team loses — *Backend*
- [ ] Apply comeback rule (if enabled): check back-to-back wins after elimination — *Backend*
- [ ] Standings view: rank by points (and show eliminated / active) — *Both*
- [ ] Per-user summary: total points, teams used, status (active/eliminated/comeback) — *Both*

**Tests**

- [ ] Resolve week: points computed correctly (win/tie) using team points equation — *Backend*
- [ ] Elimination applied when enabled and pick loses — *Backend*
- [ ] Comeback re-entry applied when N back-to-back wins after elimination (if enabled) — *Backend*
- [ ] Standings sort by points; eliminated/active/comeback status correct — *Both*
- [ ] Per-user summary matches resolved picks and status — *Both*

---

## Admin & data

- [ ] Enter or sync game results (and optionally odds updates) — *Both*
- [ ] Trigger “resolve week” to run scoring and update standings — *Backend*
- [ ] (Optional) Import odds from external source or manual entry — *Backend*

**Tests**

- [ ] Entering game result updates game and is persisted — *Backend*
- [ ] “Resolve week” triggers scoring and updates all affected users/standings — *Backend*
- [ ] Odds update (if supported) reflected in games list and points preview — *Both*

---

## UI / pages

- [ ] **Home:** Landing + sign in / sign up — *Frontend*
- [ ] **Dashboard:** My leagues, current week, quick links — *Frontend*
- [ ] **League page:** Standings, settings, members, current week — *Frontend*
- [ ] **Make pick:** Games list, odds, team points preview, submit pick — *Frontend*
- [ ] **Pick history:** Past picks and points per week — *Frontend*
- [ ] **Rules:** In-app copy of rules (from Game_rules.md) — *Frontend*
- [ ] **Profile / settings:** Account and notification prefs (optional) — *Frontend*

**Tests**

- [ ] Home and sign in / sign up render and basic flow works (e2e or smoke) — *Frontend*
- [ ] Dashboard shows user’s leagues and current week — *Frontend*
- [ ] League page shows standings, members, make-pick entry point — *Frontend*
- [ ] Make-pick page lists games, shows points preview, submit updates pick — *Frontend*
- [ ] Pick history shows past picks and points — *Frontend*
- [ ] Rules page displays game rules content — *Frontend*

---

## Optional & polish

- [ ] Responsive layout (mobile-friendly) — *Frontend*
- [ ] Notifications (e.g. pick reminder, results, elimination) — *Both*
- [ ] Dark/light theme — *Frontend*
- [ ] Export standings or history (e.g. CSV) — *Both*
- [x] Basic tests for domain models (`User`, `League`, `Settings`) — *Backend*
- [ ] Tests for scoring and rule logic (points equation, elimination, comeback, etc.) — *Backend*
- [ ] Deploy (e.g. Vercel + DB) and env/config for production — *Both*

**Tests**

- [ ] Responsive: key flows work on narrow viewport (manual or e2e) — *Frontend*
- [ ] Export standings/history returns correct data (unit or integration) — *Backend*
- [ ] Smoke or e2e: sign in → join league → make pick → view standings — *Both*

---

*Based on [Game_rules.md](Game_rules.md) — Last Man Standing rules.*
