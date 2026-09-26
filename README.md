# Crazy Car

A Streamlit racing championship with 23 circuits, seven cars, five original fictional sponsor logos, and keyboard or touch joystick controls. The dark lime/orange lobby and canvas racing engine retain the original CrazyCar identity.

## Run locally

Python 3.10+ is recommended. No Node build, database, accounts, or external assets are required for gameplay.

```sh
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS/Linux instead: source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit. For Community Cloud, select `app.py` and include `game/`, `game_config.py`, `style.css`, `logo.svg`, and `.streamlit/config.toml` in the deployment.

## Play

Choose your car, sponsor, and COMPUTER / KEYBOARD or MOBILE / JOYSTICK in the lobby. Start from any unlocked level. Select START RACE inside the canvas to focus the game. Every intermediate completion waits for NEXT LEVEL; the final circuit shows CHAMPIONSHIP COMPLETE.

| Desktop key | Action |
|---|---|
| ↑ | Accelerate |
| ↓ | Brake / reverse |
| ← → | Steer |
| R | Restart current level |
| P | Pause / resume |
| Space | Retry while a failure dialog is active |

Choose MOBILE / JOYSTICK before starting. Drag upward to accelerate, left/right to steer, and downward to brake/reverse. Diagonal movement combines acceleration and steering. Release to center. The top-left pause button provides Resume, Restart, and Return to Lobby. Failure dialogs also offer Retry and Return to Lobby.

Only the joystick/canvas suppress touch gestures; the lobby remains scrollable. Portrait uses a following camera and a rotation suggestion. Landscape provides more room. Resizing or losing focus pauses the race and clears input. Enable optional music with the ♪ button; audio starts from a real interaction and never gates gameplay.

## Progress and cars

Progress persists in the current Streamlit session, including restarts and returns to the lobby. A new session/full reload can reset it. Reaching levels 6, 12, 18, and 23 unlocks cars automatically. Red cards remain visible and tappable; their dialogs explain the requirement. BeastHunter unlocks at Level 12.

| Car | Unlock level | Speed label | Handling label |
|---|---:|---|---|
| Blaze GT | 1 | Fast | Balanced |
| Phantom X | 1 | Quick | Sharp |
| Volt RS | 1 | Steady | Grippy |
| Road Reaper | 6 | Fast | Balanced |
| BeastHunter | 12 | Quick | Sharp |
| Night Fang | 18 | Fast | Grippy |
| Apex Titan | 23 | Fast | Sharp |

Speed/handling labels preserve the original cosmetic statistics. All cars use the same base physics: forward maximum 210, reverse maximum 75, acceleration 170, reverse acceleration 150 world units per second squared, and the original speed-sensitive angular steering. Unlocks are visual rewards, not a requirement to beat later circuits.

## Championship

Widths are logical world units, independent of screen size. The original Daytona, Silverstone and Monaco point layouts remain intact, with wider Rookie roads. Twenty fictional routes add increasing length, segment count, tighter bends and narrower roads. Their coordinates are explicit configuration, not random runtime generation. Timers budget distance and corner count with decreasing recovery margin across five bands.

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

## Fictional sponsors

| Sponsor | Logo concept |
|---|---|
| ThunderOil Racing | Lightning bolt and oil drop |
| Apex Dynamics | Angular mountain apex |
| VelocityWear | Speed stripes and V |
| NitroByte Energy | Pixel lightning |
| TitanTrack Motorsports | Track-framed T |

Each configuration contains a single lightweight SVG path design used in lobby branding and a cached `Path2D` roof mark, inside the car's rotation transform. No corporate logos or downloaded images are used.

## Architecture

- `app.py`: Streamlit lobby, car dialogs, mode selection, session progress and component events.
- `game_config.py`: level/car/sponsor configuration and progress/unlock helpers.
- `game/index.html`, `race.css`, `race.js`: one canvas engine and responsive UI.
- `style.css`, `.streamlit/config.toml`: existing racing design and consistent dark theme.

The previous `components.html()` string is now a locally served V1 component declared through `components.declare_component`. Its small bridge implements the Streamlit V1 ready/render/value/frame-height message contract. See [Streamlit component communication](https://docs.streamlit.io/develop/concepts/custom-components/components-v1/intro). A stable race key keeps the iframe alive across completion reruns. Python receives only completion and lobby-exit events; movement stays entirely inside requestAnimationFrame. No parent DOM traversal or iframe button-click hacks are used.

Keyboard and Pointer Events normalize into `{accelerate, brake, steer}`. One physics function consumes that state. Ordered checkpoints supplement the original nearest-centerline collision test to prevent shortcuts and accidental spawn/finish completion. A fixed per-track world and following camera prevent phone rotation from changing collision geometry.

The host uses dynamic viewport CSS with a `vh` fallback. The iframe reads its own viewport, caps device-pixel ratio at 2, and reports height using the component bridge. Joystick pointer capture supports motion outside the base; pointer-up, cancellation, capture loss, blur and visibility changes clear all input. Modals use native buttons, focus management, and a Tab loop. Touch targets are at least 44 pixels.

## Verification and browser support

Actually tested in this Windows environment: installed Chrome and Edge through Playwright, and Chromium touch emulation at 390×844, 430×932, 844×390, 932×430, 768×1024 and 1024×768. Tests cover locked-card click/dialog, sponsor/car selection, keyboard drive, pause invariants, restart/retry, all completion events, milestone unlocks, return-to-lobby persistence, joystick analog/diagonal/reverse input, cancellation, blur and rotation invariants.

Safari iOS, Chrome iOS and Chrome Android are intended support targets, **not real-device tested**. Emulation cannot establish iOS audio policy behavior, browser chrome changes on every device, physical multitouch feel, thermal performance, or sustained 60 FPS. Pointer Events, scoped touch-action, gesture-initiated audio, viewport fallbacks and defensive audio errors are used for compatibility. Google Fonts are optional; local system-font fallbacks remain readable offline.

```sh
python -m unittest discover -s tests -v
# Optional browser checks, with the app running on localhost:8501:
python -m pip install playwright
python tests/browser_check.py
python tests/drive_check.py
```

The browser script requires installed Chrome and Edge. The drive check runs a deterministic centerline controller through the real physics, without teleporting. All 23 routes finish inside their timers; Master circuits require slower cornering. This is a feasibility check, not a substitute for human difficulty tuning. Browser screenshots and feasibility output go to ignored `artifacts/`.

See [implementation report](IMPLEMENTATION.md), [current design](CrazyCarMyDesign.md), and [architecture](md/architecture.md). Editable Mermaid sources are in `documents/`.
