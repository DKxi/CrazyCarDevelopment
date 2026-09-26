# Crazy Car

Run with:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL in Edge or Chrome. The race is rendered in a Streamlit HTML canvas component, so arrow-key input is handled directly in the browser.

## How the game works

- **Difficulty:** Daytona is wide and short, Silverstone is longer and medium-width, and Monaco is longest and narrowest.
- **Tracks:** Each level has a different list of points. The browser draws a smooth road by connecting those points and drawing a thick road over the grass.
- **Road shrinking:** Every level uses a smaller road width, so the same car physics require more accurate steering.
- **Physics:** Up and Down change speed along the car's forward vector. Left and Right change the car angle. There is no sideways movement, which keeps steering predictable.
- **Sponsors:** The selected fictional sponsor is sent into the race component and painted on the car, HUD, and lobby.
- **Username:** A new adjective/name/number combination is generated whenever the Streamlit session starts or the page is refreshed.
- **Music:** The component uses the Web Audio API to synthesize two lightweight looping themes. Calm notes play in the lobby; bass and faster notes play while racing.
- **Flow:** Lobby → level 1 → automatic level 2 → automatic level 3 → finish screen. Leaving the road ends the current run.


![Architecture](./md/architecture.md)
![Graph](./md/graph.md)
![Class](./md/class.md)
![Sequence](./md/sequence.md)
![State](./md/state.md)
