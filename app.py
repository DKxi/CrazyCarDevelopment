import base64
import json
import random
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


APP_DIR = Path(__file__).parent

# Time allowed for circuits 1, 2, and 3, in seconds.
TIME_LIMITS = [60, 60, 60]

st.set_page_config(page_title = "Crazy Car", page_icon = "🏁", layout = "wide", initial_sidebar_state = "collapsed")


def load_css():
    css_path = APP_DIR / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def random_username():
    first = ["Racer", "Turbo", "Drift", "Nitro", "Apex", "Road", "Speed"]
    second = ["Falcon", "Nova", "Comet", "Viper", "Rocket", "Blaze", "Phantom"]
    return f"{random.choice(first)}{random.choice(second)}{random.randint(100, 999)}"


def init_state():
    if "username" not in st.session_state:
        st.session_state.username = random_username()
    st.session_state.setdefault("screen", "lobby")
    st.session_state.setdefault("car_id", "blaze")
    st.session_state.setdefault("sponsor", "ThunderOil Racing")


def logo_html():
    logo = (APP_DIR / "logo.svg").read_text() if (APP_DIR / "logo.svg").exists() else ""
    encoded = base64.b64encode(logo.encode()).decode()
    return f'<img class="logo" src="data:image/svg+xml;base64,{encoded}" alt="Crazy Car logo">'


CARS = {
    "blaze": {
        "name": "Blaze GT",
        "color": "#ff5c35",
        "accent": "#ffd166",
        "speed": "Fast",
        "handling": "Balanced",
        "emoji": "🔥"
    },
    "phantom": {
        "name": "Phantom X",
        "color": "#7c6cff",
        "accent": "#62e6ff",
        "speed": "Quick",
        "handling": "Sharp",
        "emoji": "👻"
    },
    "volt": {
        "name": "Volt RS",
        "color": "#d9f047",
        "accent": "#102020",
        "speed": "Steady",
        "handling": "Grippy",
        "emoji": "⚡"
    },
}
SPONSORS = ["ThunderOil Racing", "Apex Dynamics", "VelocityWear", "NitroByte Energy", "TitanTrack Motorsports"]


