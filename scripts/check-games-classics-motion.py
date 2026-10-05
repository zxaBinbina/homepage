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
    expect(page.get_by_text('30 行挑战完成！漂亮的一局。', exact=True)).to_have_count(1)
    expect(page.locator('.tetris-curtain')).to_have_count(0)
    expect(page.locator('.tetris-board')).to_have_attribute('aria-busy', 'false')
    expect(page.get_by_role('button', name='直接落下')).to_be_disabled()
    page.locator('.game-surface').screenshot(path=str(out / 'game-classics-tetris-win.png'))

    page.evaluate('''() => {
      const s = document.querySelector('.tetris-surface').__vueParentComponent.setupState;
      s.restart(); s.game.status = 'lost';
    }''')
    expect(page.get_by_text('方块堆到顶了，再来一局吧。', exact=True)).to_have_count(1)
    expect(page.locator('.tetris-curtain')).to_have_count(0)
    page.locator('.game-surface').screenshot(path=str(out / 'game-classics-tetris-lost.png'))

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
    # Both strategy games keep all results centered over the board, including fullscreen.
    page.emulate_media(reduced_motion='reduce')
    for game in ['xiangqi', 'gomoku']:
        visit(game)
        for result, message in [('win', '你赢了！这一局走得漂亮。'), ('loss', '电脑赢了，再试试另一种走法吧。'), ('draw', '和棋')]:
            page.evaluate('''([kind, result]) => {
              const s = document.querySelector('.strategy-surface').__vueParentComponent.setupState;
              s.restart();
              if (kind === 'xiangqi') {
                if (result === 'draw') s.quiet = 120;
                else s.board[result === 'win' ? 4 : 85] = 0;
              } else {
                s.board = result === 'draw'
                  ? Array.from({length:225}, (_,i) => (i%15 + 2*Math.floor(i/15))%4 < 2 ? 1 : -1)
                  : Array(225).fill(0);
                if (result !== 'draw') for (let i=90;i<95;i++) s.board[i] = result === 'win' ? 1 : -1;
                s.last = {from:-1,to:result === 'draw' ? 224 : 94};
              }
            }''', [game, result])
            expect(page.locator('.strategy-result')).to_contain_text(message)
            expect(page.locator('.strategy-result')).to_have_attribute('role', 'status')
            expect(page.locator('.game-toolbar .game-status')).to_have_count(0)
            expect(page.locator('.strategy-cell[tabindex="0"]')).to_have_count(0)
            for theme in ['dark', 'light']:
                page.evaluate('(t) => document.documentElement.dataset.theme = t', theme)
                for width in [320, 390, 768, 1024, 1440]:
                    page.set_viewport_size({'width':width, 'height':1000})
                    page.evaluate('() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))')
                    assert page.locator('.strategy-board').evaluate('''board => {
                      const b=board.getBoundingClientRect(), m=board.querySelector('.strategy-result').getBoundingClientRect(), t=board.querySelector('.strategy-result-message').getBoundingClientRect();
                      return Math.abs(m.x+m.width/2-b.x-b.width/2)<1 && Math.abs(m.y+m.height/2-b.y-b.height/2)<1
                        && Math.abs(t.y+t.height/2-b.y-b.height/2)<1 && t.width<=m.width && t.height<=m.height;
                    }'''), (game, result, theme, width)
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                    if result == 'loss' and width in [390, 1440]:
                        page.locator('.strategy-surface').screenshot(path=str(out / f'game-classics-{game}-result-{theme}-{width}.png'))
            if result == 'draw':
                page.get_by_role('button', name='网页全屏', exact=True).click()
                page.set_viewport_size({'width':844,'height':390})
                page.evaluate('() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))')
                expect(page.locator('dialog .strategy-result')).to_contain_text('和棋')
                assert page.locator('.strategy-result').evaluate('el => { const b=el.getBoundingClientRect(); return b.x>=0 && b.y>=0 && b.right<=innerWidth && b.bottom<=innerHeight; }')
                page.keyboard.press('Escape')
            page.get_by_role('button', name='重新开始').click()
            expect(page.locator('.strategy-result')).to_have_count(0)
        # A real move supplies the undo snapshot; undo must also remove a terminal overlay.
        page.set_viewport_size({'width':1440,'height':1000})
        if game == 'xiangqi':
            page.locator('.board-cell').nth(54).click()
            page.locator('.board-cell').nth(45).click()
        else:
            page.locator('.board-cell').nth(112).click()
            page.get_by_role('button', name='确认落子').click()
        expect(page.locator('.strategy-turn')).to_have_text('轮到你了')
        page.evaluate('''kind => {
          const s=document.querySelector('.strategy-surface').__vueParentComponent.setupState;
          if(kind==='xiangqi') s.board[85]=0;
          else { for(let i=90;i<95;i++) s.board[i]=-1; s.last={from:-1,to:94}; }
        }''', game)
        expect(page.locator('.strategy-result')).to_be_visible()
        page.get_by_role('button', name='悔棋', exact=True).click()
        expect(page.locator('.strategy-result')).to_have_count(0)
        expect(page.locator('.strategy-cell[tabindex="0"]')).to_have_count(1)
    assert not errors, errors
    browser.close()
print('Classics motion: clear/move durations, locks, cancellation, reduced-motion changes, fullscreen moves, win/loss/undo and unmount passed.')
