/* Streamlit v1 message bridge. Only completion and exit emit values, never frames.
   The keyed iframe survives Python reruns; repeated render messages must not reset it. */
'use strict';
const $ = id => document.getElementById(id);
let config, tracks, initialized = false, parentOrigin = '*', eventSequence = 0;
function send(type, data = {}) {
  window.parent.postMessage({isStreamlitMessage: true, type, ...data}, parentOrigin);
}
window.addEventListener('message', event => {
  if (event.source !== window.parent || event.data?.type !== 'streamlit:render') return;
  parentOrigin = event.origin;
  if (!initialized) {
    config = event.data.args.config;
    tracks = config.tracks;
    initialized = true;
    startup();
  }
});
send('streamlit:componentReady', {apiVersion: 1});

// World geometry is invariant under resize, orientation changes and pixel density.
let WORLD_WIDTH = 1000, WORLD_HEIGHT = 650;
const canvas = $('game'), ctx = canvas.getContext('2d');
let level = 0, road = [], player = {x:0,y:0,a:0,s:0};
let status = 'ready', last = 0, timeLeft = 0, checkpoint = 1, completed = 0;
let view = {width:1000,height:650,scale:1,x:0,y:0};
const input = {accelerate:0, brake:0, steer:0}, keys = {};
let pointerId = null;

function emitEvent(action) {
  send('streamlit:setComponentValue', {dataType:'json', value:{
    raceId:config.raceId, eventId:`${config.raceId}:${++eventSequence}`,
    completed, action
  }});
}
function resize() {
  // The race page sizes this iframe with CSS dynamic viewport units. Reading our
  // own viewport needs no access to the parent DOM and follows mobile browser chrome.
  const height = window.innerHeight;
  $('wrap').style.height = `${height}px`;
  send('streamlit:setFrameHeight', {height});
  const rect = canvas.getBoundingClientRect(), dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(rect.width*dpr); canvas.height = Math.round(rect.height*dpr);
  view.width = rect.width; view.height = rect.height;
  // Portrait uses a following camera instead of shrinking the car to an unreadable speck.
  view.scale = Math.min(1, Math.max(rect.width/WORLD_WIDTH, rect.height/WORLD_HEIGHT));
  view.scale = Math.max(.65, view.scale);
  ctx.setTransform(dpr,0,0,dpr,0,0);
}
function buildRoad() {
  WORLD_WIDTH = tracks[level].world_width; WORLD_HEIGHT = tracks[level].world_height;
  road = tracks[level].points.map(p => ({x:p[0]*WORLD_WIDTH,y:p[1]*WORLD_HEIGHT}));
}
function loadLevel(index) {
  level = index; buildRoad(); resize(); resetCurrentLevel();
  $('level').textContent = `LEVEL ${String(level+1).padStart(2,'0')} / ${tracks.length} · ${tracks[level].difficulty.toUpperCase()}`;
  $('track').textContent = tracks[level].name.toUpperCase();
}
function resetCurrentLevel() {
  resetInput();
  Object.assign(player, {x:road[0].x,y:road[0].y,s:0,a:Math.atan2(road[1].y-road[0].y,road[1].x-road[0].x)});
  timeLeft = tracks[level].time_limit; checkpoint = 1; status = 'racing';
  closeModal(); updateTimer(); last = performance.now();
}
function advanceToNextLevel() { loadLevel(level < tracks.length-1 ? level+1 : 0); }
function returnToLobby() { status = 'exiting'; resetInput(); stopAudio(); emitEvent('lobby'); }

