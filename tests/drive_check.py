"""Deterministic centerline driver through the actual JS physics (no teleporting).
This tests feasibility, not human difficulty or mobile device performance.
"""
from playwright.sync_api import sync_playwright
import json
from pathlib import Path

with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1280,'height':900})
    page.goto('http://localhost:8501')
    page.get_by_role('button',name='START CHAMPIONSHIP').click()
    page.locator('iframe').wait_for()
    frame=page.locator('iframe').element_handle().content_frame()
    frame.get_by_role('button',name='START RACE',exact=True).click()
    result=frame.evaluate('''() => {
      const results=[];
      // Suppress network events in this test only, while preserving completion logic.
      emitEvent=()=>{};
      for(let index=0;index<tracks.length;index++) {
        loadLevel(index);
        let segment=0;
        for(let tick=0;tick<20000 && status==='racing';tick++) {
          const a=road[segment],b=road[segment+1];
          const dx=b.x-a.x,dy=b.y-a.y,length=Math.hypot(dx,dy);
          let projection=((player.x-a.x)*dx+(player.y-a.y)*dy)/length;
          const lookahead=index>=19?24:16;
          let distance=Math.max(0,projection)+lookahead, targetSegment=segment;
          let from=a,to=b,remainingLength=length;
          while(distance>remainingLength && targetSegment<road.length-2) {
            distance-=remainingLength;targetSegment++;from=road[targetSegment];to=road[targetSegment+1];remainingLength=Math.hypot(to.x-from.x,to.y-from.y);
          }
          const t=Math.min(1,distance/remainingLength);
          const targetX=from.x+(to.x-from.x)*t,targetY=from.y+(to.y-from.y)*t;
          const desired=Math.atan2(targetY-player.y,targetX-player.x);
          const error=Math.atan2(Math.sin(desired-player.a),Math.cos(desired-player.a));
          input.steer=Math.max(-1,Math.min(1,error*7/(2.5*(Math.abs(player.s)/80+.35))));
          const targetSpeed=Math.abs(error)>.3?38:(index>=19?62:85);
          input.accelerate=player.s<targetSpeed?1:0;
          input.brake=player.s>targetSpeed+3?1:0;
          updatePhysics(1/120);
          if(projection>length-4 && segment<road.length-2)segment++;
        }
        results.push({level:index+1,name:tracks[index].name,status,seconds:Math.round((tracks[index].time_limit-timeLeft)*10)/10,remaining:Math.round(timeLeft*10)/10,checkpoint,reason:document.getElementById('modalTitle').textContent});
      }
      return results;
    }''')
    Path('artifacts/feasibility.json').write_text(json.dumps(result,indent=2))
    for row in result:print(row)
    browser.close()
    assert all(row['status']=='complete' for row in result)


