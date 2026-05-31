# Smart-Env

Local control for a candle warmer via a TP-Link Kasa smart plug. The repository contains a FastAPI web dashboard and a standalone CLI script. Both turn the plug on and off over the LAN; the web app can also schedule an automatic shutoff after a fixed duration.

There is no microcontroller firmware, servo control, sensor integration, or cloud backend in this repository.

## Features

### Web dashboard

Serves a single HTML page at `GET /` that shows the plug alias and current on/off state. State is fetched from the plug on every page load via `python-kasa`.

**Technologies:** FastAPI, Jinja2 templates, static CSS.

### Timed turn-on (web)

`POST /on-timer` turns the plug on, then schedules an in-process task to turn it off after `TIMER_MINUTES` (120). The dashboard exposes this as **Turn On (120 min)**.

**Technologies:** FastAPI, `asyncio.create_task`, `python-kasa`.

### Manual turn-off (web)

`POST /off` turns the plug off immediately. The dashboard exposes this as **Turn Off**.

**Technologies:** FastAPI, `python-kasa`.

### Turn-on without timer (API only)

`POST /on` turns the plug on with no auto-off. This route exists in `app.py` but is not linked from the dashboard UI.

**Technologies:** FastAPI, `python-kasa`.

### CLI timed session

`plug_timer.py` prompts for a duration in minutes, runs `kasa --host <IP> on`, blocks with `time.sleep`, then runs `kasa --host <IP> off`. This is independent of the web app.

**Technologies:** Python stdlib (`subprocess`, `time`), `kasa` CLI from the `python-kasa` package.

## Hardware

| Device | Role in this repo | Notes |
|--------|-------------------|-------|
| TP-Link Kasa smart plug | Controlled device | IP hardcoded as `192.168.1.183` in source |
| Candle warmer | Load on the plug | Referenced in UI copy only; not controlled directly |

**Not present in the codebase:**

- ESP32 or other microcontroller
- SG90 servo or other actuators
- Sensors (temperature, light, motion, etc.)

Control is limited to switching power to whatever is plugged into the Kasa outlet.

## Project Structure

```
smart-env/
├── LICENSE
├── README.md
├── .gitignore
└── candle_warmer/
    ├── app.py              # FastAPI app: routes, timer logic, template rendering
    ├── kasa_control.py     # Async plug discovery and on/off/state via python-kasa
    ├── plug_timer.py       # Blocking CLI script using the kasa command-line tool
    ├── templates/
    │   └── index.html      # Dashboard markup and form actions
    └── static/
        └── style.css       # Dashboard styles
```

There is no `requirements.txt`, `pyproject.toml`, Docker config, or test directory.

## Setup

### Python version

The repo does not pin a Python version in code. `.gitignore` references `.venv312/`, which indicates local development on Python 3.12. Use Python 3.10 or newer (required by recent `python-kasa` releases).

### Virtual environment

From the repository root:

```bash
python3.12 -m venv .venv312
source .venv312/bin/activate
```

### Install dependencies

There is no dependency manifest in the repo. Install packages inferred from imports:

```bash
pip install fastapi uvicorn python-kasa
```

`Jinja2` is pulled in as a FastAPI dependency for `Jinja2Templates`.

For `plug_timer.py`, the `kasa` CLI must be on your `PATH` (installed with `python-kasa`).

### Configuration

There are no environment variables. Set the plug IP in source:

| File | Variable | Default |
|------|----------|---------|
| `candle_warmer/kasa_control.py` | `PLUG_IP` | `"192.168.1.183"` |
| `candle_warmer/plug_timer.py` | `PLUG_IP` | `"192.168.1.183"` |

Timer duration for the web app is set in `candle_warmer/app.py`:

```python
TIMER_MINUTES = 120
```

The plug must be reachable on the same LAN as the machine running the app.

### Run the web app

The app uses relative paths for `static/` and `templates/`, and imports `kasa_control` as a local module. Run from `candle_warmer/`:

```bash
cd candle_warmer
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`.

### Run the CLI timer

```bash
cd candle_warmer
python plug_timer.py
```

Enter the desired runtime in minutes when prompted.

