"""Development-only endgame fixtures exercise real commits; no test API ships."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:5173').rstrip('/')
out = Path('artifacts')
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1440, 'height': 1000}, reduced_motion='no-preference')
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))

    def visit(game):
        page.goto(base + '/games/' + game, wait_until='networkidle')
        expect(page.locator('.game-surface')).to_be_visible()

    def hold_motion():
        page.evaluate('''() => {
          window.classicAnimations = [];
          const animate = Element.prototype.animate;
          Element.prototype.animate = function(...args) {
            const a = animate.apply(this, args);
            if (this.closest('.tetris-board, .strategy-board')) { a.pause(); window.classicAnimations.push(a); }
            return a;
          };
        }''')

    def tetris_endgame():
        page.evaluate('''() => {
          const s = document.querySelector('.tetris-surface').__vueParentComponent.setupState;
          s.restart(); s.game.lines = 28;
          for (let i=180; i<200; i++) if (![4,5].includes(i%10)) s.game.board[i] = 1;
          s.game.active = { x:4, y:18, shape:[[1,1],[1,1]] };
          s.started = true;
        }''')

    visit('tetris')
    hold_motion()
    tetris_endgame()
    page.get_by_role('button', name='直接落下').click()
    expect(page.locator('.tetris-board')).to_have_attribute('aria-busy', 'true')
    expect(page.locator('.is-clearing')).to_have_count(20)
    assert page.evaluate('classicAnimations.every(a => a.effect.getTiming().duration === 180)')
    expect(page.get_by_role('button', name='向左移动')).to_be_disabled()
    page.get_by_role('button', name='重新开始').click()
    expect(page.locator('.tetris-board')).to_have_attribute('aria-busy', 'false')
    expect(page.locator('.tetris-cell.is-fixed')).to_have_count(0)
    expect(page.locator('.game-stats strong').nth(1)).to_contain_text('0')
    tetris_endgame()
    page.get_by_role('button', name='直接落下').click()
    expect(page.locator('.tetris-board')).to_have_attribute('aria-busy', 'true')
    page.emulate_media(reduced_motion='reduce')
    expect(page.locator('.game-status')).to_contain_text('挑战完成')
    expect(page.locator('.tetris-board')).to_have_attribute('aria-busy', 'false')
    expect(page.get_by_role('button', name='直接落下')).to_be_disabled()
    page.locator('.game-surface').screenshot(path=str(out / 'game-classics-tetris-win.png'))

    visit('xiangqi')
    page.emulate_media(reduced_motion='no-preference')
    hold_motion()
    page.get_by_role('button', name='网页全屏', exact=True).click()
    page.set_viewport_size({'width': 844, 'height': 390})
    page.locator('.board-cell').nth(54).click()
    page.locator('.board-cell').nth(45).click()
    expect(page.locator('.strategy-surface')).to_have_attribute('aria-busy', 'true')
    assert page.evaluate('classicAnimations.length === 1 && classicAnimations[0].effect.getTiming().duration === 240')
    frames = page.evaluate('classicAnimations[0].effect.getKeyframes().map(f => f.transform)')
    assert frames[0] != frames[1], frames
    page.get_by_role('button', name='悔棋', exact=True).click()
    expect(page.locator('.board-cell').nth(54)).to_contain_text('兵')
    expect(page.locator('.board-cell').nth(45)).to_have_text('')
    expect(page.locator('.strategy-surface')).to_have_attribute('aria-busy', 'false')
    page.locator('.board-cell').nth(54).click()
    page.locator('.board-cell').nth(45).click()
    page.emulate_media(reduced_motion='reduce')
    expect(page.locator('.strategy-turn')).to_have_text('轮到你了')
    page.get_by_role('button', name='悔棋', exact=True).click()
    expect(page.locator('.game-stats strong').nth(1)).to_have_text('0')

    visit('gomoku')
    page.set_viewport_size({'width': 1440, 'height': 1000})
    page.emulate_media(reduced_motion='no-preference')
    hold_motion()
    page.evaluate('''() => {
      const s = document.querySelector('.strategy-surface').__vueParentComponent.setupState;
      s.board = Array(225).fill(0); for(let i=0;i<4;i++) s.board[90+i]=1;
    }''')
    page.locator('.board-cell').nth(94).click()
    page.get_by_role('button', name='确认落子').click()
    expect(page.locator('.strategy-surface')).to_have_attribute('aria-busy', 'true')
    assert page.evaluate('classicAnimations[0].effect.getTiming().duration === 180')
    page.emulate_media(reduced_motion='reduce')
    expect(page.locator('.game-status')).to_contain_text('你赢了')
    expect(page.locator('.is-winning')).to_have_count(5)
    page.locator('.game-surface').screenshot(path=str(out / 'game-classics-gomoku-win.png'))
    page.get_by_role('button', name='悔棋', exact=True).click()
    expect(page.locator('.game-status')).not_to_be_visible()
    expect(page.locator('.strategy-piece')).to_have_count(4)
    page.get_by_role('button', name='重新开始').click()
    page.evaluate('''() => {
      const s = document.querySelector('.strategy-surface').__vueParentComponent.setupState;
      s.board = Array(225).fill(0); for(let i=0;i<4;i++) s.board[90+i]=-1;
    }''')
    page.locator('.board-cell').nth(112).click()
    page.get_by_role('button', name='确认落子').click()
    expect(page.locator('.game-status')).to_contain_text('电脑赢了')
    expect(page.locator('.is-winning')).to_have_count(5)
    # A queued reply must not survive route unmount.
    page.get_by_role('button', name='重新开始').click()
    page.locator('.board-cell').nth(112).click()
    page.get_by_role('button', name='确认落子').click()
    page.get_by_role('link', name='全部游戏', exact=True).click()
    expect(page.locator('.game-card')).to_have_count(7)
    page.wait_for_timeout(1000)
    assert not errors, errors
    browser.close()
print('Classics motion: clear/move durations, locks, cancellation, reduced-motion changes, fullscreen moves, win/loss/undo and unmount passed.')
