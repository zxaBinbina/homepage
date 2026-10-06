"""Development-only fixtures for slide / jump motion and interrupted work."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:5173').rstrip('/')
out = Path('artifacts')
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    page = browser.new_page(viewport={'width':1440, 'height':1000}, reduced_motion='no-preference')
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))

    def visit(game):
        page.goto(base + '/games/' + game, wait_until='networkidle')
        expect(page.locator('.game-surface')).to_be_visible()
        page.evaluate('''() => {
          window.newAnimations = [];
          const animate = Element.prototype.animate;
          Element.prototype.animate = function(...args) {
            const a = animate.apply(this,args);
            if (this.matches('.sliding-tile, .jump-actor, .jump-figure') || this.parentElement?.matches('.jump-stage > svg')) {
              a.pause(); newAnimations.push(a);
            }
            return a;
          };
        }''')

    def sliding_fixture():
        page.evaluate('''() => {
          const s = document.querySelector('.sliding-surface').__vueParentComponent.setupState;
          s.restart(); s.game = {size:4, board:[1,2,3,4,5,6,7,8,9,10,11,12,13,14,0,15], moves:0};
          newAnimations = [];
        }''')

    def jump_fixture():
        page.evaluate('''() => {
          const s = document.querySelector('.jump-surface').__vueParentComponent.setupState;
          s.restart(); s.phase = 'charging'; newAnimations = []; s.jump(630);
        }''')

    visit('huarongdao')
    sliding_fixture()
    page.locator('[data-tile="15"]').click()
    expect(page.locator('.sliding-surface')).to_have_attribute('aria-busy', 'true')
    assert page.evaluate('newAnimations.length === 1 && newAnimations[0].effect.getTiming().duration === 200')
    page.locator('[data-tile="14"]').dispatch_event('click')
    expect(page.locator('.game-stats strong').first).to_have_text('0')
    expect(page.locator('.game-result')).to_have_count(0)
    page.get_by_role('button', name='撤销', exact=True).click()
    expect(page.locator('.sliding-surface')).to_have_attribute('aria-busy', 'false')
    expect(page.locator('[data-tile="15"]')).to_have_attribute('data-index','15')
    page.locator('[data-tile="15"]').click()
    page.emulate_media(reduced_motion='reduce')
    expect(page.locator('.game-result')).to_contain_text('全部归位')
    page.locator('.game-surface').screenshot(path=str(out / 'game-new-huarongdao-win.png'))
    page.get_by_role('button', name='撤销', exact=True).click()
    expect(page.locator('.game-result')).to_have_count(0)
    page.emulate_media(reduced_motion='no-preference')
    page.wait_for_function('!document.querySelector(".game-surface").__vueParentComponent.setupState.motion.reduced.value')
    page.locator('[data-tile="15"]').click()
    page.get_by_role('button', name='重新开始', exact=True).click()
    expect(page.locator('.sliding-surface')).to_have_attribute('aria-busy', 'false')
    expect(page.locator('.game-stats strong').first).to_have_text('0')
    page.get_by_role('button', name='网页全屏', exact=True).click()
    page.set_viewport_size({'width':844,'height':390})
    page.wait_for_function('document.querySelector(".game-fullscreen-dialog").getAnimations().length === 0 && getComputedStyle(document.querySelector(".game-fullscreen-dialog")).opacity === "1"')
    sliding_fixture()
    page.locator('[data-tile="15"]').click()
    frames = page.evaluate('newAnimations[0].effect.getKeyframes().map(f => f.transform)')
    assert frames[0] != frames[-1]
    page.emulate_media(reduced_motion='reduce')
    expect(page.locator('.game-result')).to_contain_text('全部归位')
    page.keyboard.press('Escape')
    expect(page.locator('.game-fullscreen-dialog')).not_to_be_visible()

    page.set_viewport_size({'width':1440,'height':1000})
    page.emulate_media(reduced_motion='no-preference')
    page.wait_for_function('!document.querySelector(".game-surface").__vueParentComponent.setupState.motion.reduced.value')
    visit('jump')
    jump_fixture()
    expect(page.locator('.jump-surface')).to_have_attribute('aria-busy','true')
    assert page.evaluate('newAnimations[0].effect.getTiming().duration === 480')
    frames = page.evaluate('newAnimations[0].effect.getKeyframes().map(f => new DOMMatrix(f.transform)).map(m => [m.e,m.f])')
    assert frames[0] == [140,272] and frames[-1] == [350,272] and frames[4][1] < 180, frames
    page.locator('.jump-stage').focus()
    page.keyboard.press('Space')
    assert page.evaluate('newAnimations.length === 1'), 'No second jump while in flight'
    page.get_by_role('button', name='重新开始', exact=True).click()
    expect(page.locator('.jump-surface')).to_have_attribute('aria-busy','false')
    expect(page.locator('.game-stats strong').first).to_have_text('0')
    page.get_by_role('button', name='网页全屏', exact=True).click()
    page.set_viewport_size({'width':844,'height':390})
    page.wait_for_function('document.querySelector(".game-fullscreen-dialog").getAnimations().length === 0 && getComputedStyle(document.querySelector(".game-fullscreen-dialog")).opacity === "1"')
    jump_fixture()
    page.evaluate('newAnimations[0].currentTime = 240')
    page.screenshot(path=str(out / 'game-new-jump-midair-fullscreen.png'))
    page.evaluate('newAnimations[0].finish()')
    page.wait_for_function('newAnimations.some(a => a.effect.getTiming().duration === 280)')
    expect(page.locator('.jump-surface')).to_have_attribute('aria-busy','true')
    expect(page.locator('.game-stats strong').first).to_have_text('1')
    page.emulate_media(reduced_motion='reduce')
    expect(page.locator('.jump-surface')).to_have_attribute('aria-busy','false')
    assert page.locator('.jump-actor').evaluate('el => Math.abs(el.getBoundingClientRect().x - el.closest("svg").getBoundingClientRect().x) < el.closest("svg").getBoundingClientRect().width / 2'), 'Camera follows landing'
    page.keyboard.press('Escape')
    page.set_viewport_size({'width':320,'height':740})
    page.emulate_media(reduced_motion='no-preference')
    page.wait_for_function('!document.querySelector(".game-surface").__vueParentComponent.setupState.motion.reduced.value')
    page.evaluate('''() => {
      const s = document.querySelector('.jump-surface').__vueParentComponent.setupState;
      s.restart(); s.phase='charging'; newAnimations=[]; s.jump(300);
    }''')
    expect(page.locator('.game-result')).to_have_count(0)
    assert page.evaluate('newAnimations[0].effect.getTiming().duration === 650')
    page.emulate_media(reduced_motion='reduce')
    expect(page.locator('.game-result')).to_contain_text('本局 0 分')
    page.locator('.game-surface').screenshot(path=str(out / 'game-new-jump-lost-320.png'))
    assert page.locator('.game-result').evaluate('e => e.scrollHeight <= e.clientHeight'), 'Result fits narrow scene'
    page.emulate_media(reduced_motion='no-preference')
    page.wait_for_function('!document.querySelector(".game-surface").__vueParentComponent.setupState.motion.reduced.value')
    jump_fixture()
    page.locator('.tool-back').click()
    expect(page.locator('.game-card')).to_have_count(11)
    page.locator('.game-card[href="/games/jump"]').click()
    expect(page.locator('.jump-surface')).to_have_attribute('aria-busy','false')
    expect(page.locator('.game-stats strong').first).to_have_text('0')
    assert not errors, errors
    browser.close()
print('Sliding / jump motion passed: slide/arc/fall/camera, input locks, undo/restart/unmount cancellation, scaled fullscreen and reduced motion.')
