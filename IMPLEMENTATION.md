# CrazyCar implementation report

## Git-style summary

`feat: expand CrazyCar to 23 circuits with session unlocks, sponsor roof logos and mobile controls`

Preserves Streamlit, Canvas, the original track coordinates, cars/sponsors and physics model. Extracts the browser engine into a local V1 component with completion/exit events, unifies keyboard/pointer input, and adds responsive pause/retry/progression flows.

## Changed files

- `app.py`
- `style.css`
- `requirements.txt` (minimum Streamlit 1.40 for the existing stable dialog API; major version bounded)
- `README.md`
- `CrazyCarMyDesign.md`
- `md/architecture.md`
- `md/class.md`
- `md/graph.md`
- `md/sequence.md`
- `md/state.md`
- `documents/architecture.mmd`
- `documents/class.mmd`
- `documents/graph.mmd`
- `documents/sequence.mmd`
- `documents/state.mmd`

## New files

- `.gitignore`
- `.streamlit/config.toml`
- `game_config.py`
- `game/index.html`
- `game/race.css`
- `game/race.js`
- `tests/test_config.py`
- `tests/test_lobby.py`
- `tests/browser_check.py`
- `tests/drive_check.py`
- `IMPLEMENTATION.md`

Ignored local verification artifacts: `.venv/`, `.test-deps/`, `artifacts/`, Python bytecode. No Git commit was made; the Git executable was unavailable on PATH.

## Levels

| # | Circuit | Road width | Time (s) | Difficulty |
|---:|---|---:|---:|---|
| 1 | Daytona | 88 | 60 | Rookie |
| 2 | Silverstone | 86 | 63 | Rookie |
| 3 | Monaco | 84 | 68 | Rookie |
| 4 | Desert Rush | 85 | 68 | Rookie |
| 5 | Neon Harbor | 80 | 64 | Amateur |
| 6 | Alpine Run | 78 | 67 | Amateur |
| 7 | Canyon Strike | 77 | 66 | Amateur |
| 8 | Thunder Valley | 75 | 68 | Amateur |
| 9 | Midnight Circuit | 73 | 68 | Amateur |
| 10 | Glacier Pass | 70 | 66 | Pro |
| 11 | Crimson Ridge | 68 | 66 | Pro |
| 12 | Storm Coast | 67 | 68 | Pro |
| 13 | Inferno Ring | 65 | 67 | Pro |
| 14 | Copper Mesa | 63 | 69 | Pro |
| 15 | Aurora Bend | 62 | 65 | Elite |
| 16 | Ember Canyon | 60 | 67 | Elite |
| 17 | Obsidian Run | 58 | 66 | Elite |
| 18 | Solar Crest | 57 | 68 | Elite |
| 19 | Tempest Ridge | 55 | 68 | Elite |
| 20 | Vortex Coast | 54 | 65 | Master |
| 21 | Lunar Switchback | 51 | 65 | Master |
| 22 | Dragon Summit | 49 | 66 | Master |
| 23 | Crown Circuit | 46 | 66 | Master |

## Cars

| Car | Unlock level | Speed label | Handling label |
|---|---:|---|---|
| Blaze GT | 1 | Fast | Balanced |
| Phantom X | 1 | Quick | Sharp |
| Volt RS | 1 | Steady | Grippy |
| Road Reaper | 6 | Fast | Balanced |
| BeastHunter | 12 | Quick | Sharp |
| Night Fang | 18 | Fast | Grippy |
| Apex Titan | 23 | Fast | Sharp |

These statistics are labels, as in the original implementation; cars share the same physical capabilities.

## Sponsors

| Sponsor | Logo concept |
|---|---|
| ThunderOil Racing | Lightning bolt and oil drop |
| Apex Dynamics | Angular mountain apex |
| VelocityWear | Speed stripes and V |
| NitroByte Energy | Pixel lightning |
| TitanTrack Motorsports | Track-framed T |

## Input and mobile implementation

Keyboard arrows and Pointer Events feed a shared `{accelerate, brake, steer}` state. Physics consumes only those normalized values. The joystick captures its pointer, clamps its radius, applies a dead zone, supports diagonals and clears on cancellation. Blur/visibility changes pause safely. Native dialog buttons and keyboard focus management serve both modes; Space retries failures only.

The host uses dynamic viewport CSS and the iframe reads its own viewport, with no parent DOM traversal. A fixed world and following camera preserve geometry during orientation changes. The roof mark rotates with the car. Audio is optional and gesture-initiated, with errors caught and resources cleaned up.

## Tests performed

- Python compilation and JavaScript syntax check.
- Six unittest/AppTest tests: configuration, non-crossing routes and bounds, IDs, car requirements, sponsor uniqueness, progress clamping and lobby unlock state.
- Installed Chrome and Edge via Playwright: locked card/dialog, car/sponsor selection, arrow movement, pause invariants, restart, Space retry, timeout, all completion events and final championship, unlock milestones and session progress after returning to lobby.
- Chromium touch emulation at all six requested dimensions: analog steering/acceleration/reverse, diagonal input, release/cancel, scoped gesture handling, pause/restart/exit, orientation invariants, horizontal overflow.
- Deterministic driver through actual physics: all 23 routes complete within their timers. Master runs finish in approximately 55–58.4 seconds with 7.6–10 seconds remaining. No teleporting in this feasibility test.

The integration progression test moves the car to ordered checkpoints to exercise event handling quickly; the separate drive test establishes continuous-physics route feasibility. These are explicitly different checks.

## Remaining limitations

Safari iOS, Chrome iOS and Chrome Android are intended targets, not tested on physical devices. Chromium touch emulation does not certify WebKit, audio policy behavior, actual multitouch feel or sustained 60 FPS. Human difficulty balance and device performance require further playtesting. Session progress may reset on a new Streamlit session/full reload, as requested. Online Google Fonts are optional and have local fallbacks.

## Local commands

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

```powershell
python -m unittest discover -s tests -v
python -m pip install playwright
# Keep Streamlit running on localhost:8501; Chrome and Edge must be installed.
python tests/browser_check.py
python tests/drive_check.py
```

In this workspace the isolated environment is already prepared, so `.\.venv\Scripts\python.exe -m streamlit run app.py` runs directly.