// Both devices feed the same analog controls. Physics never reads keys or pointers.
function setKeyboardInput() {
  input.accelerate = keys.ArrowUp ? 1 : 0;
  input.brake = keys.ArrowDown ? 1 : 0;
  input.steer = (keys.ArrowRight ? 1 : 0) - (keys.ArrowLeft ? 1 : 0);
}
function resetInput() {
  for (const key of Object.keys(keys)) delete keys[key];
  input.accelerate = input.brake = input.steer = 0;
  const captured = pointerId; pointerId = null;
  if (captured !== null && $('joystick').hasPointerCapture(captured)) $('joystick').releasePointerCapture(captured);
  $('stick').style.transform = 'translate(0px,0px)';
}
function updateJoystickInput(event) {
  const rect = $('joystick').getBoundingClientRect(), radius = rect.width/2-22;
  let x = (event.clientX-rect.left-rect.width/2)/radius;
  let y = (event.clientY-rect.top-rect.height/2)/radius;
  const magnitude = Math.hypot(x,y);
  if (magnitude > 1) { x /= magnitude; y /= magnitude; }
  // Rescale each axis past the dead zone while retaining diagonal control.
  const deadZone = value => Math.abs(value)<.12 ? 0 : Math.sign(value)*(Math.abs(value)-.12)/.88;
  input.steer = deadZone(x); input.accelerate = Math.max(0,-deadZone(y)); input.brake = Math.max(0,deadZone(y));
  $('stick').style.transform = `translate(${x*radius}px,${y*radius}px)`;
}
$('joystick').addEventListener('pointerdown', event => {
  if (status !== 'racing' || pointerId !== null) return;
  event.preventDefault(); pointerId = event.pointerId;
  $('joystick').setPointerCapture(pointerId); unlockAudio(); updateJoystickInput(event);
});
$('joystick').addEventListener('pointermove', event => {
  if (event.pointerId !== pointerId) return;
  event.preventDefault(); updateJoystickInput(event);
});
for (const name of ['pointerup','pointercancel','lostpointercapture']) {
  $('joystick').addEventListener(name, event => { if (event.pointerId === pointerId) resetInput(); });
}
window.addEventListener('keydown', event => {
  if (!initialized) return;
  const key = event.key.toLowerCase();
  if (['ArrowUp','ArrowDown','ArrowLeft','ArrowRight',' '].includes(event.key)) event.preventDefault();
  // Keep focus inside custom dialogs; prevent held Space from firing a new button.
  if (event.key === 'Tab' && !$('modal').hidden) {
    const buttons = [...$('modalActions').querySelectorAll('button')];
    const first = buttons[0], end = buttons[buttons.length-1];
    if (event.shiftKey && document.activeElement === first) {event.preventDefault();end.focus();}
    else if (!event.shiftKey && document.activeElement === end) {event.preventDefault();first.focus();}
  }
  if (event.repeat) return;
  unlockAudio();
  if (config.controlMode !== 'keyboard') return;
  if (event.code === 'Space' && status === 'failed') { resetCurrentLevel(); return; }
  if (key === 'p') { if (status === 'paused') resumeGame(); else openPauseMenu(); return; }
  if (key === 'r' && ['racing','paused'].includes(status)) {resetCurrentLevel();return;}
  if (status === 'racing') { keys[event.key] = true; setKeyboardInput(); }
});
window.addEventListener('keyup', event => {delete keys[event.key]; if (config?.controlMode === 'keyboard') setKeyboardInput();});
function loseFocus() { resetInput(); if (status === 'racing') openPauseMenu(); }
window.addEventListener('blur', loseFocus);
document.addEventListener('visibilitychange', () => {if (document.hidden) loseFocus();});

// Preserve the original acceleration, reverse, angular steering and center-line test.
function pointDistance(x,y) {
  let best = Infinity;
  for (let i=0;i<road.length-1;i++) {
    const a=road[i],b=road[i+1],dx=b.x-a.x,dy=b.y-a.y;
    const t=Math.max(0,Math.min(1,((x-a.x)*dx+(y-a.y)*dy)/(dx*dx+dy*dy)));
    best=Math.min(best,Math.hypot(x-a.x-t*dx,y-a.y-t*dy));
  }
  return best;
}
function updatePhysics(dt) {
  const track=tracks[level];
  timeLeft=Math.max(0,timeLeft-dt);updateTimer();
  if (timeLeft === 0) {fail('TIME EXPIRED','The countdown reached zero before the finish.');return;}
  player.a += input.steer*2.5*track.steering_modifier*dt*(Math.abs(player.s)/80+.35);
  if (input.accelerate>0) player.s=Math.min(player.s+170*track.acceleration_modifier*input.accelerate*dt,210*track.max_speed_modifier);
  else if (input.brake>0) player.s=Math.max(player.s-150*input.brake*dt,-75);
  else player.s*=Math.pow(.985,dt*60);
  player.x+=Math.cos(player.a)*player.s*dt;player.y+=Math.sin(player.a)*player.s*dt;
  if (pointDistance(player.x,player.y)>track.road_width/2-track.off_road_tolerance) {
    fail('OFF TRACK','The tires left the tarmac. Reset and find a cleaner line.');return;
  }
  // Ordered route checkpoints prevent shortcuts across adjacent stretches and
  // ensure neither a collision nor spawn proximity can award a completion.
  if (checkpoint<road.length && Math.hypot(player.x-road[checkpoint].x,player.y-road[checkpoint].y)<track.road_width/2) checkpoint++;
  if (checkpoint === road.length) completeLevel();
}
function loop(now) {
  const dt=Math.min(Math.max(0,(now-last)/1000),.04);last=now;
  if (status==='racing') updatePhysics(dt);
  draw();requestAnimationFrame(loop);
}

