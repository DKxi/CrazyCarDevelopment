# CrazyCar architecture

Current implementation; source is `app.py`, `game_config.py` and `game/`.

```mermaid
flowchart TD
    App[Streamlit app.py] --> Lobby[Lobby and locked-car dialogs]
    App --> Session[Session progress and selections]
    Config[game_config.py: levels cars sponsors] --> App
    Lobby --> Mode[Control mode selection]
    Mode --> Race[Local V1 canvas component]
    Race --> Keyboard[Keyboard input]
    Race --> Joystick[Pointer joystick]
    Keyboard --> Input[Unified analog input state]
    Joystick --> Input
    Input --> Physics[Original driving physics and ordered checkpoints]
    Physics --> Render[Canvas and sponsor roof logo]
    Physics --> Results[Pause failure and completion menus]
    Results -->|completion or lobby event| Session
    Session -->|unlock cars at configured level| Lobby
```
