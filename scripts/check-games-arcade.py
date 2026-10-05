"""Snake and Popstar: public controls, responsive themes, touch and fullscreen."""
import os
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:4173').rstrip('/')
out = Path('artifacts')
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.add_init_script('Math.random = () => 0')
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    page.clock.install(time=now)
    page.clock.pause_at(now)
    page.goto(base + '/games/snake', wait_until='networkidle')
    expect(page.locator('.snake-segment')).to_have_count(3)
    before = page.locator('.snake-segment').first.get_attribute('style')
    page.clock.run_for(1000)
    assert page.locator('.snake-segment').first.get_attribute('style') == before
    page.get_by_role('button', name='开始游戏', exact=True).click()
    page.locator('.snake-board').press('ArrowLeft')
    page.clock.run_for(150)
    assert '600%' in page.locator('.snake-segment').first.get_attribute('style'), 'No direct reversal'
    # Two rapid turns must apply on separate ticks, rather than reversing into the neck.
    page.locator('.snake-board').press('ArrowUp')
    page.locator('.snake-board').press('ArrowLeft')
    page.clock.run_for(150)
    assert page.locator('.snake-segment').first.get_attribute('data-direction') == 'up'
    page.clock.run_for(150)
    assert page.locator('.snake-segment').first.get_attribute('data-direction') == 'left'
    page.locator('.snake-board').press('p')
    before = page.locator('.snake-segment').first.get_attribute('style')
    page.clock.run_for(1000)
    assert page.locator('.snake-segment').first.get_attribute('style') == before
    page.get_by_role('button', name='继续游戏', exact=True).click()
    page.evaluate('window.dispatchEvent(new Event("blur"))')
    expect(page.get_by_role('button', name='继续游戏', exact=True)).to_be_visible()
    page.get_by_role('button', name='重新开始', exact=True).click()
    page.get_by_label('起始速度').select_option('0')
    page.get_by_role('button', name='开始游戏', exact=True).click()
    # Food is at (0,0). Reach it using actual timer updates and buttons.
    page.get_by_role('button', name='向上', exact=True).click()
    page.clock.run_for(9 * 210)
    page.get_by_role('button', name='向左', exact=True).click()
    page.clock.run_for(5 * 210)
    expect(page.locator('.snake-segment')).to_have_count(4)
    expect(page.locator('.game-stats strong').first).to_have_text('10')
    page.clock.run_for(210)
    expect(page.locator('.game-result')).to_contain_text('撞到了')
    page.get_by_role('button', name='重新开始', exact=True).click()
    page.locator('.header .brand').focus()
    page.keyboard.press('ArrowUp')
    expect(page.locator('.game-stats strong').first).to_have_text('0')
    context.close()

    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
    page = context.new_page()
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.add_init_script('Math.random = () => 0')
    page.goto(base + '/games/popstar', wait_until='networkidle')
    expect(page.locator('.star-cell')).to_have_count(100)
    expect(page.locator('.star-cell[tabindex="0"]')).to_have_count(1)
    page.locator('.star-cell').nth(90).focus()
    page.keyboard.press('ArrowRight')
    expect(page.locator('.star-cell').nth(91)).to_be_focused()
    page.keyboard.press('Enter')
    expect(page.locator('.star-cell.is-selected')).to_have_count(100)
    expect(page.locator('.game-stats strong').nth(1)).to_have_text('0')
    page.keyboard.press('Escape')
    expect(page.locator('.star-cell.is-selected')).to_have_count(0)
    page.keyboard.press('Space')
    page.keyboard.press('Space')
    expect(page.locator('.game-result')).to_contain_text('第 1 关完成')
    expect(page.locator('.game-stats strong').nth(1)).to_have_text('52000')
    expect(page.get_by_role('button', name='下一关', exact=True)).to_be_focused()
    page.get_by_role('button', name='下一关', exact=True).click()
    expect(page.locator('.game-stats strong').first).to_have_text('2')
    expect(page.locator('.game-stats strong').nth(1)).to_have_text('52000')
    expect(page.locator('.game-stats strong').nth(2)).to_have_text('3000')
    expect(page.locator('.star-cell')).to_have_count(100)
    page.get_by_role('button', name='重新开始', exact=True).click()
    expect(page.locator('.game-stats strong').first).to_have_text('1')
    expect(page.locator('.game-stats strong').nth(1)).to_have_text('0')
    context.close()

    # Random colored boards for current screenshots and real geometry checks.
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
    page = context.new_page()
    page.on('pageerror', lambda e: errors.append(str(e)))
    for game in ['snake', 'popstar']:
        for theme in ['dark', 'light']:
            for width in [320, 390, 480, 481, 760, 768, 1024, 1051, 1440]:
                page.set_viewport_size({'width': width, 'height': 1000})
                page.goto(base + '/games/' + game, wait_until='networkidle')
                page.evaluate('(theme) => document.documentElement.dataset.theme = theme', theme)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (game, theme, width)
                expect(page.locator('.game-session-note')).to_be_visible()
                if width in [320, 390, 768, 1024, 1440]:
                    page.locator('.game-surface').screenshot(path=str(out / f'game-arcade-{game}-{theme}-{width}.png'))
        page.set_viewport_size({'width': 1440, 'height': 1000})
        page.goto(base + '/games/' + game, wait_until='networkidle')
        if game == 'popstar':
            page.locator('.star-cell').first.click()
        before = page.locator('.game-stats').inner_text()
        board = page.locator('.' + ('snake' if game == 'snake' else 'popstar') + '-board')
        previous = board.inner_html()
        page.get_by_role('button', name='网页全屏', exact=True).click()
        for width, height in [(320, 740), (390, 844), (844, 390), (1440, 900)]:
            page.set_viewport_size({'width': width, 'height': height})
            page.wait_for_timeout(150)
            box = page.locator('.game-surface').bounding_box()
            assert box and box['x'] >= -1 and box['y'] >= -1 and box['x'] + box['width'] <= width + 1 and box['y'] + box['height'] <= height + 1, (game, width, box)
            expect(page.locator('.game-guide')).not_to_be_visible()
            assert page.locator('.game-stats').inner_text() == before
            assert board.inner_html() == previous
            if width in [390, 844]:
                page.screenshot(path=str(out / f'game-arcade-{game}-fullscreen-{width}.png'))
        page.keyboard.press('Escape')
        expect(page.get_by_role('button', name='网页全屏', exact=True)).to_be_focused()
        assert page.locator('.game-stats').inner_text() == before
        page.reload(wait_until='networkidle')
        expect(board).to_be_visible()
    context.close()

    touch = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, reduced_motion='reduce')
    phone = touch.new_page()
    phone.on('pageerror', lambda e: errors.append(str(e)))
    phone.goto(base + '/games/snake', wait_until='networkidle')
    phone.get_by_label('起始速度').select_option('0')
    phone.get_by_role('button', name='开始游戏', exact=True).tap()
    phone.locator('.snake-board').scroll_into_view_if_needed()
    box = phone.locator('.snake-board').bounding_box()
    session = touch.new_cdp_session(phone)
    x, y = box['x'] + box['width'] / 2, box['y'] + box['height'] / 2
    session.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]})
    session.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x, 'y': y - 65}]})
    session.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
    expect(phone.locator('.snake-segment').first).to_have_attribute('data-direction', 'up')
    phone.get_by_role('button', name='暂停', exact=True).tap()
    phone.goto(base + '/games/popstar', wait_until='networkidle')
    pair = phone.locator('.star-cell').evaluate_all('''cells => {
      for (const cell of cells) {
        const i = +cell.dataset.index, color = cell.querySelector('.star-gem').dataset.color;
        for (const n of [i+10, ...(i%10<9 ? [i+1] : [])]) {
          const other = cells.find(c => +c.dataset.index === n);
          if (other?.querySelector('.star-gem').dataset.color === color) return i;
        }
      }
    }''')
    tile = phone.locator(f'.star-cell[data-index="{pair}"]')
    tile.tap()
    selected = phone.locator('.star-cell.is-selected').count()
    assert selected >= 2
    tile.tap()
    expect(phone.locator('.star-cell')).to_have_count(100 - selected)
    touch.close()
    assert not errors, errors
    browser.close()
print('Arcade browser passed: keyboard, touch, scores, pause, restart, 9 widths, themes, fullscreen state and focus. Fresh screenshots: artifacts/game-arcade-*.png')