# The complete race lives in a small browser canvas embedded by Streamlit.
# This keeps the game loop simple and makes arrow - key controls feel immediate.
RACE_HTML = r'''
<style>
html,body{margin:0;background:#0c0f0e;color:#f4f1e8;font-family:monospace;overflow:hidden}#wrap{position:relative;width:100%;height:650px;background:#111814;overflow:hidden}canvas{display:block;width:100%;height:100%;background:#18231b}.hud{position:absolute;top:18px;left:22px;right:22px;display:flex;justify-content:space-between;pointer-events:none}.hudbox{background:rgba(12,15,14,.82);border-left:3px solid #d9f047;padding:10px 14px;min-width:130px}.label{font-size:10px;color:#8c918e;letter-spacing:1px}.value{font-size:19px;color:#d9f047;font-weight:bold;margin-top:5px}.center{text-align:center}.hint{position:absolute;bottom:18px;left:22px;color:#c8cec5;background:rgba(12,15,14,.75);padding:9px 12px;font-size:11px}.timer{position:absolute;right:22px;bottom:18px;background:rgba(12,15,14,.88);border-right:3px solid #ff5c35;padding:10px 14px;text-align:right}.timer .value{color:#ffb347;font-size:24px}.timer.warning .value{color:#ff5c35}.resolution{color:#8c918e;font-size:8px;margin-top:4px}.modal{position:absolute;inset:0;display:none;align-items:center;justify-content:center;background:rgba(8,11,9,.78);text-align:center}.modal.show{display:flex}.panel{background:#191d1b;border:1px solid #d9f047;padding:30px 45px;min-width:310px}.panel h1{font:700 48px Arial;margin:8px 0;color:#d9f047}.panel p{color:#b4bbb3;font-size:12px;line-height:１.6}.panel button{background:#d9f047;border:0;padding:１3px 25px;font:bold １２px monospace;cursor:pointer;margin-top:８px}
</style> <div id="wrap"><canvas id="game"></canvas>
<div class="hud"><div class="hudbox"><div class="label">DRIVER</div><div class="value" id="driver"></div></div><div class="hudbox center"><div class="label">CIRCUIT <span id="level"></span></div><div class="value" id="track"></div></div><div class="hudbox" style="text-align:right"><div class="label">SPONSOR</div><div class="value" id="sponsor" style="font-size:12px"></div></div></div>
<div class="hint">↑ ACCELERATE &nbsp; ↓ REVERSE &nbsp; ← → STEER &nbsp; R RESTART &nbsp; P PAUSE</div><div class="timer" id="timer"><div class="label">TIME REMAINING</div><div class="value" id="timeValue"></div><div class="resolution" id="resolution"></div></div>
<div id="modal" class="modal"><div class="panel"><div class="label" id="modalLabel"></div><h1 id="modalTitle"></h1><p id="modalText"></p><button id="modalButton"></button></div></div></div>
<script>
const config=__CONFIG__; const canvas=document.getElementById('game'),ctx=canvas.getContext('2d');
document.getElementById('driver').textContent=config.username; document.getElementById('sponsor').textContent=config.sponsor;
// Each route is an open path: the final point must be different from the start.
// Otherwise a new circuit would immediately detect the car at its own finish line.
const tracks=[{name:'Daytona',full:'INTERNATIONAL SPEEDWAY',width:78,points:[[.18,.55],[.16,.25],[.35,.12],[.72,.14],[.87,.30],[.84,.70],[.68,.87],[.30,.86],[.13,.70]]},{name:'Silverstone',full:'CIRCUIT',width:62,points:[[.15,.28],[.35,.15],[.65,.18],[.86,.35],[.72,.52],[.86,.74],[.62,.85],[.38,.72],[.18,.84],[.28,.56]]},{name:'Monaco',full:'GRAND PRIX CIRCUIT',width:47,points:[[.12,.76],[.18,.50],[.12,.25],[.35,.18],[.46,.32],[.62,.18],[.88,.25],[.76,.44],[.88,.65],[.62,.78],[.52,.62],[.35,.80]]}];
let level=0, road=[], player={x:0,y:0,a:0,s:0},keys={},running=true,paused=false,last=0, audio=null,timeLeft=0;

function resize(){canvas.width=canvas.clientWidth*devicePixelRatio;canvas.height=canvas.clientHeight*devicePixelRatio;ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0);document.getElementById('resolution').textContent='BROWSER '+window.innerWidth+'×'+window.innerHeight+' · SCREEN '+screen.width+'×'+screen.height;buildRoad()} window.addEventListener('resize',resize);
function buildRoad(){const t=tracks[level],w=canvas.clientWidth,h=canvas.clientHeight;road=t.points.map(p=>({x:p[0]*w,y:p[1]*h})); if(!player.x){player.x=road[0].x;player.y=road[0].y;player.a=Math.atan2(road[1].y-road[0].y,road[1].x-road[0].x)}}
function music(racing){if(audio)audio.close();try{audio=new (window.AudioContext||window.webkitAudioContext)();let notes=racing?[440, 494, 523, 587]:[262,330,392,330],i=0;setInterval(()=>{if(!audio||audio.state==='closed')return;let o=audio.createOscillator(),g=audio.createGain();o.frequency.value=notes[i++%notes.length];o.type=racing?'square':'triangle';g.gain.setValueAtTime(.0001,audio.currentTime);g.gain.exponentialRampToValueAtTime(racing?.035:.018,audio.currentTime+.03);g.gain.exponentialRampToValueAtTime(.0001,audio.currentTime+.28);o.connect(g).connect(audio.destination);o.start();o.stop(audio.currentTime+.3)},racing?260:620)}catch(e){}}
function pointDistance(x,y){let best=Infinity;for(let i=0;i<road.length-1;i++){let a=road[i],b=road[i+1],dx=b.x-a.x,dy=b.y-a.y,t=Math.max(0,Math.min(1,((x-a.x)*dx+(y-a.y)*dy)/(dx*dx+dy*dy)));best=Math.min(best,Math.hypot(x-(a.x+t*dx),y-(a.y+t*dy)))}return best}
function draw(){let w=canvas.clientWidth,h=canvas.clientHeight,t=tracks[level];ctx.clearRect(0,0,w,h);ctx.fillStyle='#17231a';ctx.fillRect(0,0,w,h);ctx.strokeStyle='#223227';ctx.lineWidth=2;for(let x=0;x<w;x+=42){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,h);ctx.stroke()}for(let y=0;y<h;y+=42){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke()};ctx.lineCap='round';ctx.lineJoin='round';ctx.beginPath();road.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.strokeStyle='#0b0d0c';ctx.lineWidth=t.width+14;ctx.stroke();ctx.strokeStyle='#66706a';ctx.lineWidth=t.width;ctx.stroke();ctx.setLineDash([18,18]);ctx.strokeStyle='#a8b0a6';ctx.lineWidth=2;ctx.stroke();ctx.setLineDash([]);ctx.fillStyle='#d9f047';ctx.font='bold 12px monospace';ctx.fillText('START',road[0].x-20,road[0].y-25);drawCar()}
function drawCar(){ctx.save();ctx.translate(player.x,player.y);/* The sprite points up locally, so add 90 degrees to match the physics vector. */ctx.rotate(player.a+Math.PI/2);let c=config.car;color(c.color,c.accent);ctx.fillStyle=c.color;ctx.beginPath();ctx.roundRect(-13,-23,26,46,7);ctx.fill(); ctx.fillStyle=c.accent; ctx.fillRect(-9,-7,18,9); ctx.fillStyle='#111'; ctx.fillRect(-10,-17,20,7); ctx.fillRect(-10,11,20,7); ctx.fillStyle='#f4f1e8'; ctx.font='bold 6px monospace'; ctx.rotate(-Math.PI/2); ctx.fillText(config.sponsor.substring(0,8),-22,3); ctx.restore()}
function color(){}


function modal(title,text,label,button,action){document.getElementById('modalTitle').textContent=title;document.getElementById('modalText').textContent=text;document.getElementById('modalLabel').textContent=label;document.getElementById('modalButton').textContent=button;document.getElementById('modalButton').onclick=action;document.getElementById('modal').classList.add('show')}
function updateTimer(){let seconds=Math.max(0,Math.ceil(timeLeft));document.getElementById('timeValue').textContent=String(Math.floor(seconds/60)).padStart(2,'0')+':'+String(seconds%60).padStart(2,'0');document.getElementById('timer').classList.toggle('warning',seconds<=10)}
function reset(){player.x=road[0].x;player.y=road[0].y;player.s=0;player.a=Math.atan2(road[1].y-road[0].y,road[1].x-road[0].x);timeLeft=config.timeLimits[level];running=true;paused=false;document.getElementById('modal').classList.remove('show');updateTimer();music(true)}
function next(){
  if(level<2){
    // Close the old result modal first, then build and start the next circuit.
    document.getElementById('modal').classList.remove('show');
    level++;
    document.getElementById('level').textContent='0'+(level+1);
    document.getElementById('track').textContent=tracks[level].name.toUpperCase();
    road=[];
    player.x=null;
    buildRoad();
    reset();
  }else{
    // The final modal uses this same handler for RACE AGAIN.
    // Restart the championship at Daytona instead of opening the modal again.
    document.getElementById('modal').classList.remove('show');
    level=0;
    document.getElementById('level').textContent='01';
    document.getElementById('track').textContent=tracks[0].name.toUpperCase();
    road=[];
    player.x=null;
    buildRoad();
    reset();
  }
}
function loop(now){let dt=Math.min((now-last)/1000,.04);last=now;if(running&&!paused){timeLeft-=dt;updateTimer();if(timeLeft<=0){timeLeft=0;running=false;updateTimer();modal('TIME EXPIRED','The countdown reached zero before you crossed the finish line.','CIRCUIT LOST','PLAY AGAIN',reset)}if(running&&keys.ArrowLeft)player.a-=2.5*dt*(Math.abs(player.s)/80+.35);if(running&&keys.ArrowRight)player.a+=2.5*dt*(Math.abs(player.s)/80+.35);if(running&&keys.ArrowUp)player.s=Math.min(player.s+170*dt,210);else if(running&&keys.ArrowDown)player.s=Math.max(player.s-150*dt,-75);else player.s*=.985;if(running){player.x+=Math.cos(player.a)*player.s*dt;player.y+=Math.sin(player.a)*player.s*dt;if(pointDistance(player.x,player.y)>tracks[level].width/2-8){running=false;modal('OFF TRACK','The tires left the tarmac. Reset and find a cleaner line.','RUN OVER','TRY AGAIN',reset)}let end=Math.hypot(player.x-road[road.length-1].x,player.y-road[road.length-1].y)<tracks[level].width/1.4;if(end){running=false;modal(level<2?'CIRCUIT COMPLETE':'CHAMPIONSHIP COMPLETE',level<2?'Next circuit loading automatically.':'You mastered every circuit.','CHECKERED FLAG',level<2?'NEXT CIRCUIT':'RACE AGAIN',next)}}}draw();requestAnimationFrame(loop)}
function resumeGame(){paused=false;document.getElementById('modal').classList.remove('show')}
window.addEventListener('keydown',e=>{if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight',' '].includes(e.key))e.preventDefault();keys[e.key]=true;if(e.key.toLowerCase()==='r'&&running)reset();if(e.key.toLowerCase()==='p'&&running&&!paused){paused=true;modal('GAME PAUSED','Your car and countdown are paused. Resume when you are ready.','PAUSED','RESUME',resumeGame)}});window.addEventListener('keyup',e=>keys[e.key]=false);document.getElementById('level').textContent='01';document.getElementById('track').textContent=tracks[0].name.toUpperCase();timeLeft=config.timeLimits[0];resize();updateTimer();music(true);requestAnimationFrame(loop);
</script>'''


