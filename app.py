import base64
import uuid
from game_config import LEVELS, CARS, SPONSORS, is_car_unlocked, apply_progress
import random
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


APP_DIR = Path(__file__).parent


st.set_page_config(page_title = "Crazy Car", page_icon = "🏁", layout = "wide", initial_sidebar_state = "collapsed")


def load_css():
    css_path = APP_DIR / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding="utf-8")}</style>", unsafe_allow_html=True)


def random_username():
    first = ["Racer", "Turbo", "Drift", "Nitro", "Apex", "Road", "Speed"]
    second = ["Falcon", "Nova", "Comet", "Viper", "Rocket", "Blaze", "Phantom"]
    return f"{random.choice(first)}{random.choice(second)}{random.randint(100, 999)}"


def init_state():
    if "username" not in st.session_state:
        st.session_state.username = random_username()
    st.session_state.setdefault("screen", "lobby")
    st.session_state.setdefault("car_id", "blaze")
    st.session_state.setdefault("sponsor", "thunderoil")
    st.session_state.setdefault("highest_level_unlocked", 1)
    st.session_state.setdefault("control_mode", "keyboard")
    st.session_state.setdefault("race_id", "")
    st.session_state.setdefault("last_event", None)


def logo_html():
    logo = (APP_DIR / "logo.svg").read_text() if (APP_DIR / "logo.svg").exists() else ""
    encoded = base64.b64encode(logo.encode()).decode()
    return f'<img class="logo" src="data:image/svg+xml;base64,{encoded}" alt="Crazy Car logo">'


@st.dialog("CAR LOCKED")
def locked_car_dialog(car):
    st.write("You cannot get this right now.")
    st.write(f"Get to Level {car['unlock_level']} to unlock {car['name']}.")
    if st.button("GOT IT", use_container_width=True):
        st.rerun()


def car_card(car_id, car):
    locked = not is_car_unlocked(car_id, st.session_state.highest_level_unlocked)
    selected = "locked" if locked else "selected" if st.session_state.car_id == car_id else ""
    st.markdown(
        f'''<div class="car-card {selected}"><div class="car-preview" style="--car:{car["color"]};--accent:{car["accent"]}">
        <span>{"🔒" if locked else car["emoji"]}</span><b>CRAZY</b></div><div class="car-name">{car["name"]}</div>
        <div class="car-stats"><span>Speed<br><b>{car["speed"]}</b></span><span>Control<br><b>{car["handling"]}</b></span></div></div>''',
        unsafe_allow_html=True,
    )
    if locked:
        st.caption(f"🔒 UNLOCKS LEVEL {car['unlock_level']}")
    if st.button(f"{'🔒 View' if locked else 'Select'} {car['name']}", key=f"car_{car_id}", use_container_width=True):
        if locked:
            locked_car_dialog(car)
            return
        st.session_state.car_id = car_id
        st.rerun()



