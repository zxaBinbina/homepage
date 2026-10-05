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
    expect(page.get_by_role('button', name='插旗', exact=True)).to_have_count(0)
    expect(page.get_by_role('button', name='翻开', exact=True)).to_have_count(0)
    expect(page.get_by_text('当前棋盘', exact=False)).to_have_count(0)
    page.locator('.mine-cell').nth(80).click(button='right')
    expect(page.locator('.mine-cell').nth(80)).to_have_attribute('aria-label', '第 9 行第 9 列：已插旗')
    expect(page.locator('.game-stats strong').first).to_have_text('9')
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
    for level, size, count in [('2', 16, 40), ('3', 20, 80), ('4', 30, 200)]:
        page.get_by_label('难度', exact=True).select_option(level)
        expect(page.locator('.mine-cell')).to_have_count(size * size)
        expect(page.locator('.game-stats strong').first).to_have_text(str(count))
    page.get_by_label('难度', exact=True).select_option('custom')
    custom_toggle = page.get_by_role('button', name='自定义设置', exact=True)
    expect(custom_toggle).to_have_attribute('aria-expanded', 'true')
    side = page.get_by_label('棋盘边长', exact=True)
    count = page.get_by_label('地雷数量', exact=True)
    apply = page.get_by_role('button', name='应用并开局', exact=True)
    for value in ['', '4', '129', '9.5']:
        side.fill(value)
        apply.click()
        expect(side).to_have_attribute('aria-invalid', 'true')
        expect(side).to_be_focused()
        expect(page.locator('.mine-cell')).to_have_count(900)
    side.fill('5')
    expect(count).to_have_attribute('max', '16')
    for value in ['', '0', '-1', '17', '1.5']:
        count.fill(value)
        apply.click()
        expect(count).to_have_attribute('aria-invalid', 'true')
        expect(count).to_be_focused()
        expect(page.locator('.mine-cell')).to_have_count(900)
    count.fill('16')
    count.press('Enter')
    expect(custom_toggle).to_have_attribute('aria-expanded', 'false')
    expect(custom_toggle).to_be_focused()
    expect(side).not_to_be_visible()
    expect(page.locator('.mine-cell')).to_have_count(25)
    page.locator('.mine-cell').nth(12).click()
    expect(page.locator('.game-status')).to_contain_text('恭喜过关')
    expect(page.locator('.mine-cell.is-open')).to_have_count(9)
    # Draft changes must not affect restart; only Apply replaces the active configuration.
    custom_toggle.click()
    side.fill('17')
    count.fill('53')
    custom_toggle.click()
    expect(side).not_to_be_visible()
    custom_toggle.press('Enter')
    expect(side).to_have_value('17')
    expect(count).to_have_value('53')
    page.get_by_role('button', name='重新开始', exact=True).click()
    expect(page.locator('.mine-cell')).to_have_count(25)
    expect(page.locator('.game-stats strong').first).to_have_text('16')
    apply.click()
    page.locator('.mine-cell').last.click(button='right')
    page.locator('.mine-cell').nth(144).click()
    expect(page.locator('.game-stats strong').nth(1)).not_to_have_text('0')
    # Editing the next board leaves the current flags, open cells and timer intact.
    custom_toggle.click()
    side.fill('128')
    count.fill('1')
    expect(page.locator('.mine-cell')).to_have_count(289)
    expect(page.locator('.mine-cell.is-flag')).to_have_count(1)
    expect(count).to_have_attribute('max', '16375')
    apply.click()
    expect(page.locator('.mine-cell')).to_have_count(16384)
    expect(page.locator('.mine-cell.is-flag, .mine-cell.is-open')).to_have_count(0)
    expect(page.locator('.game-stats strong').nth(1)).to_have_text('0')
    expect(page.get_by_role('button', name='翻开', exact=True)).to_have_count(0)
    page.locator('.mine-cell').first.focus()
    page.keyboard.press('ArrowDown')
    expect(page.locator('.mine-cell').nth(128)).to_be_focused()
    page.locator('.mine-cell').last.click(button='right')
    expect(page.locator('.mine-cell').last).to_have_attribute('aria-label', '第 128 行第 128 列：已插旗')
    assert page.locator('.mine-board-scroll').evaluate('el => el.scrollLeft > 0 && el.scrollTop > 0')
    custom_toggle.click()
    for theme in ['dark', 'light']:
        page.evaluate('theme => document.documentElement.dataset.theme = theme', theme)
        for width in [320, 390, 480, 481, 768, 1024, 1440]:
            page.set_viewport_size({'width': width, 'height': 1000})
            page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), ('custom board', theme, width)
            assert page.locator('.mine-board-scroll').evaluate('el => el.clientHeight <= innerHeight * .7 + 1')
            if width in [320, 390, 1440]:
                page.evaluate('window.scrollTo({top:0,behavior:"instant"})')
                page.screenshot(path=str(out / f'game-minesweeper-custom-{theme}-{width}.png'), full_page=True)
    page.get_by_role('button', name='重新开始', exact=True).click()
    assert page.locator('.mine-board-scroll').evaluate('el => el.scrollLeft === 0 && el.scrollTop === 0')
    # Large blank floods remain immediate even with motion enabled.
    page.emulate_media(reduced_motion='no-preference')
    page.locator('.mine-cell').nth(129).click()
    expect(page.locator('.mine-cell.is-open')).to_have_count(16383)
    expect(page.locator('.game-status')).to_contain_text('恭喜过关')
    assert page.locator('.mine-board').evaluate('el => el.getAnimations({subtree: true}).length') == 0
    page.emulate_media(reduced_motion='reduce')
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
                if path == '/games/solitaire':
                    sizes = page.locator('.solitaire-table .playing-card, .card-placeholder').evaluate_all('els => els.map(el => {const r=el.getBoundingClientRect(); return {width:r.width,height:r.height}})')
                    assert all(abs(size['height'] - size['width'] * 1.4) < 0.1 for size in sizes), (theme, width, 'Card proportions', sizes)
                    assert page.locator('.tableau-stack').evaluate_all('''stacks => stacks.every(stack => {
                        const cards = Array.from(stack.querySelectorAll('.tableau-card'));
                        return cards.every(card => card.getBoundingClientRect().bottom <= stack.getBoundingClientRect().bottom + 1);
                    })'''), (theme, width, 'Tableau stack must contain its last card')
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
    phone.get_by_label('难度', exact=True).select_option('custom')
    phone.get_by_label('棋盘边长', exact=True).fill('128')
    phone.get_by_label('地雷数量', exact=True).fill('500')
    phone.get_by_role('button', name='应用并开局', exact=True).tap()
    expect(phone.locator('.mine-cell')).to_have_count(16384)
    phone.get_by_role('button', name='插旗', exact=True).tap()
    phone.locator('.mine-cell').first.tap()
    expect(phone.locator('.game-stats strong').first).to_have_text('499')
    phone.locator('.mine-board-scroll').scroll_into_view_if_needed()
    box = phone.locator('.mine-board-scroll').bounding_box()
    start = {'x': box['x'] + 180, 'y': box['y'] + 180}
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [start]})
    for distance in [30, 60, 90, 120]:
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': start['x'] - distance, 'y': start['y'] - distance}]})
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
    phone.wait_for_function('document.querySelector(".mine-board-scroll").scrollLeft > 0 && document.querySelector(".mine-board-scroll").scrollTop > 0')
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
