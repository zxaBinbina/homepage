"""Animation and drag regression checks. Use the dev server for the terminal-state fixture."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:5173').rstrip('/')
out = Path('artifacts')
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1100}, reduced_motion='no-preference')
    context.set_default_timeout(10000)
    context.add_init_script('Math.random = () => 0')
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))

    def visit(game):
        page.goto(base + '/games/' + game, wait_until='networkidle')
        expect(page.locator('.game-surface')).to_be_visible()

    def card_idle():
        expect(page.locator('.solitaire-surface')).to_have_attribute('aria-busy', 'false')

    def mouse_drag(source, target, stack=1):
        source.scroll_into_view_if_needed()
        a, b = source.bounding_box(), target.bounding_box()
        page.mouse.move(a['x'] + a['width'] / 2, a['y'] + 14)
        page.mouse.down()
        page.mouse.move(b['x'] + b['width'] / 2, b['y'] + min(30, b['height'] / 2), steps=8)
        expect(page.locator('.solitaire-drag-stack > .playing-card')).to_have_count(stack)
        page.mouse.up()
        expect(page.locator('.solitaire-drag-layer')).to_have_count(0)
        card_idle()

    visit('2048')
    page.evaluate('''() => {
      const board = document.querySelector('.number-board');
      window.moveTimes = [];
      new MutationObserver(() => window.moveTimes.push({busy: board.getAttribute('aria-busy'), time: performance.now()})).observe(board, {attributes:true, attributeFilter:['aria-busy']});
    }''')
    page.locator('.number-board').focus()
    page.keyboard.press('ArrowLeft')
    expect(page.locator('.number-board')).to_have_attribute('aria-busy', 'true')
    expect(page.locator('.number-flight')).to_have_count(2)
    page.keyboard.press('ArrowRight')
    expect(page.locator('.number-board')).to_have_attribute('aria-busy', 'false')
    assert page.locator('.number-tile').all_text_contents()[:4] == ['4', '2', '', ''], 'Input during a move changed the next board'
    duration = page.evaluate('moveTimes.find(t => t.busy === "false").time - moveTimes.find(t => t.busy === "true").time')
    assert 180 <= duration <= 400, duration
    page.keyboard.press('ArrowDown')
    expect(page.locator('.number-board')).to_have_attribute('aria-busy', 'true')
    page.get_by_role('button', name='重新开始', exact=True).click()
    page.wait_for_timeout(450)
    assert page.locator('.number-tile').all_text_contents()[:2] == ['2', '2']
    expect(page.locator('.number-flight')).to_have_count(0)
    page.locator('.number-board').focus()
    page.keyboard.press('ArrowLeft')
    page.emulate_media(reduced_motion='reduce')
    expect(page.locator('.number-board')).to_have_attribute('aria-busy', 'false')
    expect(page.locator('.number-flight')).to_have_count(0)
    expect(page.locator('.number-tile').first).to_have_text('4')
    page.emulate_media(reduced_motion='no-preference')
    page.get_by_role('checkbox', name='无动画', exact=True).check()
    page.get_by_role('button', name='重新开始', exact=True).click()
    page.locator('.number-board').focus()
    page.keyboard.press('ArrowLeft')
    expect(page.locator('.number-tile').first).to_have_text('4')
    assert page.locator('.number-board').evaluate('(el) => el.getAnimations({subtree:true}).length') == 0
    expect(page.get_by_role('checkbox', name='无动画', exact=True)).to_be_checked()
    page.get_by_role('checkbox', name='无动画', exact=True).uncheck()
    page.locator('.number-board').focus()
    page.keyboard.press('ArrowDown')
    page.get_by_role('link', name='全部游戏', exact=True).click()
    expect(page.locator('.games-grid')).to_be_visible()
    print(f'2048: movement/merge/spawn settled in {duration:.0f}ms; lock, restart, route cleanup and live reduced motion passed.', flush=True)

    visit('minesweeper')
    page.locator('.mine-cell').nth(80).click(button='right')
    page.locator('.mine-cell').nth(40).click()
    assert page.locator('.mine-board').evaluate('(el) => el.getAnimations({subtree:true}).length') > 1
    page.screenshot(path=str(out / 'game-motion-mine-reveal.png'), full_page=True)
    page.wait_for_timeout(400)
    page.locator('.mine-cell').nth(80).click(button='right')
    page.locator('.mine-cell').nth(80).click()
    page.wait_for_function('document.querySelector(".mine-scanner")?.getAnimations().length > 0')
    expect(page.locator('.game-status')).to_contain_text('恭喜过关')
    page.screenshot(path=str(out / 'game-motion-mine-scan.png'), full_page=True)
    expect(page.locator('.mine-scanner')).to_have_count(0, timeout=2500)
    assert page.locator('.mine-symbol').evaluate_all('els => els.every(el => getComputedStyle(el).opacity === "1")')
    expect(page.locator('.mine-cell.is-found')).to_have_count(10)
    page.get_by_role('button', name='重新开始', exact=True).click()
    page.locator('.mine-cell').nth(80).click(button='right')
    page.locator('.mine-cell').nth(40).click()
    page.locator('.mine-cell').nth(1).click()
    expect(page.locator('.mine-burst')).to_have_count(1)
    assert page.locator('.mine-shockwave').evaluate('(el) => el.getAnimations().length') == 1
    page.screenshot(path=str(out / 'game-motion-mine-explosion.png'), full_page=True)
    page.get_by_role('button', name='重新开始', exact=True).click()
    page.wait_for_timeout(600)
    expect(page.locator('.mine-burst, .mine-scanner')).to_have_count(0)
    expect(page.locator('.mine-cell.is-open')).to_have_count(0)
    print('Mines: staggered flips, explosion, victory scanner and restart cleanup passed.', flush=True)

    visit('solitaire')
    page.locator('.stock-card').click()
    expect(page.locator('.solitaire-surface')).to_have_attribute('aria-busy', 'true')
    page.wait_for_function('Array.from(document.querySelectorAll(".is-card-moving")).some(el => el.getAnimations().some(a => a.effect.getKeyframes().some(f => f.transform?.includes("rotateY(180deg)"))))')
    page.locator('.is-card-moving').evaluate_all('els => els.forEach(el => el.getAnimations().forEach(a => {a.pause(); a.currentTime=120}))')
    page.screenshot(path=str(out / 'game-motion-solitaire-flip.png'), full_page=True)
    page.locator('.is-card-moving').evaluate_all('els => els.forEach(el => el.getAnimations().forEach(a => a.finish()))')
    card_idle()
    page.get_by_role('button', name='重新开始', exact=True).click()
    mouse_drag(page.locator('.tableau-card[data-card-id="0-1"]'), page.locator('.foundation-card').first)
    expect(page.locator('.game-stats strong').first).to_have_text('1 / 52')
    # A queen cannot enter an empty column; it returns without consuming a move.
    mouse_drag(page.locator('.tableau-card[data-card-id="3-12"]'), page.locator('.empty-column'))
    expect(page.locator('.game-stats strong').nth(1)).to_have_text('1')
    expect(page.locator('.game-status')).to_contain_text('回到原处')
    mouse_drag(page.locator('.tableau-card[data-card-id="3-12"]'), page.locator('.pile-target').nth(4))
    expect(page.locator('.tableau-card.card-back')).to_have_count(20)
    mouse_drag(page.locator('.tableau-card[data-card-id="2-13"]'), page.locator('.empty-column'), stack=2)
    expect(page.locator('.solitaire-column').first.locator('.tableau-card')).to_have_count(2)
    page.get_by_role('button', name='撤销', exact=True).click()
    card_idle()
    expect(page.locator('.solitaire-column').first.locator('.tableau-card')).to_have_count(0)
    source = page.locator('.tableau-card[data-card-id="3-13"]')
    box = source.bounding_box()
    page.mouse.move(box['x']+20, box['y']+15)
    page.mouse.down()
    page.mouse.move(box['x']+90, box['y']+35, steps=4)
    expect(page.locator('.solitaire-drag-layer')).to_have_count(1)
    page.keyboard.press('Escape')
    page.mouse.up()
    expect(page.locator('.solitaire-drag-layer')).to_have_count(0)
    print('Solitaire: stock flip, mouse drag, invalid return, stack drag, undo and Escape passed.', flush=True)

    # Only the dev build exposes Vue component state; no fixture hooks ship to visitors.
    # Start one move from completion so the real commit path triggers the celebration.
    def endgame():
        page.evaluate('''() => {
            const state = document.querySelector('.solitaire-surface').__vueParentComponent.setupState;
            const card = (suit, rank) => ({suit,rank,faceUp:true});
            state.game = {stock:[], waste:[card(3,13)], moves:0,
                foundations: Array.from({length:4},(_,suit) => Array.from({length:suit===3?12:13},(_,i)=>card(suit,i+1))),
                tableau:[[],[],[],[],[],[],[]]};
        }''')
        page.get_by_role('button', name='选择翻牌 方块 K', exact=True).click()
        page.get_by_role('button', name='方块收牌区，方块 Q', exact=True).click()
        card_idle()
    endgame()
    expect(page.locator('.solitaire-celebration')).to_have_count(1)
    page.wait_for_timeout(600)
    first = page.locator('.solitaire-celebration').evaluate('(el) => el.toDataURL()')
    page.wait_for_timeout(200)
    assert first != page.locator('.solitaire-celebration').evaluate('(el) => el.toDataURL()'), 'Celebration is static'
    page.screenshot(path=str(out / 'game-motion-solitaire-win.png'), full_page=True)
    expect(page.locator('.solitaire-celebration')).to_have_count(0, timeout=6500)
    page.get_by_role('button', name='重播庆祝', exact=True).click()
    expect(page.locator('.solitaire-celebration')).to_have_count(1)
    page.get_by_role('button', name='跳过庆祝', exact=True).click()
    expect(page.locator('.solitaire-celebration')).to_have_count(0)
    page.emulate_media(reduced_motion='reduce')
    page.get_by_role('button', name='重新开始', exact=True).click()
    endgame()
    expect(page.locator('.game-status')).to_contain_text('接龙成功')
    expect(page.locator('.solitaire-celebration')).to_have_count(0)
    print('Solitaire victory: moving flip/bounce trails, finite completion, replay, skip and reduced motion passed.', flush=True)

    touch = browser.new_context(viewport={'width':390,'height':900}, has_touch=True, is_mobile=True, reduced_motion='no-preference')
    touch.add_init_script('Math.random = () => 0')
    phone = touch.new_page()
    phone.on('pageerror', lambda error: errors.append(str(error)))
    phone.goto(base + '/games/solitaire', wait_until='networkidle')
    expect(phone.locator('.solitaire-orientation-hint')).to_be_visible()
    phone.get_by_role('button', name='关闭横屏提示').tap()
    expect(phone.locator('.solitaire-orientation-hint')).to_have_count(0)
    source = phone.locator('.tableau-card[data-card-id="0-1"]')
    source.scroll_into_view_if_needed()
    a, b = source.bounding_box(), phone.locator('.foundation-card').first.bounding_box()
    start = {'x':a['x']+25,'y':a['y']+18}
    end = {'x':b['x']+b['width']/2,'y':b['y']+30}
    cdp = touch.new_cdp_session(phone)
    cdp.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[start]})
    phone.wait_for_timeout(350)
    expect(phone.locator('.solitaire-drag-layer')).to_have_count(1)
    cdp.send('Input.dispatchTouchEvent', {'type':'touchMove','touchPoints':[end]})
    expect(phone.locator('.foundation-card.is-drop-target')).to_have_count(1)
    cdp.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]})
    expect(phone.locator('.solitaire-drag-layer')).to_have_count(0)
    expect(phone.locator('.game-stats strong').first).to_have_text('1 / 52')
    expect(phone.locator('.solitaire-surface')).to_have_attribute('aria-busy','false')
    # A normal swipe pans the table instead of lifting cards.
    source = phone.locator('.tableau-card[data-card-id="3-12"]')
    source.scroll_into_view_if_needed()
    a = source.bounding_box()
    start = {'x':a['x']+35,'y':a['y']+20}
    cdp.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[start]})
    for shift in [15,35,55,80]:
        cdp.send('Input.dispatchTouchEvent', {'type':'touchMove','touchPoints':[{'x':start['x']-shift,'y':start['y']}]})
        phone.wait_for_timeout(20)
    cdp.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]})
    phone.wait_for_timeout(200)
    expect(phone.locator('.solitaire-drag-layer')).to_have_count(0)
    assert phone.locator('.solitaire-scroll').evaluate('(el) => el.scrollLeft') > 10
    assert phone.locator('.game-stats strong').nth(1).inner_text() == '1'
    # Long press at the edge supports scrolling to offscreen columns and cancellation.
    phone.locator('.solitaire-scroll').evaluate('(el) => el.scrollLeft = 0')
    a = source.bounding_box()
    start = {'x':a['x']+20,'y':a['y']+18}
    cdp.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[start]})
    phone.wait_for_timeout(350)
    cdp.send('Input.dispatchTouchEvent', {'type':'touchMove','touchPoints':[{'x':365,'y':start['y']}]})
    phone.wait_for_timeout(450)
    assert phone.locator('.solitaire-scroll').evaluate('(el) => el.scrollLeft') > 40
    cdp.send('Input.dispatchTouchEvent', {'type':'touchCancel','touchPoints':[]})
    expect(phone.locator('.solitaire-drag-layer')).to_have_count(0)
    phone.set_viewport_size({'width':844,'height':390})
    phone.reload(wait_until='networkidle')
    expect(phone.locator('.solitaire-orientation-hint')).not_to_be_visible()
    colors = []
    for theme in ['dark','light']:
        phone.evaluate('(theme) => document.documentElement.dataset.theme=theme',theme)
        colors.append(phone.locator('.tableau-card:not(.card-back)').first.evaluate('(el) => getComputedStyle(el).backgroundColor'))
        phone.screenshot(path=str(out / f'game-motion-cards-{theme}-landscape.png'), full_page=True)
    assert colors[0] != colors[1]
    assert phone.evaluate('document.documentElement.scrollWidth <= innerWidth')
    print('Touch: hold-to-drag, ordinary scrolling, edge scrolling, cancellation, landscape hint and card themes passed.', flush=True)
    assert not errors, errors
    touch.close()
    browser.close()
print('Game motion and drag checks passed. Screenshots: artifacts/game-motion-*.png')