@st.dialog(":blue[GAME CREDITS]", width="small")
def credits_dialog():
    st.markdown(
        """
        <style>
        div[role="dialog"] {
            background: var(--panel) !important;
            border: 1px solid var(--blue) !important;
            border-radius: 0 !important;
        }
        div[role="dialog"] h2 {
            color: var(--blue) !important;
            font-family: 'Barlow Condensed', sans-serif !important;
            font-size: 38px !important;
            font-weight: bold;
            letter-spacing: 2px;
            text-transform: uppercase;
        }
        .credits-copy {
            color: var(--muted);
            font-family: 'Space Mono', monospace;
            font-size: 11px;
            line-height: 1.7;
            text-align: center;
        }
        .credit-item {
            border-top: 1px solid #333a35;
            padding: 14px 0;
        }
        .credit-item:first-child { border-top: 0; }
        .credit-label {
            color: var(--muted);
            display: block;
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }
        </style>
        <div class="credits-copy">
            <div class="credit-item">
                <span class="credit-label">CSS STYLE SHEET CODE</span>
                Divij with help of a coding assistant, CODEX
            </div>
            <div class="credit-item">
                <span class="credit-label">GAME DESIGN AND GAME FLOW</span>
                Divij
            </div>
            <div class="credit-item">
                <span class="credit-label">TOOLS AND PROGRAMMING</span>
                HTML, CSS, PYTHON, GITHUB, and STREAMLIT COMMUNITY CLOUD
            </div>
            <div class="credit-item">
                <span class="credit-label">AUDIO</span>
                Web Audio API
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("BACK TO LOBBY", key="back_to_lobby", use_container_width=True):
        st.rerun()

def lobby():
    st.markdown('<div class="topbar">' + logo_html() + '<span class="online">● READY TO RACE</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hero"><div class="eyebrow">WELCOME BACK, {st.session_state.username.upper()}</div><h1><span style="color: white;">Own the<br><em>circuit</em></span></h1><p>{len(LEVELS)} circuits. One championship. Keep your tires on the tarmac.</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">01 / CHOOSE YOUR MACHINE</div>', unsafe_allow_html=True)
    st.caption(f"LEVEL {st.session_state.highest_level_unlocked:02d} / {len(LEVELS)} UNLOCKED")
    car_items = list(CARS.items())
    for offset in range(0, len(car_items), 3):
        cols = st.columns(3, gap="large")
        for col, (car_id, car) in zip(cols, car_items[offset:offset + 3]):
            with col:
                with st.container(key=f"car_tile_{car_id}"):
                    car_card(car_id, car)
    st.markdown('<div class="section-label">02 / PICK YOUR SPONSOR</div>', unsafe_allow_html=True)
    sponsor_cols = st.columns(len(SPONSORS), gap="small")
    for col, (sponsor_id, sponsor) in zip(sponsor_cols, SPONSORS.items()):
        with col:
            selected = st.session_state.sponsor == sponsor_id
            st.markdown(f'<div class="sponsor-logo">{sponsor["logo"]}</div>', unsafe_allow_html=True)
            if st.button(sponsor['name'], key=f"sponsor_{sponsor_id}", type="primary" if selected else "secondary", use_container_width=True):
                st.session_state.sponsor = sponsor_id
                st.rerun()
    st.markdown(f'<div class="sponsor-chip">SPONSORED BY <strong>{SPONSORS[st.session_state.sponsor]["name"]}</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">03 / CHOOSE YOUR CONTROLS</div>', unsafe_allow_html=True)
    st.radio("Control mode", ["keyboard", "joystick"], format_func=lambda mode: "COMPUTER / KEYBOARD" if mode == "keyboard" else "MOBILE / JOYSTICK", key="control_mode", horizontal=True)
    start_level = st.selectbox("Start at an unlocked level", range(1, st.session_state.highest_level_unlocked + 1), index=st.session_state.highest_level_unlocked - 1, format_func=lambda n: f"Level {n}: {LEVELS[n-1]['name']}")
    st.markdown('<div class="launch-row">', unsafe_allow_html=True)
    if st.button("START CHAMPIONSHIP  →", type="primary", use_container_width=True):
        st.session_state.start_level = start_level
        st.session_state.race_id = uuid.uuid4().hex
        st.session_state.screen = "race"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.caption("↑ accelerate · ↓ reverse · ← → steer · R restart · P pause · Space retry" if st.session_state.control_mode == "keyboard" else "Drag the joystick up to accelerate, left/right to steer, down to reverse.")
    _, credits_col = st.columns([5, 1])
    with credits_col:
        if st.button("CREDITS", key="open_credits", use_container_width=True):
            credits_dialog()


race_component = components.declare_component("crazycar_race", path=str(APP_DIR / "game"))


def race():
    config = dict(username=st.session_state.username, sponsor=SPONSORS[st.session_state.sponsor],
                  car=CARS[st.session_state.car_id], tracks=LEVELS,
                  controlMode=st.session_state.control_mode, startLevel=st.session_state.start_level,
                  raceId=st.session_state.race_id)
    st.markdown('<style>.block-container{padding-top:8px!important;padding-bottom:0!important}iframe{height:calc(100vh - 90px)!important;height:calc(100dvh - 90px)!important;min-height:260px}header[data-testid="stHeader"]{display:none}</style>', unsafe_allow_html=True)
    event = race_component(config=config, key=st.session_state.race_id, default=None)
    if isinstance(event, dict) and event.get("raceId") == st.session_state.race_id:
        event_id = event.get("eventId")
        if event_id != st.session_state.last_event:
            st.session_state.last_event = event_id
            st.session_state.highest_level_unlocked = apply_progress(
                st.session_state.highest_level_unlocked, event.get("completed"))
            if event.get("action") == "lobby":
                st.session_state.screen = "lobby"
                st.rerun()


load_css()
init_state()
if st.session_state.screen == "lobby":
    lobby()
else:
    race()