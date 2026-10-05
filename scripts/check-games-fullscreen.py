"""Web fullscreen keeps the same game, confines focus, and supports touch/drag."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:5173').rstrip('/')
out = Path('artifacts')
out.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    context = browser.new_context(viewport={'width':1440,'height':1000}, reduced_motion='reduce')
    context.add_init_script('Math.random = () => 0')
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    for game in ['2048', 'minesweeper', 'solitaire']:
        page.goto(base + '/games/' + game, wait_until='networkidle')
        if game == '2048':
            page.locator('.number-board').focus()
            page.keyboard.press('ArrowLeft')
        elif game == 'minesweeper':
            page.locator('.mine-cell').nth(40).click()
        else:
            page.locator('.stock-card').click()
        page.evaluate('window.savedSurface = document.querySelector(".game-surface")')
        page.get_by_role('button', name='网页全屏', exact=True).click()
        expect(page.locator('dialog[open]')).to_have_count(1)
        assert page.evaluate('savedSurface === document.querySelector(".game-surface")'), 'Fullscreen remounted the game'
        expect(page.locator('.game-guide')).not_to_be_visible()
        if game == '2048':
            expect(page.locator('.game-stats strong').first).to_have_text('4')
            page.get_by_role('button', name='向下移动').click()
        elif game == 'minesweeper':
            assert page.locator('.mine-cell.is-open').count() > 1
        else:
            expect(page.locator('.pile-label').first).to_have_text('牌堆 · 23')
            page.get_by_role('button', name='撤销', exact=True).click()
            expect(page.locator('.pile-label').first).to_have_text('牌堆 · 24')
        page.get_by_role('button', name='退出全屏', exact=True).focus()
        page.locator('.header .brand').evaluate('el => el.focus()')
        assert page.evaluate('!!document.activeElement.closest("dialog[open]")'), (game, 'Background must be inert')
        for _ in range(12):
            page.keyboard.press('Tab')
            assert page.evaluate('document.activeElement === document.body || !!document.activeElement.closest("dialog[open]")')
        for theme in ['dark', 'light']:
            page.evaluate('theme => document.documentElement.dataset.theme=theme', theme)
            for width, height in [(320,844),(390,844),(768,1000),(1024,1000),(1440,1000),(844,390)]:
                page.set_viewport_size({'width':width,'height':height})
                page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                page.locator('.game-play-content').evaluate('el => el.scrollTo({top:0,behavior:"instant"})')
                page.wait_for_function('''() => {
                  const el=document.querySelector('dialog[open]');
                  const box=el.getBoundingClientRect();
                  return box.x===0 && box.y===0 && Math.abs(box.width-innerWidth)<1 && Math.abs(box.height-innerHeight)<1;
                }''', timeout=4000)
                assert page.locator('.game-play-content').evaluate('el => el.scrollWidth <= el.clientWidth'), (game, theme, width, height)
                bounds = page.get_by_role('button', name='退出全屏', exact=True).bounding_box()
                assert bounds['x'] >= 0 and bounds['y'] >= 0 and bounds['x']+bounds['width'] <= width
                restart = page.get_by_role('button', name='重新开始', exact=True).bounding_box()
                assert bounds['x'] > restart['x'] + restart['width'] and abs(bounds['y'] - restart['y']) < 1
                assert page.get_by_role('button', name='退出全屏', exact=True).inner_text() == ''
                if width == 844 and game != 'solitaire':
                    board_end = page.locator('.number-directions' if game == '2048' else '.mine-board-scroll').bounding_box()
                    assert board_end['y'] + board_end['height'] <= height, (game, 'Landscape board/controls clipped')
                if width in [390, 1440, 844]:
                    page.screenshot(path=str(out / f'game-fullscreen-{game}-{theme}-{width}.png'))
        page.set_viewport_size({'width':1440,'height':1000})
        page.get_by_role('button', name='退出全屏', exact=True).click()
        expect(page.locator('dialog[open]')).to_have_count(0)
        expect(page.get_by_role('button', name='网页全屏', exact=True)).to_be_focused()
        expect(page.locator('.game-guide')).to_be_visible()
        assert page.evaluate('savedSurface === document.querySelector(".game-surface")')
        page.get_by_role('button', name='网页全屏', exact=True).click()
        page.keyboard.press('Escape')
        expect(page.locator('dialog[open]')).to_have_count(0)
        assert page.locator('html').evaluate('el => !el.classList.contains("game-fullscreen-open")')
    # Drag ghosts must live inside the modal top layer, and dropping must still work.
    page.get_by_role('button', name='网页全屏', exact=True).click()
    source = page.locator('.tableau-card[data-card-id="0-1"]')
    a, b = source.bounding_box(), page.locator('.foundation-card').first.bounding_box()
    page.mouse.move(a['x']+25,a['y']+18)
    page.mouse.down()
    page.mouse.move(b['x']+30,b['y']+30,steps=8)
    expect(page.locator('dialog .solitaire-drag-layer')).to_have_count(1)
    expect(page.locator('.foundation-card.is-drop-target')).to_have_count(1)
    page.mouse.up()
    expect(page.locator('.game-stats strong').first).to_have_text('1 / 52')
    page.get_by_role('button', name='退出全屏', exact=True).click()
    # Browser history navigation also removes the modal and restores document scrolling.
    page.goto(base + '/game', wait_until='networkidle')
    page.locator('.game-card[href="/games/solitaire"]').click()
    page.get_by_role('button', name='网页全屏', exact=True).click()
    page.go_back()
    expect(page.locator('.games-grid')).to_be_visible()
    expect(page.locator('dialog[open]')).to_have_count(0)
    assert page.locator('html').evaluate('el => !el.classList.contains("game-fullscreen-open")')
    # Entry/exit visibly fade; Escape can reverse entry, and reduced motion finishes exit.
    page.emulate_media(reduced_motion='no-preference')
    page.goto(base + '/games/2048', wait_until='networkidle')
    page.evaluate('window.savedSurface=document.querySelector(".game-surface")')
    page.get_by_role('button', name='网页全屏', exact=True).click()
    page.wait_for_function('document.querySelector("dialog[open]")?.getAnimations().length > 0')
    page.locator('dialog[open]').evaluate('el => el.getAnimations().forEach(a => {a.pause(); a.currentTime=60})')
    assert page.locator('dialog[open]').evaluate('el => {const opacity=Number(getComputedStyle(el).opacity); return opacity>0 && opacity<1}')
    page.keyboard.press('Escape')
    page.wait_for_function('document.querySelector("dialog[open]")?.getAnimations().some(a => a.playState === "running")')
    page.locator('dialog[open]').evaluate('el => el.getAnimations().forEach(a => {a.pause(); a.currentTime=50})')
    assert page.locator('dialog[open]').evaluate('el => {const opacity=Number(getComputedStyle(el).opacity); return opacity>0 && opacity<1}')
    page.emulate_media(reduced_motion='reduce')
    expect(page.locator('dialog[open]')).to_have_count(0)
    expect(page.get_by_role('button', name='网页全屏', exact=True)).to_be_focused()
    assert page.evaluate('savedSurface===document.querySelector(".game-surface")')
    assert page.locator('.game-viewport').evaluate('el => el.getAnimations().length') == 0
    touch = browser.new_context(viewport={'width':390,'height':844}, has_touch=True, is_mobile=True, reduced_motion='reduce')
    touch.add_init_script('Math.random = () => 0')
    phone = touch.new_page()
    phone.on('pageerror', lambda e: errors.append(str(e)))
    phone.goto(base + '/games/solitaire', wait_until='networkidle')
    phone.get_by_role('button', name='网页全屏', exact=True).scroll_into_view_if_needed()
    previous_scroll = phone.evaluate('scrollY')
    phone.get_by_role('button', name='网页全屏', exact=True).tap()
    source = phone.locator('.tableau-card[data-card-id="0-1"]')
    source.scroll_into_view_if_needed()
    a, b = source.bounding_box(), phone.locator('.foundation-card').first.bounding_box()
    cdp = touch.new_cdp_session(phone)
    cdp.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[{'x':a['x']+25,'y':a['y']+18}]})
    phone.wait_for_timeout(350)
    expect(phone.locator('dialog .solitaire-drag-layer')).to_have_count(1)
    cdp.send('Input.dispatchTouchEvent', {'type':'touchMove','touchPoints':[{'x':b['x']+30,'y':b['y']+30}]})
    cdp.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]})
    expect(phone.locator('.game-stats strong').first).to_have_text('1 / 52')
    phone.get_by_role('button', name='退出全屏', exact=True).tap()
    expect(phone.locator('dialog[open]')).to_have_count(0)
    assert abs(phone.evaluate('scrollY') - previous_scroll) < 2
    assert not errors, errors
    browser.close()
print('Web fullscreen: games/history preserved, modal focus, exit/Escape/navigation cleanup, mouse/touch drag, themes and responsive layouts passed.')