def car_card(car_id, car):
    selected = "selected" if st.session_state.car_id == car_id else ""
    st.markdown(
        f'''<div class="car-card {selected}"><div class="car-preview" style="--car:{car["color"]};--accent:{car["accent"]}">
        <span>{car["emoji"]}</span><b>CRAZY</b></div><div class="car-name">{car["name"]}</div>
        <div class="car-stats"><span>Speed<br><b>{car["speed"]}</b></span><span>Control<br><b>{car["handling"]}</b></span></div></div>''',
        unsafe_allow_html=True,
    )
    if st.button(f"Select {car['name']}", key=f"car_{car_id}", use_container_width=True):
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
    st.markdown(f'<div class="hero"><div class="eyebrow">WELCOME BACK, {st.session_state.username.upper()}</div><h1><span style="color: white;">Own the<br><em>circuit</em></span></h1><p>Three legendary circuits. One clean run. Keep your tires on the tarmac.</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">01 / CHOOSE YOUR MACHINE</div>', unsafe_allow_html=True)
    cols = st.columns(3, gap="large")
    for col, (car_id, car) in zip(cols, CARS.items()):
        with col:
            car_card(car_id, car)
    st.markdown('<div class="section-label">02 / PICK YOUR SPONSOR</div>', unsafe_allow_html=True)
    sponsor_cols = st.columns(len(SPONSORS), gap="small")
    for col, sponsor in zip(sponsor_cols, SPONSORS):
        with col:
            if st.button(sponsor, key=f"sponsor_{sponsor}", use_container_width=True):
                st.session_state.sponsor = sponsor
                st.rerun()
    st.markdown(f'<div class="sponsor-chip">SPONSORED BY <strong>{st.session_state.sponsor}</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="launch-row">', unsafe_allow_html=True)
    if st.button("START CHAMPIONSHIP  →", type="primary", use_container_width=True):
        st.session_state.screen = "race"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.caption("Controls: ↑ accelerate · ↓ reverse · ← → steer · R restart · P pause")
    _, credits_col = st.columns([5, 1])
    with credits_col:
        if st.button("CREDITS", key="open_credits", use_container_width=True):
            credits_dialog()


