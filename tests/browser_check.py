"""Real Streamlit integration and browser behavior. Run with python tests/browser_check.py.
Requires Playwright and installed Chrome/Edge; no production JS test hooks are shipped.
"""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright

BASE='http://localhost:8501'
ARTIFACTS=Path('artifacts');ARTIFACTS.mkdir(exist_ok=True)


def race_frame(page):
    page.locator('iframe').wait_for()
    return page.locator('iframe').element_handle().content_frame()


def start(page, mobile=False):
    if mobile:
        page.get_by_text('MOBILE / JOYSTICK',exact=True).click()
    page.get_by_role('button',name='START CHAMPIONSHIP').click()
    frame=race_frame(page)
    frame.get_by_role('button',name='START RACE',exact=True).click()
    return frame


def run():
    with sync_playwright() as p:
        for channel in ([] if '--mobile-only' in sys.argv else ['chrome','msedge']):
            browser=p.chromium.launch(channel=channel,headless=True)
            page=browser.new_page(viewport={'width':1280,'height':900})
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(BASE)
            page.get_by_role('button',name='🔒 View BeastHunter').wait_for()
            preview=page.locator('.st-key-car_tile_beasthunter .car-preview')
            preview.scroll_into_view_if_needed()
            box=preview.bounding_box()
            page.mouse.click(box['x']+box['width']/2,box['y']+box['height']/2)
            page.get_by_text('Get to Level 12 to unlock BeastHunter.',exact=True).wait_for()
            page.get_by_role('button',name='GOT IT',exact=True).click()
            page.get_by_role('button',name='Select Phantom X').click()
            page.get_by_role('button',name='Apex Dynamics',exact=True).click()
            page.locator('.sponsor-chip strong').filter(has_text='Apex Dynamics').wait_for()
            frame=start(page)
            assert frame.evaluate('config.car.name')=='Phantom X'
            assert frame.evaluate('config.sponsor.name')=='Apex Dynamics'
            page.keyboard.press('ArrowUp',delay=250)
            assert frame.evaluate('player.s')>0
            page.keyboard.press('p')
            assert frame.evaluate('status')=='paused'
            snapshot=frame.evaluate('JSON.stringify([player,timeLeft,level])')
            page.wait_for_timeout(200)
            assert frame.evaluate('JSON.stringify([player,timeLeft,level])')==snapshot
            frame.get_by_role('button',name='RESUME',exact=True).click()
            assert frame.evaluate('status')=='racing'
            page.keyboard.press('r')
            assert frame.evaluate('player.s')==0
            page.keyboard.press('Space')
            assert frame.evaluate('status')=='racing'
            frame.evaluate("fail('OFF TRACK','Test collision retry')")
            page.keyboard.press('Space')
            assert frame.evaluate('status')=='racing'
            frame.evaluate('timeLeft=.001')
            frame.get_by_role('heading',name='TIME EXPIRED').wait_for()
            frame.get_by_role('button',name='TRY AGAIN',exact=True).click()
            # Ordered checkpoint completion exercises real collision/finish and bridge events.
            for index in range(23):
                assert frame.evaluate('level')==index
                frame.evaluate('''() => {player.s=0; for(let i=1;i<road.length;i++) {
                  player.x=road[i].x;player.y=road[i].y;updatePhysics(0);
                }}''')
                frame.get_by_role('heading',name='CHAMPIONSHIP COMPLETE' if index==22 else 'LEVEL COMPLETE',exact=True).wait_for()
                page.wait_for_timeout(100)
                assert frame.evaluate('level')==index, 'rerun reset browser state'
                unlocks={4:'Road Reaper',10:'BeastHunter',16:'Night Fang',21:'Apex Titan'}
                if index in unlocks:
                    frame.get_by_role('button',name='RETURN TO LOBBY',exact=True).click()
                    page.get_by_role('button',name=f'Select {unlocks[index]}',exact=True).wait_for()
                    frame=start(page)
                elif index<22:
                    frame.get_by_role('button',name='NEXT LEVEL',exact=True).click()
            frame.get_by_text('23 / 23 levels complete',exact=False).wait_for()
            frame.get_by_role('button',name='RETURN TO LOBBY',exact=True).click()
            page.get_by_role('button',name='Select BeastHunter',exact=True).wait_for()
            page.get_by_role('button',name='Select Apex Titan',exact=True).wait_for()
            assert page.get_by_text('LEVEL 23 / 23 UNLOCKED',exact=True).is_visible()
            assert not errors,errors
            print(channel, 'desktop, full championship events, locks and return: PASS',flush=True)
            page.screenshot(path=str(ARTIFACTS/f'{channel}-lobby.png'),full_page=True)
            browser.close()
        browser=p.chromium.launch(channel='chrome',headless=True)
        for width,height in [(390,844),(430,932),(844,390),(932,430),(768,1024),(1024,768)]:
            context=browser.new_context(viewport={'width':width,'height':height},screen={'width':width,'height':height},has_touch=True,is_mobile=True,device_scale_factor=2)
            page=context.new_page();page.goto(BASE);frame=start(page,True)
            assert frame.locator('#keyboardHint').is_hidden()
            assert frame.locator('#joystick').is_visible()
            assert frame.evaluate("getComputedStyle(document.getElementById('joystick')).touchAction")=='none'
            # Captured pointer drag, including diagonal and release.
            joystick=frame.locator('#joystick').bounding_box()
            x=joystick['x']+joystick['width']/2;y=joystick['y']+joystick['height']/2
            page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+20,y-30)
            analog=frame.evaluate('({...input})')
            assert analog['accelerate']>0 and analog['steer']>0,analog
            page.mouse.up()
            assert frame.evaluate('input.accelerate+input.brake+input.steer')==0
            page.mouse.move(x,y);page.mouse.down();page.mouse.move(x,y+30)
            assert frame.evaluate('input.brake')>0
            frame.evaluate("document.getElementById('joystick').dispatchEvent(new PointerEvent('pointercancel',{pointerId}))")
            assert frame.evaluate('input.brake')==0
            page.mouse.up()
            # Deliver real Chromium touch events as well as the mouse pointer path.
            touch=context.new_cdp_session(page)
            scroll=page.locator('[data-testid="stMain"]').evaluate('(el)=>el.scrollTop')
            touch.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':1}]})
            touch.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x+20,'y':y-30,'id':1}]})
            assert frame.evaluate('input.accelerate>0 && input.steer>0')
            touch.send('Input.dispatchTouchEvent',{'type':'touchCancel','touchPoints':[]})
            assert frame.evaluate('input.accelerate+input.brake+input.steer')==0
            assert page.locator('[data-testid="stMain"]').evaluate('(el)=>el.scrollTop')==scroll
            touch.detach()
            frame.get_by_role('button',name='Pause game').click()
            frame.get_by_role('button',name='RESTART',exact=True).click()
            assert frame.evaluate('status')=='racing'
            frame.evaluate("window.dispatchEvent(new Event('blur'))")
            assert frame.evaluate('status')=='paused'
            frame.get_by_role('button',name='RESUME',exact=True).click()
            assert frame.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
            assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
            frame.get_by_role('button',name='Pause game').click()
            state=frame.evaluate('JSON.stringify([player,timeLeft,level])')
            page.set_viewport_size({'width':height,'height':width})
            page.wait_for_timeout(150)
            assert frame.evaluate('JSON.stringify([player,timeLeft,level])')==state
            page.set_viewport_size({'width':width,'height':height})
            page.wait_for_timeout(150)
            frame.get_by_role('button',name='RESUME',exact=True).click()
            page.screenshot(path=str(ARTIFACTS/f'active-{width}x{height}.png'),full_page=True)
            frame.get_by_role('button',name='Pause game').click()
            page.screenshot(path=str(ARTIFACTS/f'mobile-{width}x{height}.png'),full_page=True)
            frame.get_by_role('button',name='RETURN TO LOBBY',exact=True).click()
            page.get_by_role('button',name='START CHAMPIONSHIP').wait_for()
            print(f'{width}x{height}: joystick, cancel, pause, restart, exit PASS',flush=True)
            context.close()
        browser.close()


if __name__=='__main__':run()

