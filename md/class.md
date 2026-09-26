# CrazyCar class

Current implementation; source is `app.py`, `game_config.py` and `game/`.

```mermaid
classDiagram
    class SessionState {
        username
        screen
        car_id
        sponsor
        control_mode
        highest_level_unlocked
        race_id
        last_event
    }
    class Level {
        id
        number
        name
        subtitle
        road_width
        points
        world_width
        world_height
        time_limit
        difficulty
        steering_modifier
    }
    class Car {
        name
        color
        accent
        speed
        handling
        unlock_level
    }
    class Sponsor {
        name
        short_name
        color
        logo
        logo_path
    }
    class BrowserRace {
        loadLevel()
        resetCurrentLevel()
        updateJoystickInput()
        setKeyboardInput()
        updatePhysics()
        drawCar()
        openPauseMenu()
        completeLevel()
        emitEvent()
    }
    SessionState --> Car
    SessionState --> Sponsor
    BrowserRace --> Level
    BrowserRace --> Sponsor
    BrowserRace --> SessionState : completion and exit events
```
