"""Development fixtures: animation locks, cancellation, outcomes and reduced motion."""
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
    page.goto(base + '/games/popstar', wait_until='networkidle')
    expect(page.locator('.popstar-board')).to_be_visible()
    page.evaluate('''() => {
      window.arcadeAnimations = [];
      const animate = Element.prototype.animate;
      Element.prototype.animate = function(...args) {
        const a = animate.apply(this, args);
        if (this.closest('.popstar-board') && !this.classList.contains('game-result')) {
          a.pause(); arcadeAnimations.push(a);
        }
        return a;
      };
    }''')

    def fixture(ending=False, level=1):
        page.evaluate('''({ending, level}) => {
          const s = document.querySelector('.popstar-surface').__vueParentComponent.setupState;
          s.restart(); s.game.board = Array(100).fill(null); s.game.level = level;
          const tiles = ending ? [[90,0],[91,0]] : [[70,1],[80,0],[90,0],[82,2],[92,2]];
          for(const [i,color] of tiles) s.game.board[i] = {id:i, color};
          window.arcadeAnimations = [];
        }''', {'ending': ending, 'level': level})

    def choose():
        page.locator('.star-cell[data-index="90"]').click()
        page.locator('.star-cell[data-index="90"]').click()
        expect(page.locator('.popstar-surface')).to_have_attribute('aria-busy', 'true')
        page.wait_for_function('arcadeAnimations.length >= 2')

    fixture()
    choose()
    assert page.evaluate('arcadeAnimations.every(a => a.effect.getTiming().duration === 180)')
    page.locator('.star-cell[data-index="82"]').dispatch_event('click')
    expect(page.locator('.star-cell.is-selected')).to_have_count(2)
    expect(page.get_by_role('button', name='消除 2 颗 · +20')).to_be_disabled()
    page.get_by_role('button', name='重新开始', exact=True).click()
    expect(page.locator('.star-cell')).to_have_count(100)
    expect(page.locator('.popstar-surface')).to_have_attribute('aria-busy', 'false')
    expect(page.locator('.game-stats strong').nth(1)).to_have_text('0')
    fixture()
    page.get_by_role('button', name='网页全屏', exact=True).click()
    page.set_viewport_size({'width': 844, 'height': 390})
    choose()
    page.evaluate('arcadeAnimations.forEach(a => a.finish())')
    page.wait_for_function('arcadeAnimations.some(a => a.effect.getTiming().duration === 240)')
    assert page.evaluate('arcadeAnimations.filter(a => a.effect.getTiming().duration === 240).some(a => a.effect.getKeyframes()[0].transform !== a.effect.getKeyframes()[1].transform)')
    expect(page.locator('.popstar-surface')).to_have_attribute('aria-busy', 'true')
    page.emulate_media(reduced_motion='reduce')
    expect(page.locator('.popstar-surface')).to_have_attribute('aria-busy', 'false')
    expect(page.locator('.star-cell[data-id="70"]')).to_have_attribute('data-index', '90')
    expect(page.locator('.star-cell[data-id="82"]')).to_have_attribute('data-index', '81')
    page.keyboard.press('Escape')
    expect(page.locator('.game-fullscreen-dialog')).not_to_be_visible()
    page.set_viewport_size({'width': 1440, 'height': 1000})
    page.emulate_media(reduced_motion='no-preference')
    fixture(ending=True)
    choose()
    expect(page.locator('.game-result')).to_have_count(0)
    page.emulate_media(reduced_motion='reduce')
    expect(page.locator('.game-result')).to_contain_text('第 1 关完成')
    expect(page.locator('.game-stats strong').nth(1)).to_have_text('2020')
    page.locator('.game-surface').screenshot(path=str(out / 'game-arcade-popstar-win.png'))
    fixture(ending=True, level=2)
    page.locator('.star-cell[data-index="90"]').click()
    page.locator('.star-cell[data-index="90"]').click()
    expect(page.locator('.game-result')).to_contain_text('还差一点')
    page.locator('.game-surface').screenshot(path=str(out / 'game-arcade-popstar-lost.png'))
    page.emulate_media(reduced_motion='no-preference')
    fixture()
    choose()
    # Leaving mid-animation must not commit into a subsequent game instance.
    page.locator('.tool-back').click()
    expect(page.locator('.games-grid')).to_be_visible()
    page.locator('.game-card[href="/games/popstar"]').click()
    expect(page.locator('.star-cell')).to_have_count(100)
    expect(page.locator('.game-stats strong').nth(1)).to_have_text('0')

    page.goto(base + '/games/snake', wait_until='networkidle')
    expect(page.locator('.snake-board')).to_be_visible()
    page.evaluate('''() => {
      const s = document.querySelector('.snake-surface').__vueParentComponent.setupState;
      s.game.food = {x:6,y:9};
    }''')
    page.get_by_label('起始速度').select_option('0')
    page.evaluate('document.querySelector(".snake-surface").__vueParentComponent.setupState.game.food = {x:6,y:9}')
    page.get_by_role('button', name='开始游戏', exact=True).click()
    expect(page.locator('.game-stats strong').first).to_have_text('10')
    assert page.locator('.snake-segment').first.evaluate('e => getComputedStyle(e).transitionDuration !== "0s"')
    page.emulate_media(reduced_motion='reduce')
    page.wait_for_function('getComputedStyle(document.querySelector(".snake-segment")).transitionProperty === "none"')
    page.locator('.game-surface').screenshot(path=str(out / 'game-arcade-snake-playing.png'))
    page.get_by_role('button', name='暂停', exact=True).click()
    page.get_by_role('button', name='重新开始', exact=True).click()
    page.evaluate('''() => {
      const s = document.querySelector('.snake-surface').__vueParentComponent.setupState;
      s.game.body = [{x:17,y:9},{x:16,y:9},{x:15,y:9}];
    }''')
    page.get_by_role('button', name='开始游戏', exact=True).click()
    expect(page.locator('.game-result')).to_contain_text('撞到了')
    page.locator('.game-surface').screenshot(path=str(out / 'game-arcade-snake-lost.png'))
    page.evaluate('''() => {
      const s = document.querySelector('.snake-surface').__vueParentComponent.setupState;
      s.restart(); s.game.body = [{x:16,y:0}];
      for(let y=0;y<18;y++) for(let x=0;x<18;x++) if(!(y===0 && x>=16)) s.game.body.push({x,y});
      s.game.food = {x:17,y:0};
    }''')
    page.get_by_role('button', name='开始游戏', exact=True).click()
    expect(page.locator('.game-result')).to_contain_text('填满整个棋盘')
    expect(page.locator('.snake-segment')).to_have_count(324)
    assert not errors, errors
    browser.close()
print('Arcade motion passed: pop/fall durations, input lock, restart/unmount cancellation, scaled fullscreen, terminal states, snake transition and reduced motion.')
