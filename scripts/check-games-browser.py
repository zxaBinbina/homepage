"""Game interactions, routes, keyboard/touch and responsive layouts on a build preview."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:5173').rstrip('/')
out = Path('artifacts')
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
    # A reproducible deal, without changing game code or reaching into Vue state.
    context.add_init_script('Math.random = () => 0')
    context.set_default_timeout(10000)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(base + '/game', wait_until='networkidle')
    expect(page.locator('.game-card')).to_have_count(3)
    expect(page.locator('.desktop-nav [aria-current="page"]')).to_have_text('游戏')
    assert page.locator('audio').count() == 0
    page.evaluate('window.gameProbe = document.querySelector(".header")')
    page.locator('.game-card[href="/games/2048"]').click()
    expect(page.locator('.number-board')).to_be_visible()
    assert page.evaluate('window.gameProbe === document.querySelector(".header")')
    initial = page.locator('.number-tile').all_text_contents()
    assert initial[:2] == ['2', '2']
    page.locator('.number-board').focus()
    page.keyboard.press('ArrowLeft')
    expect(page.locator('.game-stats strong').first).to_have_text('4')
    expect(page.locator('.number-tile').first).to_have_text('4')
    page.get_by_role('button', name='撤销', exact=True).click()
    assert page.locator('.number-tile').all_text_contents() == initial
    expect(page.locator('.game-stats strong').first).to_have_text('0')
    page.get_by_role('button', name='向下移动').click()
    expect(page.get_by_role('button', name='撤销', exact=True)).to_be_enabled()
    page.get_by_role('button', name='重新开始').click()
    assert page.locator('.number-tile').all_text_contents() == initial
    expect(page.get_by_role('button', name='撤销', exact=True)).to_be_disabled()
    # Keyboard listeners must be confined to the game, leaving the header alone.
    page.locator('.header .brand').focus()
    page.keyboard.press('ArrowRight')
    assert page.locator('.number-tile').all_text_contents() == initial
    page.get_by_role('link', name='全部游戏', exact=True).click()
    page.locator('.game-card[href="/games/minesweeper"]').click()
    expect(page.locator('.mine-cell')).to_have_count(81)
    page.get_by_role('button', name='插旗', exact=True).click()
    page.locator('.mine-cell').nth(80).click()
    expect(page.locator('.mine-cell').nth(80)).to_have_attribute('aria-label', '第 9 行第 9 列：已插旗')
    expect(page.locator('.game-stats strong').first).to_have_text('9')
    page.get_by_role('button', name='翻开', exact=True).click()
    page.locator('.mine-cell').nth(40).click()
    expect(page.locator('.mine-cell').nth(40)).to_have_class('mine-cell is-open')
    assert page.locator('.mine-cell.is-open').count() > 1
    page.locator('.mine-cell').nth(0).focus()
    page.keyboard.press('f')
    expect(page.locator('.mine-cell').nth(0)).to_have_attribute('aria-label', '第 1 行第 1 列：已插旗')
    page.keyboard.press('f')
    page.keyboard.press('ArrowRight')
    expect(page.locator('.mine-cell').nth(1)).to_be_focused()
    page.keyboard.press('Enter')
    expect(page.locator('.game-status')).to_contain_text('踩到地雷')
    assert page.locator('.mine-cell.is-mine').count() == 10
    before = page.locator('.game-stats').inner_text()
    page.locator('.mine-cell').nth(0).focus()
    page.keyboard.press('f')
    assert page.locator('.game-stats').inner_text() == before
    page.get_by_role('button', name='重新开始').click()
    page.get_by_label('难度', exact=True).select_option('1')
    expect(page.locator('.mine-cell')).to_have_count(144)
    expect(page.locator('.game-stats strong').first).to_have_text('24')
    # With the deterministic first reveal at the center, the top ten cells are mines.
    page.get_by_label('难度', exact=True).select_option('0')
    page.locator('.mine-cell').nth(40).click()
    for i in range(10, 81):
        if '恭喜过关' in page.locator('.game-status').inner_text():
            break
        page.locator('.mine-cell').nth(i).click()
    expect(page.locator('.game-status')).to_contain_text('恭喜过关')
    page.get_by_role('link', name='全部游戏', exact=True).click()
    page.locator('.game-card[href="/games/solitaire"]').click()
    expect(page.locator('.solitaire-columns')).to_be_visible()
    expect(page.locator('.tableau-card')).to_have_count(28)
    expect(page.locator('.tableau-card.card-back')).to_have_count(21)
    page.get_by_role('button', name='翻一张牌，牌堆剩余 24 张', exact=True).click()
    expect(page.locator('.pile-label').first).to_have_text('牌堆 · 23')
    page.get_by_role('button', name='撤销', exact=True).click()
    expect(page.locator('.pile-label').first).to_have_text('牌堆 · 24')
    page.get_by_role('button', name='第 1 列，黑桃 A', exact=True).click()
    page.get_by_role('button', name='黑桃收牌区，空，从 A 开始', exact=True).click()
    expect(page.locator('.game-stats strong').first).to_have_text('1 / 52')
    page.get_by_role('button', name='第 2 列，方块 Q', exact=True).click()
    page.get_by_role('button', name='放到第 5 列', exact=True).click()
    expect(page.get_by_role('button', name='第 2 列，方块 K', exact=True)).to_be_visible()
    expect(page.locator('.tableau-card.card-back')).to_have_count(20)
    page.get_by_role('button', name='撤销', exact=True).click()
    expect(page.locator('.tableau-card.card-back')).to_have_count(21)
    page.get_by_role('button', name='第 2 列，方块 Q', exact=True).click()
    page.get_by_role('button', name='放到第 1 列', exact=True).click()
    expect(page.locator('.game-status')).not_to_be_visible()
    expect(page.locator('.solitaire-column').first.locator('.tableau-card')).to_have_count(0)
    expect(page.get_by_role('button', name='第 2 列，方块 Q', exact=True)).to_be_visible()
    expect(page.get_by_role('button', name='第 2 列，方块 Q', exact=True)).to_have_attribute('aria-pressed', 'true')
    page.keyboard.press('Escape')
    expect(page.get_by_role('button', name='取消选牌', exact=True)).to_be_disabled()
    for _ in range(24):
        page.locator('.stock-card').click()
    expect(page.locator('.stock-card')).to_have_attribute('aria-label', '重新翻牌')
    page.locator('.stock-card').click()
    expect(page.locator('.pile-label').first).to_have_text('牌堆 · 24')
    page.get_by_role('button', name='重新开始').click()
    expect(page.locator('.game-stats strong').nth(1)).to_have_text('0')

    routes = [('/game', '.games-grid'), ('/games/2048', '.number-board'), ('/games/minesweeper', '.mine-board'), ('/games/solitaire', '.solitaire-table')]
    for path, marker in routes:
        response = context.request.get(base + path)
        assert response.status == 200
        assert f'href="https://zxabinbina.cc.cd{path}"' in response.text()
        for suffix in ['/', '.html', '/index.html']:
            response = context.request.get(base + path + suffix + '?source=legacy', max_redirects=0)
            assert response.status == 301
            assert response.headers['location'] == path + '?source=legacy'
        page.goto(base + path, wait_until='networkidle')
        page.reload(wait_until='networkidle')
        expect(page.locator(marker)).to_be_visible()
        for theme in ['dark', 'light']:
            page.evaluate('(theme) => { localStorage.setItem("homepage-theme", theme); document.documentElement.dataset.theme = theme }', theme)
            for width in [320, 390, 480, 481, 760, 761, 768, 1024, 1050, 1051, 1440]:
                page.set_viewport_size({'width': width, 'height': 1000})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (path, theme, width)
                assert page.locator('main').evaluate('(el) => el.getBoundingClientRect().width <= innerWidth')
                if path.startswith('/games/'):
                    expect(page.locator('.game-heading > p')).to_have_count(0)
                    expect(page.locator('.game-status')).not_to_be_visible()
                    expect(page.locator('.game-session-note')).to_have_text('离开或刷新页面会重新开局。')
                    assert page.evaluate('''() => {
                        const guide = document.querySelector('.game-guide');
                        const game = document.querySelector('.game-surface');
                        const note = document.querySelector('.game-session-note');
                        const tips = document.querySelector('.game-guide-tips');
                        return !!(guide.compareDocumentPosition(game) & Node.DOCUMENT_POSITION_FOLLOWING)
                            && guide.getBoundingClientRect().bottom <= game.getBoundingClientRect().top
                            && tips.getBoundingClientRect().bottom <= note.getBoundingClientRect().top;
                    }'''), (path, theme, width, 'Tutorial and reminder must precede gameplay')
                if width > 760:
                    # No wrapping or overlap between brand, navigation, and actions.
                    assert page.evaluate('''() => {
                        const brand = document.querySelector('.brand').getBoundingClientRect();
                        const nav = document.querySelector('.desktop-nav').getBoundingClientRect();
                        const actions = document.querySelector('.header-actions').getBoundingClientRect();
                        const header = document.querySelector('.header').getBoundingClientRect();
                        return brand.right <= nav.left && nav.right <= actions.left && actions.right <= header.right;
                    }'''), ('header overlap', width)
                if width in [320, 390, 768, 1024, 1440]:
                    page.screenshot(path=str(out / f'game-{path.split("/")[-1]}-{theme}-{width}.png'), full_page=True)
        page.set_viewport_size({'width': 390, 'height': 844})
        page.get_by_role('button', name='打开菜单', exact=True).click()
        expect(page.locator('#mobile-nav [aria-current="page"]')).to_have_text('游戏')
        page.locator('#mobile-nav').get_by_role('link', name='游戏', exact=True).click()
        expect(page.locator('#mobile-nav')).to_have_count(0)
        expect(page.locator('.games-grid')).to_be_visible()

    # Real touch input, including a cancelled gesture, on a narrow viewport.
    touch = browser.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True, reduced_motion='reduce')
    touch.add_init_script('Math.random = () => 0')
    phone = touch.new_page()
    phone.on('pageerror', lambda error: errors.append(str(error)))
    phone.goto(base + '/games/2048', wait_until='networkidle')
    phone.locator('.number-board').scroll_into_view_if_needed()
    box = phone.locator('.number-board').bounding_box()
    cdp = touch.new_cdp_session(phone)
    start = {'x': box['x'] + box['width'] - 40, 'y': box['y'] + 80}
    end = {'x': box['x'] + 40, 'y': box['y'] + 80}
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [start]})
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [end]})
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
    expect(phone.locator('.game-stats strong').first).to_have_text('4')
    snapshot = phone.locator('.number-tile').all_text_contents()
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [start]})
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchCancel', 'touchPoints': []})
    assert phone.locator('.number-tile').all_text_contents() == snapshot
    phone.goto(base + '/games/minesweeper', wait_until='networkidle')
    phone.get_by_role('button', name='插旗', exact=True).tap()
    phone.locator('.mine-cell').first.tap()
    expect(phone.locator('.mine-cell').first).to_have_attribute('aria-label', '第 1 行第 1 列：已插旗')
    touch.close()
    page.emulate_media(reduced_motion='no-preference')
    page.set_viewport_size({'width': 1440, 'height': 1000})
    page.goto(base + '/games/2048', wait_until='networkidle')
    page.locator('.number-board').focus()
    page.keyboard.press('ArrowLeft')
    expect(page.locator('.number-tile').first).to_have_text('4')
    assert not errors, errors
    browser.close()
print('Game interactions, keyboard/touch, routes and refresh, themes, reduced motion, responsive widths and shared navigation passed. Fresh screenshots: artifacts/game-*.png')
