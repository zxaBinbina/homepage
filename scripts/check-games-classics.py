"""Four new classics: real interactions, workers, offline play, fit, touch and motion."""
import os
import re
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:5173').rstrip('/')
out = Path('artifacts')
out.mkdir(exist_ok=True)
routes = {'tetris': '.tetris-board', 'sudoku': '.sudoku-board', 'xiangqi': '.xiangqi-board', 'gomoku': '.gomoku-board'}

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
    context.add_init_script('Math.random = () => 0')
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))

    def visit(game):
        page.goto(base + '/games/' + game, wait_until='networkidle')
        expect(page.locator(routes[game])).to_be_visible()

    def idle():
        expect(page.locator('.strategy-surface')).to_have_attribute('aria-busy', 'false')
        expect(page.locator('.strategy-turn')).to_have_text('轮到你了')

    visit('tetris')
    before = page.locator('.tetris-board').inner_html()
    page.wait_for_timeout(1100)
    assert before == page.locator('.tetris-board').inner_html(), 'No auto start'
    page.get_by_role('button', name='开始游戏', exact=True).click()
    page.locator('.tetris-board').press('ArrowLeft')
    page.locator('.tetris-board').press('ArrowUp')
    page.locator('.tetris-board').press('Space')
    assert page.locator('.tetris-cell.is-fixed').count() == 4
    page.locator('.tetris-board').press('p')
    expect(page.get_by_role('button', name='继续游戏')).to_be_visible()
    before = page.locator('.tetris-board').inner_html()
    page.wait_for_timeout(1100)
    assert before == page.locator('.tetris-board').inner_html()
    page.get_by_role('button', name='继续游戏').click()
    page.evaluate('window.dispatchEvent(new Event("blur"))')
    expect(page.get_by_role('button', name='继续游戏')).to_be_visible()
    page.get_by_role('button', name='重新开始').click()
    expect(page.locator('.tetris-cell.is-fixed')).to_have_count(0)
    page.get_by_label('起始速度').select_option('2')
    expect(page.get_by_role('button', name='开始游戏', exact=True)).to_be_visible()
    page.locator('.header .brand').focus()
    page.keyboard.press('ArrowDown')
    expect(page.locator('.game-stats strong').first).to_have_text('0')

    visit('sudoku')
    blank = page.locator('.sudoku-cell:not(.is-given)').first
    given = page.locator('.sudoku-cell.is-given').first
    fixed = given.inner_text()
    given.click()
    page.keyboard.press('1')
    assert given.inner_text() == fixed
    blank.click()
    page.get_by_role('button', name='笔记', exact=True).click()
    page.get_by_role('button', name='填写 3', exact=True).click()
    expect(blank).to_contain_text('3')
    page.get_by_role('button', name='笔记', exact=True).click()
    page.get_by_role('button', name='填写 8', exact=True).click()
    expect(blank.locator('.sudoku-value')).to_have_text('8')
    page.get_by_role('button', name='撤销', exact=True).click()
    expect(blank.locator('.sudoku-notes')).to_contain_text('3')
    page.get_by_role('button', name='提示一格').click()
    expect(page.locator('.game-stats strong').nth(1)).to_have_text('1')
    expect(page.get_by_role('button', name='检查', exact=True)).to_have_count(0)
    expect(page.locator('.game-status')).not_to_be_visible()
    # Duplicate clues stay visibly marked without a redundant status message.
    page.get_by_role('button', name='填写 3', exact=True).click()
    expect(blank).to_have_class(re.compile(r'.*is-conflict.*'))
    expect(page.locator('.game-status')).not_to_be_visible()
    expect(page.get_by_text('有数字在行、列或宫内重复，请检查标记的格子。')).to_have_count(0)
    page.get_by_role('button', name='撤销', exact=True).click()
    page.locator('.sudoku-cell').first.focus()
    page.keyboard.press('ArrowRight')
    expect(page.locator('.sudoku-cell').nth(1)).to_be_focused()
    for level, count in [('1', 36), ('2', 21), ('0', 44)]:
        page.get_by_label('题目难度').select_option(level)
        expect(page.locator('.sudoku-cell.is-given')).to_have_count(count)
    for _ in range(37):
        page.get_by_role('button', name='提示一格').click()
    expect(page.locator('.game-status')).to_contain_text('全部填对')
    page.get_by_role('button', name='撤销', exact=True).click()
    expect(page.locator('.game-status')).not_to_be_visible()

    for game in ['gomoku', 'xiangqi']:
        visit(game)
        # Escape must cancel a selection without breaking component compilation.
        page.locator('.board-cell').nth(54 if game == 'xiangqi' else 112).click()
        expect(page.locator('.strategy-cell.is-selected')).to_have_count(1)
        page.keyboard.press('Escape')
        expect(page.locator('.strategy-cell.is-selected')).to_have_count(0)
        context.set_offline(True)
        if game == 'gomoku':
            page.locator('.board-cell').nth(112).click()
            expect(page.locator('.strategy-piece.is-preview')).to_have_count(1)
            page.get_by_role('button', name='确认落子').click()
        else:
            page.locator('.board-cell').nth(54).click()
            expect(page.locator('.board-cell').nth(45)).to_have_class('board-cell strategy-cell is-target')
            page.locator('.board-cell').nth(45).click()
        idle()
        expect(page.locator('.game-stats strong').nth(1)).to_have_text('1')
        if game == 'gomoku':
            expect(page.locator('.strategy-piece.is-white')).to_have_count(1)
        else:
            assert page.locator('.strategy-piece').count() in [31, 32], 'A cannon may capture on its opening turn'
        # The worker has loaded. Play another complete turn with the network disabled.
        context.set_offline(True)
        if game == 'gomoku':
            page.locator('.board-cell').nth(0).click()
            page.get_by_role('button', name='确认落子').click()
        else:
            page.locator('.board-cell').nth(56).click()
            page.locator('.board-cell').nth(47).click()
        idle()
        context.set_offline(False)
        page.get_by_role('button', name='悔棋', exact=True).click()
        expect(page.locator('.game-stats strong').nth(1)).to_have_text('1')
        page.get_by_role('button', name='悔棋', exact=True).click()
        expect(page.locator('.game-stats strong').nth(1)).to_have_text('0')
        page.get_by_label('电脑难度').select_option('1')
        if game == 'gomoku':
            page.locator('.board-cell').nth(112).dblclick()
        else:
            page.locator('.board-cell').nth(54).click()
            page.locator('.board-cell').nth(45).click()
        page.get_by_role('button', name='重新开始').click()
        page.wait_for_timeout(1100)
        expect(page.locator('.game-stats strong').nth(1)).to_have_text('0')
        expect(page.locator('.strategy-piece')).to_have_count(32 if game == 'xiangqi' else 0)

    # Direct loading/refresh, tutorial order, themes, all prescribed widths + breakpoints.
    for game in routes:
        visit(game)
        page.reload(wait_until='networkidle')
        expect(page.locator(routes[game])).to_be_visible()
        expect(page.locator('.desktop-nav [aria-current="page"]')).to_have_text('游戏')
        for theme in ['dark', 'light']:
            page.evaluate('(t) => document.documentElement.dataset.theme = t', theme)
            for width in [320, 390, 480, 481, 760, 768, 1024, 1440]:
                page.set_viewport_size({'width': width, 'height': 1000})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (game, theme, width, 'overflow')
                assert page.locator('.game-guide').bounding_box()['y'] < page.locator('.game-surface').bounding_box()['y']
                if width in [390, 1440]:
                    page.locator('.game-surface').screenshot(path=str(out / f'game-classics-{game}-{theme}-{width}.png'))
        page.get_by_role('button', name='网页全屏', exact=True).click()
        for width, height in [(320, 568), (390, 844), (768, 1000), (1440, 900), (568, 320), (844, 390)]:
            page.set_viewport_size({'width': width, 'height': height})
            page.wait_for_timeout(200)
            page.wait_for_function('''size => { const r = document.querySelector('.game-surface').getBoundingClientRect(); return innerWidth === size[0] && innerHeight === size[1] && r.x >= -1 && r.y >= -1 && r.right <= innerWidth + 1 && r.bottom <= innerHeight + 1; }''', arg=[width, height])
            surface = page.locator('.game-surface').bounding_box()
            assert surface['x'] >= -1 and surface['y'] >= -1 and surface['x'] + surface['width'] <= width + 1 and surface['y'] + surface['height'] <= height + 1, (game, width, height, surface)
            expect(page.locator('dialog .game-guide')).not_to_be_visible()
            if width == 844:
                page.screenshot(path=str(out / f'game-classics-{game}-fullscreen.png'))
        page.keyboard.press('Escape')
        expect(page.get_by_role('button', name='网页全屏', exact=True)).to_be_focused()

    phone_context = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, reduced_motion='reduce')
    phone = phone_context.new_page()
    phone.on('pageerror', lambda e: errors.append(str(e)))
    phone.goto(base + '/games/tetris', wait_until='networkidle')
    phone.get_by_role('button', name='开始游戏', exact=True).tap()
    phone.get_by_role('button', name='向左移动').tap()
    phone.get_by_role('button', name='旋转方块').tap()
    phone.get_by_role('button', name='直接落下').tap()
    expect(phone.locator('.tetris-cell.is-fixed')).to_have_count(4)
    phone.goto(base + '/games/sudoku', wait_until='networkidle')
    phone.locator('.sudoku-cell:not(.is-given)').first.tap()
    phone.get_by_role('button', name='填写 3', exact=True).tap()
    phone.goto(base + '/games/gomoku', wait_until='networkidle')
    phone.get_by_role('button', name='网页全屏', exact=True).tap()
    phone.locator('.board-cell').nth(112).tap()
    phone.get_by_role('button', name='确认落子').tap()
    expect(phone.locator('.strategy-piece.is-white')).to_have_count(1)
    phone.goto(base + '/games/xiangqi', wait_until='networkidle')
    phone.locator('.board-cell').nth(54).tap()
    phone.locator('.board-cell').nth(45).tap()
    expect(phone.locator('.strategy-turn')).to_have_text('轮到你了')
    assert not errors, errors
    browser.close()
print('Four classics: interactions, worker cancellation, offline turns, keyboard/touch, theme/width matrix and fullscreen fit passed. Fresh screenshots: artifacts/game-classics-*.png')