def race():
    car = CARS[st.session_state.car_id]
    config = {"username": st.session_state.username, "sponsor": st.session_state.sponsor, "car": car, "timeLimits": TIME_LIMITS}
    config_json = json.dumps(config).replace("</", "<\\/")
    # Keep the race page within the viewport so the browser does not need scrolling.
    st.markdown('<style>section.main{overflow:hidden!important}.block-container{padding-bottom:8px!important}</style>', unsafe_allow_html=True)
    st.markdown('<div class="race-shell">', unsafe_allow_html=True)
    # Change Streamlit state directly; reloading the browser would reopen the race.
    header_logo, header_name, header_exit = st.columns([2, 3, 1])
    with header_logo:
        st.markdown(logo_html(), unsafe_allow_html=True)
    with header_name:
        st.markdown(f'<div class="race-player">{st.session_state.username}</div>', unsafe_allow_html=True)
    with header_exit:
        if st.button("EXIT TO LOBBY", key="exit_to_lobby", use_container_width=True):
            st.session_state.screen = "lobby"
            st.rerun()
    components.html(RACE_HTML.replace("__CONFIG__", config_json), height=650, scrolling=False)
    st.markdown('</div>', unsafe_allow_html=True)


load_css()
init_state()
if st.session_state.screen == "lobby":
    lobby()
else:
    race()