// Rendering retains the original grass grid, asphalt, dashed center and car silhouette.
let sponsorPath;
function draw() {
  const w=view.width,h=view.height,t=tracks[level],scale=view.scale;
  ctx.clearRect(0,0,w,h);ctx.fillStyle='#17231a';ctx.fillRect(0,0,w,h);
  view.x = w >= WORLD_WIDTH*scale ? (w-WORLD_WIDTH*scale)/2 : Math.min(0,Math.max(w-WORLD_WIDTH*scale,w/2-player.x*scale));
  view.y = h >= WORLD_HEIGHT*scale ? (h-WORLD_HEIGHT*scale)/2 : Math.min(0,Math.max(h-WORLD_HEIGHT*scale,h/2-player.y*scale));
  ctx.save();ctx.translate(view.x,view.y);ctx.scale(scale,scale);
  ctx.strokeStyle='#223227';ctx.lineWidth=2;
  ctx.beginPath();
  for(let x=0;x<WORLD_WIDTH;x+=42){ctx.moveTo(x,0);ctx.lineTo(x,WORLD_HEIGHT);}
  for(let y=0;y<WORLD_HEIGHT;y+=42){ctx.moveTo(0,y);ctx.lineTo(WORLD_WIDTH,y);}
  ctx.stroke();ctx.lineCap='round';ctx.lineJoin='round';ctx.beginPath();
  road.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));
  ctx.strokeStyle='#0b0d0c';ctx.lineWidth=t.road_width+14;ctx.stroke();
  ctx.strokeStyle='#66706a';ctx.lineWidth=t.road_width;ctx.stroke();
  ctx.setLineDash([18,18]);ctx.strokeStyle='#a8b0a6';ctx.lineWidth=2;ctx.stroke();ctx.setLineDash([]);
  ctx.fillStyle='#d9f047';ctx.font='bold 12px monospace';ctx.fillText('START',road[0].x-20,road[0].y-30);
  const end=road[road.length-1],prev=road[road.length-2];
  ctx.save();ctx.translate(end.x,end.y);ctx.rotate(Math.atan2(end.y-prev.y,end.x-prev.x));
  for(let i=0;i<8;i++)for(let j=0;j<2;j++){ctx.fillStyle=(i+j)%2?'#111':'#fff';ctx.fillRect(j*7-7,(i-4)*t.road_width/8,7,t.road_width/8);}
  ctx.restore();
  if(checkpoint<road.length){ctx.beginPath();ctx.arc(road[checkpoint].x,road[checkpoint].y,5,0,Math.PI*2);ctx.fillStyle='#d9f047';ctx.fill();}
  drawCar();ctx.restore();
}
function drawCar() {
  ctx.save();ctx.translate(player.x,player.y);ctx.rotate(player.a+Math.PI/2);
  const c=config.car;ctx.fillStyle=c.color;ctx.beginPath();
  if(ctx.roundRect)ctx.roundRect(-13,-23,26,46,7);else ctx.rect(-13,-23,26,46);
  ctx.fill();ctx.fillStyle=c.accent;ctx.fillRect(-9,-7,18,9);
  ctx.fillStyle='#111';ctx.fillRect(-10,-17,20,7);ctx.fillRect(-10,11,20,7);
  ctx.fillRect(-11,-10,22,21);ctx.save();ctx.translate(-9,-9);ctx.scale(18/32,18/32);
  ctx.fillStyle=config.sponsor.color;ctx.fill(sponsorPath,'evenodd');ctx.restore();ctx.restore();
}
function updateTimer() {
  const seconds=Math.ceil(timeLeft);
  $('timeValue').textContent=`${String(Math.floor(seconds/60)).padStart(2,'0')}:${String(seconds%60).padStart(2,'0')}`;
  document.querySelector('.timer').classList.toggle('warning',seconds<=10);
}