## How It Works

### Device communication

`kasa_control.py` calls `Discover.discover_single(PLUG_IP)` on each operation, then `plug.update()` to refresh state. It exposes three async functions used by the web app:

- `get_state()` → `{ "name": plug.alias, "is_on": plug.is_on }`
- `turn_on()` → `plug.turn_on()`
- `turn_off()` → `plug.turn_off()`

If discovery returns `None`, it raises `RuntimeError`.

`plug_timer.py` does not use `kasa_control.py`. It shells out to:

```bash
kasa --host <PLUG_IP> on|off
```

### Web control flow

1. `GET /` calls `get_state()` and renders `index.html` with the result and `timer_minutes`.
2. **Turn On (120 min)** submits `POST /on-timer`:
   - Calls `turn_on()`.
   - Starts `asyncio.create_task(delayed_off)` where `delayed_off` sleeps `TIMER_MINUTES * 60` seconds, then calls `turn_off()`.
   - Redirects to `/` with HTTP 303.
3. **Turn Off** submits `POST /off`, calls `turn_off()`, redirects to `/`.

All POST handlers redirect back to the dashboard; there is no JSON API.

### Scheduling logic

The only automation is the single in-memory timer in `on_timer()`. There is no cron, job queue, persistence, or UI to change the duration at runtime. Submitting `/on-timer` again while a timer is already running starts a second independent task; the code does not cancel or track previous timers.

### Servo control

Not implemented. No servo, GPIO, or microcontroller code exists in the repository.

### API interactions

| Method | Path | UI | Behavior |
|--------|------|----|----------|
| `GET` | `/` | Yes | Render dashboard with current plug state |
| `POST` | `/on-timer` | Yes | Turn on; schedule auto-off after `TIMER_MINUTES` |
| `POST` | `/off` | Yes | Turn off immediately |
| `POST` | `/on` | No | Turn on with no timer |
| — | `/static/*` | Yes | Serve CSS |

External API usage is limited to LAN communication with the Kasa plug via `python-kasa` or the `kasa` CLI. No third-party cloud services are called from this code.

## Current Limitations

- **Hardcoded IP** — `PLUG_IP` is duplicated in two files; no env-based config.
- **No dependency lockfile** — versions are not pinned in the repository.
- **Volatile timer** — auto-off runs in a background task; restarting the server cancels pending shutoffs.
- **No timer deduplication** — multiple `/on-timer` requests create overlapping off tasks.
- **No error UI** — plug discovery failures surface as unhandled server errors, not user-facing messages.
- **Blocking CLI** — `plug_timer.py` uses `time.sleep` and holds the terminal for the full duration.
- **Redundant discovery** — every state read and toggle re-runs `discover_single`.
- **Partial API exposure** — `POST /on` is implemented but not available from the dashboard.
- **No tests, CI, or deployment config** in the repository.
- **No actuator or sensor support** — power switching only.

## Roadmap

Possible future work (not implemented):

- Physical button actuator (e.g. ESP32 + SG90 servo) for warmers without a smart plug
- Brightness or dimming control
- Environmental sensors (temperature, occupancy, etc.)
- Configurable timer duration from the UI
- Persistent scheduling and timer recovery after restart
- Environment-based configuration (`PLUG_IP`, `TIMER_MINUTES`)
- Dependency manifest and deployment docs

## Technologies Used

| Technology | Where used |
|------------|------------|
| [FastAPI](https://fastapi.tiangolo.com/) | HTTP server and routes (`app.py`) |
| [Uvicorn](https://www.uvicorn.org/) | ASGI server (run manually; not imported in code) |
| [Jinja2](https://jinja.palletsprojects.com/) | HTML templating via FastAPI |
| [python-kasa](https://github.com/python-kasa/python-kasa) | LAN plug control (`kasa_control.py`) |
| `asyncio` | In-process auto-off timer (`app.py`) |
| HTML / CSS | Dashboard UI (`templates/`, `static/`) |
| `kasa` CLI | Alternative control path (`plug_timer.py`) |

## License

MIT License. Copyright (c) 2026 Trang Nguyen. See [LICENSE](LICENSE).
