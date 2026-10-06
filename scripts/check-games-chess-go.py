"""Public interactions and production-compatible checks for the two local opponents."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:5173').rstrip('/')
out = Path('artifacts')
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    errors = []
    context = browser.new_context(viewport={'width':1440,'height':1000}, reduced_motion='reduce')
    page = context.new_page()
    page.on('pageerror', lambda e: errors.append(str(e)))

    def visit(kind):
        page.goto(base + '/games/' + kind, wait_until='networkidle')
        expect(page.locator('.' + kind + '-board')).to_be_visible()

    def ready():
        expect(page.locator('.strategy-turn')).to_have_text('轮到你了', timeout=12000)
        expect(page.locator('.strategy-surface')).to_have_attribute('aria-busy','false')

    def chess_move(start, end):
        page.locator(f'[data-square="{start}"]').click()
        page.locator(f'[data-square="{end}"]').click()

    page.goto(base + '/game', wait_until='networkidle')
    expect(page.locator('.game-card')).to_have_count(13)
    for kind, title in [('chess','国际象棋单机版'),('go','围棋')]:
        page.locator(f'.game-card[href="/games/{kind}"]').click()
        expect(page.locator('.game-page-intro h1, .game-intro h1, h1').first).to_contain_text(title)
        expect(page).to_have_title(title + ' · 小游戏 · a彬彬a')
        page.reload(wait_until='networkidle')
        expect(page.locator('.' + kind + '-board')).to_be_visible()
        page.goto(base + '/game', wait_until='networkidle')

    for kind in ['chess','go']:
        visit(kind)
        expect(page.locator('.board-cell[tabindex="0"]')).to_have_count(1)
        page.locator('.board-cell[tabindex="0"]').focus()
        page.keyboard.press('ArrowLeft')
        expect(page.locator('.board-cell').nth(51 if kind == 'chess' else 39)).to_be_focused()
        page.keyboard.press('Enter')
        expect(page.locator('.is-selected')).to_have_count(1)
        page.keyboard.press('Escape')
        expect(page.locator('.is-selected')).to_have_count(0)
        for difficulty in ['0','1']:
            page.get_by_label('电脑难度').select_option(difficulty)
            if kind == 'chess':
                page.locator('[data-square="e2"]').click()
                expect(page.locator('[data-square="e4"]')).to_have_class('board-cell strategy-cell chess-cell is-target')
                page.locator('[data-square="e5"]').click()
                expect(page.locator('.chess-piece-art')).to_have_count(32)
                page.locator('[data-square="e4"]').click()
            else:
                page.locator('.board-cell').nth(40).click()
                expect(page.locator('.is-preview')).to_have_count(1)
                page.get_by_role('button', name='确认落子', exact=True).click()
            ready()
            if kind == 'chess':
                expect(page.locator('[data-square="e4"]')).to_contain_text('')
                expect(page.locator('[data-square="e4"] .chess-piece-art')).to_have_count(1)
                expect(page.locator('.game-stats strong').nth(1)).to_have_text('1')
            else:
                expect(page.locator('.strategy-piece')).to_have_count(2)
            page.get_by_role('button',name='悔棋',exact=True).click()
            ready()
            expect(page.locator('.strategy-piece')).to_have_count(32 if kind=='chess' else 0)
            expect(page.get_by_role('button',name='悔棋',exact=True)).to_be_disabled()
        page.get_by_role('button',name='机器先手',exact=True).click()
        ready()
        expect(page.get_by_role('button',name='机器先手',exact=True)).to_have_attribute('aria-pressed','true')
        expect(page.get_by_role('button',name='悔棋',exact=True)).to_be_disabled()
        before = page.locator('.board-cell').evaluate_all('els=>els.map(e=>e.getAttribute("aria-label"))')
        if kind == 'chess': chess_move('e7','e5')
        else:
            page.locator('.board-cell').nth(0).click()
            expect(page.locator('.is-preview.is-white')).to_have_count(1)
            page.get_by_role('button',name='确认落子',exact=True).click()
        ready()
        page.get_by_role('button',name='悔棋',exact=True).click()
        assert page.locator('.board-cell').evaluate_all('els=>els.map(e=>e.getAttribute("aria-label"))') == before
        page.get_by_role('button',name='重新开始',exact=True).click()
        ready()
        expect(page.get_by_role('button',name='机器先手',exact=True)).to_have_attribute('aria-pressed','true')
        page.get_by_role('button',name='机器先手',exact=True).click()

        # A loaded production page must keep playing with an inline worker while offline.
        if ':4173' in base:
            context.set_offline(True)
            if kind == 'chess': chess_move('e2','e4')
            else:
                page.locator('.board-cell').nth(40).click()
                page.get_by_role('button',name='确认落子',exact=True).click()
            ready()
            page.get_by_role('button',name='悔棋',exact=True).click()
            page.get_by_role('button',name='重新开始',exact=True).click()
            context.set_offline(False)

    visit('go')
    page.get_by_role('button',name='停一手',exact=True).click()
    expect(page.locator('.go-scoring')).to_be_visible(timeout=12000)
    page.get_by_role('button',name='继续对局',exact=True).click()
    ready()
    expect(page.locator('.go-scoring')).to_have_count(0)
    page.get_by_role('button',name='停一手',exact=True).click()
    expect(page.locator('.go-scoring')).to_be_visible(timeout=12000)
    page.get_by_role('button',name='确认数子',exact=True).click()
    expect(page.locator('.game-result')).to_contain_text('白棋胜 6.5 点')
    page.get_by_role('button',name='悔棋',exact=True).click()
    expect(page.locator('.game-result')).to_have_count(0)
    ready()

    for kind in ['chess','go']:
        visit(kind)
        for theme in ['dark','light']:
            page.evaluate('(theme)=>document.documentElement.dataset.theme=theme',theme)
            for width in [320,390,480,481,760,768,1024,1051,1440]:
                page.set_viewport_size({'width':width,'height':1000})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(kind,theme,width)
                board = page.locator('.' + kind + '-board').bounding_box()
                assert abs(board['width']-board['height']) < 1,(kind,board)
                if width in [320,390,768,1024,1440]:
                    page.locator('.game-surface').screenshot(path=str(out/f'game-chess-go-{kind}-{theme}-{width}.png'))
        if kind == 'chess': chess_move('e2','e4')
        else:
            page.locator('.board-cell').nth(40).click()
            page.get_by_role('button',name='确认落子',exact=True).click()
        ready()
        before = page.locator('.board-cell').evaluate_all('els=>els.map(e=>e.getAttribute("aria-label"))')
        page.get_by_role('button',name='网页全屏',exact=True).click()
        for width,height in [(320,740),(390,844),(844,390),(1440,900)]:
            page.set_viewport_size({'width':width,'height':height})
            page.wait_for_function('''()=>{ const r=document.querySelector('.game-surface').getBoundingClientRect(); return r.left>=-.5 && r.top>=-.5 && r.right<=innerWidth+.5 && r.bottom<=innerHeight+.5 }''')
            assert page.locator('.board-cell').evaluate_all('els=>els.map(e=>e.getAttribute("aria-label"))') == before
            if width in [390,844]: page.screenshot(path=str(out/f'game-chess-go-{kind}-fullscreen-{width}.png'))
        page.keyboard.press('Escape')
        expect(page.get_by_role('button',name='网页全屏',exact=True)).to_be_focused()
    context.close()
    touch = browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,reduced_motion='reduce')
    page = touch.new_page()
    page.on('pageerror', lambda e: errors.append(str(e)))
    for kind in ['chess','go']:
        visit(kind)
        page.get_by_role('button',name='网页全屏',exact=True).tap()
        if kind == 'chess':
            page.locator('[data-square="e2"]').tap()
            page.locator('[data-square="e4"]').tap()
        else:
            page.locator('.board-cell').nth(40).tap()
            expect(page.locator('.is-preview')).to_have_count(1)
            page.get_by_role('button',name='确认落子',exact=True).tap()
        ready()
        page.get_by_role('button',name='悔棋',exact=True).tap()
        expect(page.locator('.strategy-piece')).to_have_count(32 if kind=='chess' else 0)
    touch.close()
    browser.close()
    assert not errors,errors
print('Chess / Go browser passed: routes, keyboard/touch, both AI levels and sides, undo, passes/scoring, themes, 9 widths, fullscreen and focus. Fresh screenshots: artifacts/game-chess-go-*.png')