// Explicit states prevent retries, pause actions and finish events from overlapping.
function modal(title,text,label,actions) {
  resetInput();$('modalTitle').textContent=title;$('modalText').textContent=text;$('modalLabel').textContent=label;
  $('modalActions').replaceChildren();
  for (const [name,action] of actions) {
    const button=document.createElement('button');button.textContent=name;
    button.onclick=()=>{unlockAudio();action();};$('modalActions').appendChild(button);
  }
  $('modal').hidden=false;$('modalActions').firstElementChild.focus({preventScroll:true});
}
function closeModal() {$('modal').hidden=true;canvas.focus({preventScroll:true});}
function openPauseMenu() {
  if(status!=='racing')return;
  status='paused';modal('GAME PAUSED','Your car and countdown are paused.','TAKE A BREATHER',[
    ['RESUME',resumeGame],['RESTART',resetCurrentLevel],['RETURN TO LOBBY',returnToLobby]]);
}
function resumeGame() {resetInput();status='racing';last=performance.now();closeModal();}
function fail(title,text) {
  status='failed';modal(title,text+(config.controlMode==='keyboard'?'\nPress SPACE or select TRY AGAIN':''),'RUN OVER',[
    ['TRY AGAIN',resetCurrentLevel],['RETURN TO LOBBY',returnToLobby]]);
}
function completeLevel() {
  status='complete';completed=level+1;emitEvent('progress');
  const final=level===tracks.length-1;
  const text=final ? `${config.username} · ${config.car.name}\n${config.sponsor.name}\n${tracks.length} / ${tracks.length} levels complete` : `Level ${level+1} of ${tracks.length} complete\nNext: ${tracks[level+1].name}`;
  modal(final?'CHAMPIONSHIP COMPLETE':'LEVEL COMPLETE',text,'CHECKERED FLAG',[
    [final?'RACE AGAIN':'NEXT LEVEL',advanceToNextLevel],['RETURN TO LOBBY',returnToLobby]]);
}
$('pause').onclick=openPauseMenu;

// One optional audio context and interval. Creation/resume only follows a gesture.
let audio=null,audioInterval=null,soundEnabled=false;
function unlockAudio() {
  if(!soundEnabled)return;
  try {
    if(!audio){
      audio=new (window.AudioContext||window.webkitAudioContext)();let note=0;
      audioInterval=setInterval(()=>{
        if(audio.state!=='running'||status!=='racing')return;
        try{const o=audio.createOscillator(),g=audio.createGain();o.frequency.value=[440,494,523,587][note++%4];o.type='square';g.gain.setValueAtTime(.0001,audio.currentTime);g.gain.exponentialRampToValueAtTime(.025,audio.currentTime+.03);g.gain.exponentialRampToValueAtTime(.0001,audio.currentTime+.28);o.connect(g).connect(audio.destination);o.start();o.stop(audio.currentTime+.3);}catch(_error){}
      },260);
    }
    audio.resume().catch(()=>{});
  }catch(_error){soundEnabled=false;$('sound').textContent='♪ OFF';}
}
function stopAudio(){clearInterval(audioInterval);audioInterval=null;if(audio){audio.close().catch(()=>{});audio=null;}}
$('sound').onclick=()=>{soundEnabled=!soundEnabled;$('sound').textContent=soundEnabled?'♪ ON':'♪ OFF';$('sound').setAttribute('aria-label',soundEnabled?'Mute sound':'Enable sound');$('sound').setAttribute('aria-pressed',String(soundEnabled));if(soundEnabled)unlockAudio();else stopAudio();};
window.addEventListener('pagehide',stopAudio);
function startup() {
  const mobile=config.controlMode==='joystick';document.body.classList.toggle('mobile',mobile);
  $('mobileControls').hidden=!mobile;$('keyboardHint').hidden=mobile;
  canvas.setAttribute('aria-label',mobile?'Race track. Use the joystick below to drive.':'Race track. Arrow keys drive, P pauses, R restarts.');
  $('driver').textContent=config.username;$('sponsor').textContent=config.sponsor.name;
  sponsorPath=new Path2D(config.sponsor.logo_path);
  level=config.startLevel-1;buildRoad();resize();loadLevel(level);
  // A ready screen supplies iframe focus and a genuine mobile audio gesture.
  status='ready';modal('READY TO RACE',mobile?'Drag up to accelerate, left/right to steer, down to reverse.':'Arrow keys drive. P pauses. R restarts.','CHOOSE YOUR LINE', [['START RACE',resetCurrentLevel],['RETURN TO LOBBY',returnToLobby]]);
  window.addEventListener('resize',()=>{if(status==='racing')openPauseMenu();resize();});
  requestAnimationFrame(loop);
}
