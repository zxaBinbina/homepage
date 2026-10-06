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
        assert page.locator('.solitaire-drag-stack > .playing-card').evaluate_all('els => els.every(el => {const r=el.getBoundingClientRect(); return Math.abs(r.height-r.width*1.4)<0.1})'), 'Dragged cards must retain their proportions'
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

    visit('2048')
    page.evaluate('''() => {
      const s = document.querySelector('.number-surface').__vueParentComponent.setupState;
      s.game = {board:[1024,1024,...Array(14).fill(0)],score:0};
    }''')
    page.get_by_role('button', name='向左移动').click()
    expect(page.locator('.number-board')).to_have_attribute('aria-busy', 'true')
    expect(page.locator('.game-result')).to_have_count(0)
    expect(page.locator('.number-board')).to_have_attribute('aria-busy', 'false')
    expect(page.locator('.game-result')).to_contain_text('合成 2048')
    expect(page.get_by_role('button', name='向右移动')).to_be_disabled()
    page.get_by_role('button', name='继续挑战').click()
    expect(page.locator('.game-result')).to_have_count(0)
    expect(page.locator('.number-board')).to_be_focused()
    page.keyboard.press('ArrowRight')
    expect(page.locator('.number-board')).to_have_attribute('aria-busy', 'false')
    assert page.locator('.number-tile').nth(2).inner_text() == '2048'
    expect(page.locator('.game-result')).to_have_count(0)
    page.get_by_role('button', name='撤销', exact=True).click()
    expect(page.locator('.game-result')).to_have_count(0)
    page.get_by_role('button', name='撤销', exact=True).click()
    page.get_by_role('button', name='向左移动').click()
    expect(page.locator('.game-result')).to_contain_text('合成 2048')
    page.get_by_role('button', name='重新开始', exact=True).click()
    expect(page.locator('.game-result')).to_have_count(0)
    page.evaluate('''() => {
      const s = document.querySelector('.number-surface').__vueParentComponent.setupState;
      s.history = [s.game];
      s.game = {board:[2,4,8,16,4,8,16,32,8,16,32,64,16,32,64,128],score:100};
    }''')
    expect(page.locator('.game-result')).to_contain_text('没有可移动')
    expect(page.get_by_role('button', name='继续挑战')).to_have_count(0)
    page.get_by_role('button', name='撤销', exact=True).click()
    expect(page.locator('.game-result')).to_have_count(0)
    expect(page.get_by_role('button', name='向左移动')).to_be_enabled()
    print('2048 result: waits for merge, continue restores keyboard play, undo and restart clear milestone/terminal results.', flush=True)

    visit('minesweeper')
    page.locator('.mine-cell').nth(80).click(button='right')
    page.locator('.mine-cell').nth(40).click()
    assert page.locator('.mine-board').evaluate('(el) => el.getAnimations({subtree:true}).length') > 1
    page.screenshot(path=str(out / 'game-motion-mine-reveal.png'), full_page=True)
    page.wait_for_timeout(400)
    page.locator('.mine-cell').nth(80).click(button='right')
    page.locator('.mine-cell').nth(80).click()
    page.wait_for_function('document.querySelector(".mine-scanner")?.getAnimations().length > 0')
    expect(page.locator('.game-result')).to_have_count(0)
    page.screenshot(path=str(out / 'game-motion-mine-scan.png'), full_page=True)
    expect(page.locator('.mine-scanner')).to_have_count(0, timeout=2500)
    expect(page.locator('.game-result')).to_contain_text('恭喜过关')
    assert page.locator('.mine-symbol').evaluate_all('els => els.every(el => getComputedStyle(el).opacity === "1")')
    expect(page.locator('.mine-cell.is-found')).to_have_count(10)
    page.get_by_role('button', name='重新开始', exact=True).click()
    page.locator('.mine-cell').nth(80).click(button='right')
    page.locator('.mine-cell').nth(40).click()
    page.locator('.mine-cell').nth(1).click()
    expect(page.locator('.mine-burst')).to_have_count(1)
    expect(page.locator('.game-result')).to_have_count(0)
    assert page.locator('.mine-shockwave').evaluate('(el) => el.getAnimations().length') == 1
    page.screenshot(path=str(out / 'game-motion-mine-explosion.png'), full_page=True)
    page.get_by_role('button', name='重新开始', exact=True).click()
    page.wait_for_timeout(600)
    expect(page.locator('.mine-burst, .mine-scanner')).to_have_count(0)
    expect(page.locator('.mine-cell.is-open')).to_have_count(0)
    expect(page.locator('.game-result')).to_have_count(0)
    page.locator('.mine-cell').nth(80).click(button='right')
    page.locator('.mine-cell').nth(40).click()
    page.locator('.mine-cell').nth(1).click()
    expect(page.locator('.mine-burst')).to_have_count(1)
    expect(page.locator('.game-result')).to_have_count(0)
    expect(page.locator('.mine-burst')).to_have_count(0)
    expect(page.locator('.game-result')).to_contain_text('踩到地雷')
    page.get_by_role('button', name='重新开始', exact=True).click()
    page.locator('.mine-cell').nth(40).click()
    expect(page.locator('.mine-scanner')).to_have_count(1)
    expect(page.locator('.game-result')).to_have_count(0)
    page.emulate_media(reduced_motion='reduce')
    expect(page.locator('.game-result')).to_contain_text('恭喜过关')
    expect(page.locator('.mine-scanner')).to_have_count(0)
    page.emulate_media(reduced_motion='no-preference')
    print('Mines: flips, explosion and scanner precede results; restart cancels stale results and reduced motion completes immediately.', flush=True)

    visit('solitaire')
    page.locator('.stock-card').click()
    expect(page.locator('.solitaire-surface')).to_have_attribute('aria-busy', 'true')
    page.wait_for_function('Array.from(document.querySelectorAll(".is-card-moving")).some(el => el.getAnimations().some(a => a.effect.getKeyframes().some(f => f.transform?.includes("rotateY(180deg)"))))')
    page.locator('.is-card-moving').evaluate_all('els => els.forEach(el => el.getAnimations().forEach(a => {a.pause(); a.currentTime=120}))')
    assert page.locator('.is-card-moving').first.evaluate('''el => {
      const matrix = new DOMMatrixReadOnly(getComputedStyle(el).transform);
      return Math.abs(matrix.m13) > 0.45 && matrix.m43 > 10;
    }'''), 'The drawn card flattened before its flip could be seen'
    page.screenshot(path=str(out / 'game-motion-solitaire-flip.png'))
    page.locator('.is-card-moving').evaluate_all('els => els.forEach(el => el.getAnimations().forEach(a => a.finish()))')
    card_idle()
    old_id = page.locator('.waste-stack > button').get_attribute('data-card-id')
    old_bounds = page.locator(f'.waste-stack [data-card-id="{old_id}"]').bounding_box()
    page.locator('.stock-card').click()
    expect(page.locator('.waste-covered')).to_have_count(1)
    assert page.locator(f'.waste-stack [data-card-id="{old_id}"]').evaluate('(el) => el.getAnimations().length') == 0
    assert page.locator(f'.waste-stack [data-card-id="{old_id}"]').bounding_box() == old_bounds
    assert page.locator('.stock-card').evaluate('(el) => getComputedStyle(el).backgroundColor') != 'rgba(0, 0, 0, 0)'
    card_idle()
    # Valid late-game deals cover both a single card and a full stock's worth.
    recycle_durations = []
    single_card_durations = []
    for count in [1, 3, 24]:
        page.evaluate('''count => {
          const surface = document.querySelector('.solitaire-surface');
          const state = surface.__vueParentComponent.setupState;
          const card = (suit,rank) => ({suit,rank,faceUp:true});
          state.game = {stock:[], moves:0,
            waste:Array.from({length:count},(_,i)=>card(Math.floor(i/13),13-i%13)),
            foundations:Array.from({length:4},(_,suit)=>Array.from({length:13-Math.min(13,Math.max(0,count-suit*13))},(_,i)=>card(suit,i+1))),
            tableau:[[],[],[],[],[],[],[]]};
          state.history = [];
          window.recycleTimes = [];
          window.recycleObserver?.disconnect();
          window.recycleObserver = new MutationObserver(() => recycleTimes.push({busy:surface.getAttribute('aria-busy'),time:performance.now()}));
          recycleObserver.observe(surface, {attributes:true,attributeFilter:['aria-busy']});
        }''', count)
        page.locator('.stock-card').click()
        expect(page.locator('.is-recycling-card')).to_have_count(count)
        timing = page.locator('.is-recycling-card').evaluate_all('els => els.map(el => el.getAnimations()[0].effect.getTiming()).sort((a,b) => a.delay-b.delay)')
        assert len({t['delay'] for t in timing}) == count, 'Cards must leave individually'
        assert max(t['delay'] + t['duration'] for t in timing) <= 401
        assert min(t['duration'] for t in timing) >= 150, 'Each flip needs multiple visible frames'
        single_card_durations.append(timing[0]['duration'])
        card_idle()
        elapsed = page.evaluate('recycleTimes.find(t=>t.busy==="false").time-recycleTimes.find(t=>t.busy==="true").time')
        assert 0 < elapsed <= 500, (count, elapsed)
        recycle_durations.append(f'{count} cards: {elapsed:.0f}ms')
        expected_stock = [[i // 13, 13-i % 13, False] for i in reversed(range(count))]
        assert page.evaluate('''() => document.querySelector('.solitaire-surface').__vueParentComponent.setupState.game.stock.map(c => [c.suit,c.rank,c.faceUp])''') == expected_stock
        expect(page.locator('.pile-label').first).to_have_text(f'牌堆 · {count}')
        expect(page.locator('.game-stats strong').nth(1)).to_have_text('1')
        page.get_by_role('button', name='撤销', exact=True).click()
        card_idle()
        expect(page.locator('.waste-stack .playing-card')).to_have_count(count)
        expect(page.locator('.pile-label').first).to_have_text('牌堆 · 0')
    assert single_card_durations[0] > single_card_durations[-1], 'More cards must flip faster'
    print('Solitaire recycle timing: ' + ', '.join(recycle_durations), flush=True)
    # Disabling motion during recycling completes every remaining card and unlocks input.
    page.locator('.stock-card').click()
    expect(page.locator('.is-recycling-card')).to_have_count(24)
    page.locator('.is-recycling-card').evaluate_all('els => els.forEach(el => el.getAnimations().forEach(a => {a.pause(); a.currentTime=180}))')
    assert page.locator('.is-recycling-card').evaluate_all('''els => els.filter(el => {
      const transform = getComputedStyle(el).transform;
      if (transform === 'none') return false;
      const matrix = new DOMMatrixReadOnly(transform);
      return Math.abs(matrix.m13) > 0.3 && matrix.m43 > 10;
    }).length''') >= 3, 'The recycle should show a wave of visible 3D flips'
    page.screenshot(path=str(out / 'game-motion-solitaire-recycle.png'))
    page.emulate_media(reduced_motion='reduce')
    card_idle()
    expect(page.locator('.pile-label').first).to_have_text('牌堆 · 24')
    expect(page.locator('.is-recycling-card, .is-card-moving')).to_have_count(0)
    page.get_by_role('button', name='撤销', exact=True).click()
    card_idle()
    page.emulate_media(reduced_motion='no-preference')
    # Restart cancels the sequence without allowing an old card to reappear.
    page.locator('.stock-card').click()
    expect(page.locator('.is-recycling-card')).to_have_count(24)
    page.get_by_role('button', name='重新开始', exact=True).click()
    page.wait_for_timeout(500)
    card_idle()
    expect(page.locator('.pile-label').first).to_have_text('牌堆 · 24')
    expect(page.locator('.waste-stack .playing-card')).to_have_count(0)
    expect(page.locator('.game-stats strong').nth(1)).to_have_text('0')
    mouse_drag(page.locator('.tableau-card[data-card-id="0-1"]'), page.locator('.foundation-card').first)
    expect(page.locator('.game-stats strong').first).to_have_text('1 / 52')
    # A queen cannot enter an empty column; it returns without consuming a move.
    mouse_drag(page.locator('.tableau-card[data-card-id="3-12"]'), page.locator('.empty-column'))
    expect(page.locator('.game-stats strong').nth(1)).to_have_text('1')
    expect(page.locator('.game-status')).not_to_be_visible()
    expect(page.locator('.solitaire-column').nth(1).locator('[data-card-id="3-12"]')).to_have_count(1)
    expect(page.locator('.solitaire-column').first.locator('.tableau-card')).to_have_count(0)
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
    print('Solitaire: draw overlay, individual recycle, card order, cancellation, reduced motion, mouse/stack drag, undo and Escape passed.', flush=True)

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
        if not page.evaluate('matchMedia("(prefers-reduced-motion: reduce)").matches'):
            expect(page.locator('.game-result')).to_have_count(0)
        card_idle()
    endgame()
    expect(page.locator('.solitaire-celebration')).to_have_count(1)
    expect(page.locator('.game-result')).to_have_count(0)
    page.wait_for_timeout(600)
    first = page.locator('.solitaire-celebration').evaluate('(el) => el.toDataURL()')
    page.wait_for_timeout(200)
    assert first != page.locator('.solitaire-celebration').evaluate('(el) => el.toDataURL()'), 'Celebration is static'
    page.screenshot(path=str(out / 'game-motion-solitaire-win.png'), full_page=True)
    expect(page.locator('.solitaire-celebration')).to_have_count(0, timeout=6500)
    expect(page.locator('.game-result')).to_contain_text('接龙成功')
    expect(page.get_by_role('button', name='重播庆祝', exact=True)).to_have_count(0)
    page.get_by_role('button', name='撤销', exact=True).click()
    card_idle()
    expect(page.locator('.game-result')).to_have_count(0)
    endgame()
    expect(page.locator('.solitaire-celebration')).to_have_count(1)
    page.get_by_role('button', name='跳过庆祝', exact=True).click()
    expect(page.locator('.solitaire-celebration')).to_have_count(0)
    expect(page.locator('.game-result')).to_contain_text('接龙成功')
    page.get_by_role('button', name='重新开始', exact=True).click()
    endgame()
    expect(page.locator('.solitaire-celebration')).to_have_count(1)
    page.get_by_role('button', name='重新开始', exact=True).click()
    expect(page.locator('.solitaire-celebration, .game-result')).to_have_count(0)
    endgame()
    expect(page.locator('.solitaire-celebration')).to_have_count(1)
    page.emulate_media(reduced_motion='reduce')
    expect(page.locator('.solitaire-celebration')).to_have_count(0)
    expect(page.locator('.game-result')).to_contain_text('接龙成功')
    page.get_by_role('button', name='重新开始', exact=True).click()
    endgame()
    expect(page.locator('.game-status')).to_contain_text('接龙成功')
    expect(page.locator('.solitaire-celebration')).to_have_count(0)
    print('Solitaire victory: result follows celebration, no replay, skip, undo, restart and reduced motion passed.', flush=True)

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
    phone.wait_for_timeout(700)
    phone.locator('.solitaire-scroll').evaluate('(el) => el.scrollTo({left:0,behavior:"instant"})')
    source.scroll_into_view_if_needed()
    a = source.bounding_box()
    start = {'x':a['x']+20,'y':a['y']+18}
    cdp.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[start]})
    phone.wait_for_timeout(350)
    expect(phone.locator('.solitaire-drag-layer')).to_have_count(1)
    cdp.send('Input.dispatchTouchEvent', {'type':'touchMove','touchPoints':[{'x':355,'y':start['y']}]})
    phone.wait_for_timeout(450)
    assert phone.locator('.solitaire-scroll').evaluate('(el) => el.scrollLeft') > 40, phone.evaluate('({scroll: document.querySelector(".solitaire-scroll").scrollLeft, dragging:!!document.querySelector(".solitaire-drag-layer"), rect:document.querySelector(".solitaire-scroll").getBoundingClientRect().toJSON()})')
    cdp.send('Input.dispatchTouchEvent', {'type':'touchCancel','touchPoints':[]})
    expect(phone.locator('.solitaire-drag-layer')).to_have_count(0)
    phone.set_viewport_size({'width':844,'height':390})
    phone.reload(wait_until='networkidle')
    expect(phone.locator('.solitaire-orientation-hint')).not_to_be_visible()
    colors = []
    for theme in ['dark','light']:
        phone.evaluate('(theme) => document.documentElement.dataset.theme=theme',theme)
        phone.wait_for_timeout(350)
        colors.append([phone.locator(selector).first.evaluate('(el) => getComputedStyle(el).backgroundColor') for selector in ['.tableau-card:not(.card-back)', '.tableau-card.card-back']])
        phone.screenshot(path=str(out / f'game-motion-cards-{theme}-landscape.png'), full_page=True)
    assert all(dark != light for dark, light in zip(colors[0], colors[1]))
    assert phone.evaluate('document.documentElement.scrollWidth <= innerWidth')
    print('Touch: hold-to-drag, ordinary scrolling, edge scrolling, cancellation, landscape hint and card themes passed.', flush=True)
    # Fullscreen uses a uniform fit transform: animation and pointer coordinates must agree.
    page.set_viewport_size({'width':320,'height':568})
    page.emulate_media(reduced_motion='reduce')
    visit('2048')
    page.get_by_role('button', name='网页全屏', exact=True).click()
    page.emulate_media(reduced_motion='no-preference')
    expect(page.locator('.number-motion-toggle input')).to_be_enabled()
    expect(page.locator('.number-motion-toggle input')).not_to_be_checked()
    # Capture the short flight before it finishes; timing itself is checked above.
    page.evaluate('''() => {
      const animate = Element.prototype.animate;
      Element.prototype.animate = function(...args) {
        const animation = animate.apply(this, args);
        if (this.matches('.number-flight')) animation.pause();
        return animation;
      };
    }''')
    page.locator('.number-board').focus()
    page.keyboard.press('ArrowLeft')
    expect(page.locator('.number-flight')).to_have_count(2)
    page.locator('.number-flight').evaluate_all('els => els.forEach(el => el.getAnimations().forEach(a => {a.pause();a.currentTime=0}))')
    starts = page.locator('.number-flight').evaluate_all('els => els.map(el => el.getBoundingClientRect().toJSON())')
    cells = page.locator('.number-tile').evaluate_all('els => els.map(el => el.getBoundingClientRect().toJSON())')
    for i, flight in enumerate(starts):
        assert all(abs(flight[key]-cells[i][key])<1 for key in ['x','y','width','height']), (flight, cells[i])
    page.locator('.number-flight').evaluate_all('els => els.forEach(el => el.getAnimations().forEach(a => {a.currentTime=140}))')
    ends = page.locator('.number-flight').evaluate_all('els => els.map(el => el.getBoundingClientRect().toJSON())')
    assert all(abs(flight['x']-cells[0]['x'])<1 for flight in ends)
    page.locator('.number-flight').evaluate_all('els => els.forEach(el => el.getAnimations().forEach(a => a.finish()))')
    expect(page.locator('.number-board')).to_have_attribute('aria-busy','false')
    expect(page.locator('.game-stats strong').first).to_have_text('4')
    page.emulate_media(reduced_motion='reduce')
    visit('solitaire')
    page.get_by_role('button', name='网页全屏', exact=True).click()
    page.emulate_media(reduced_motion='no-preference')
    stock = page.locator('.stock-card').bounding_box()
    page.locator('.stock-card').click()
    expect(page.locator('.is-card-moving')).to_have_count(1)
    page.locator('.is-card-moving').evaluate('el => el.getAnimations().forEach(a => {a.pause();a.currentTime=0})')
    drawn = page.locator('.is-card-moving').bounding_box()
    assert all(abs(drawn[key]-stock[key])<1 for key in ['x','y','width','height']), (drawn, stock)
    page.locator('.is-card-moving').evaluate('el => el.getAnimations().forEach(a => a.finish())')
    card_idle()
    mouse_drag(page.locator('.tableau-card[data-card-id="0-1"]'), page.locator('.foundation-card').first)
    expect(page.locator('.game-stats strong').first).to_have_text('1 / 52')
    # A long column changes the natural game height; fit must update without scrolling.
    page.set_viewport_size({'width':844,'height':390})
    page.wait_for_timeout(100)
    before = page.locator('.game-fit-content').evaluate('el => new DOMMatrix(getComputedStyle(el).transform).a')
    page.evaluate("""() => {
        const state=document.querySelector('.solitaire-surface').__vueParentComponent.setupState;
        const cards=[...state.game.stock,...state.game.waste,...state.game.tableau.flat(),...state.game.foundations.flat()];
        state.game={stock:cards.slice(19),waste:[],foundations:[[],[],[],[]],moves:0,
            tableau:[cards.slice(0,19).map((c,i)=>({...c,faceUp:i>=6})),[],[],[],[],[],[]]};
    }""")
    page.wait_for_function("""previous => {
        const el=document.querySelector('.game-fit-content');
        return new DOMMatrix(getComputedStyle(el).transform).a < previous;
    }""", arg=before)
    assert page.locator('.tableau-card, .game-surface').evaluate_all('''els => els.every(el => {
        const r=el.getBoundingClientRect();return r.left>=0 && r.top>=0 && r.right<=innerWidth && r.bottom<=innerHeight;
    })'''), 'Long columns must remain fully visible'
    page.screenshot(path=str(out / 'game-motion-fullscreen-long-column.png'))
    page.get_by_role('button', name='重新开始', exact=True).click()
    page.wait_for_function('previous => new DOMMatrix(getComputedStyle(document.querySelector(".game-fit-content")).transform).a >= previous', arg=before-0.01)
    print('Fullscreen fit: scaled 2048 motion, card draw, mouse drop and live long-column resizing passed.', flush=True)
    assert not errors, errors
    touch.close()
    browser.close()
print('Game motion and drag checks passed. Screenshots: artifacts/game-motion-*.png')

import runpy
runpy.run_path('scripts/check-games-classics-motion.py', run_name='__main__')

runpy.run_path('scripts/check-games-arcade-motion.py', run_name='__main__')

runpy.run_path('scripts/check-games-sliding-jump-motion.py', run_name='__main__')
