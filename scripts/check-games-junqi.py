"""Military table: real setup/moves, undo, keyboard, themes, scaling and canceled motion."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from browser_theme import set_theme_mode, wait_theme_settled

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:4173').rstrip('/')
out = Path('artifacts/junqi')
out.mkdir(parents=True, exist_ok=True)
expect.set_options(timeout=10000)


def army(page):
    return page.locator('.junqi-cell').evaluate_all('els => els.map(el => el.querySelector(".junqi-piece")?.dataset.pieceId ?? null)')


def open_game(context):
    page = context.new_page()
    page.set_default_timeout(10000)
    page.goto(base + '/games/junqi', wait_until='networkidle')
    expect(page.locator('.junqi-cell')).to_have_count(60)
    expect(page.locator('.junqi-cell .junqi-piece')).to_have_count(50)
    return page


def fit(page, fullscreen=False):
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Page overflow'
    assert page.locator('.junqi-piece').evaluate_all('''els => els.every(el => {
        const r=el.getBoundingClientRect(),b=el.closest('.junqi-board').getBoundingClientRect();
        return r.left >= b.left-1 && r.right <= b.right+1 && r.top >= b.top-1 && r.bottom <= b.bottom+1;
    })'''), ('A piece crossed the board bounds', page.viewport_size, page.locator('.junqi-board').get_attribute('class'))
    if fullscreen:
        assert page.locator('.junqi-cell, .junqi-toolbar .game-button').evaluate_all('''els => els.every(el => {
            const r=el.getBoundingClientRect(); return r.left>=-1 && r.top>=-1 && r.right<=innerWidth+1 && r.bottom<=innerHeight+1;
        })'''), 'Fullscreen must show all stations and controls'
    else:
        assert page.locator('.junqi-cell').evaluate_all('els => els.every(el => el.getBoundingClientRect().height >= 43 && el.getBoundingClientRect().width >= 44)'), 'Station touch targets'
    assert page.locator('.junqi-cell .junqi-piece').evaluate_all('''els => els.every(el => {
        const r=el.getBoundingClientRect(),t=el.querySelector('b').getBoundingClientRect();
        return t.left >= r.left-1 && t.right <= r.right+1 && t.top>=r.top-1 && t.bottom<=r.bottom+1;
    })'''), 'Piece labels must remain readable'


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    context = browser.new_context(viewport={'width':1440,'height':1100}, reduced_motion='reduce')
    context.add_init_script('Math.random=()=>0')
    errors=[]
    context.on('page',lambda page:page.on('pageerror',lambda e:errors.append(str(e))))
    page=open_game(context)
    expect(page.locator('.junqi-piece b').filter(has_text='炸弹')).to_have_count(4)
    expect(page.locator('.junqi-piece b').filter(has_text='工兵')).to_have_count(6)
    original=army(page)
    page.locator('[data-at="30"]').click()
    expect(page.locator('.junqi-cell.is-target')).not_to_have_count(0)
    page.locator('[data-at="31"]').click()
    swapped=army(page)
    assert swapped[30]==original[31] and swapped[31]==original[30]
    page.locator('[data-at="30"]').click()
    page.locator('[data-at="31"]').click()
    assert army(page)==original
    flag=page.locator('.junqi-cell[aria-label*="我方军旗"]').first
    flag.click()
    page.locator('[data-at="30"]').click()
    assert army(page)==original, 'Illegal flag setup must be rejected'
    expect(page.locator('.junqi-command h2')).to_have_text('军旗')
    page.get_by_role('button', name='取消选择', exact=True).click()
    page.get_by_role('button', name='开始对局', exact=True).click()
    expect(page.get_by_role('button', name='悔棋', exact=True)).to_be_disabled()
    page.locator('[data-at="30"]').focus()
    page.keyboard.press('ArrowRight')
    expect(page.locator('[data-at="31"]')).to_be_focused()
    page.keyboard.press('Space')
    expect(page.locator('[data-at="31"]')).to_have_attribute('aria-pressed','true')
    page.keyboard.press('Escape')
    expect(page.locator('.junqi-cell.is-selected')).to_have_count(0)
    page.locator('.header .brand').focus()
    page.keyboard.press('ArrowRight')
    expect(page.locator('.junqi-cell.is-selected')).to_have_count(0)

    # The initial commander can capture across the outer bridge.
    page.locator('[data-at="30"]').click()
    assert '可攻击' in page.locator('[data-at="25"]').get_attribute('aria-label')
    page.locator('[data-at="25"]').click()
    expect(page.locator('.junqi-cell .junqi-piece')).to_have_count(49)
    expect(page.locator('.junqi-piece.is-enemy')).to_have_count(24)
    expect(page.locator('.junqi-surface')).to_have_attribute('aria-busy','true')
    page.get_by_role('button', name='悔棋', exact=True).click()
    assert army(page)==original
    page.wait_for_timeout(650)
    assert army(page)==original, 'Undo must cancel the pending computer reply'
    page.locator('[data-at="30"]').click()
    page.locator('[data-at="25"]').click()
    expect(page.locator('.junqi-surface')).to_have_attribute('aria-busy','false')
    expect(page.locator('.junqi-recent li')).to_have_count(2)
    page.get_by_role('button', name='悔棋', exact=True).click()
    assert army(page)==original, 'Undo must restore both players as a whole turn'
    expect(page.locator('.junqi-recent')).to_have_count(0)
    expect(page.locator('.junqi-cell.is-last-to')).to_have_count(0)

    # One existing board is moved into fullscreen; orientation never resets the army.
    page.evaluate('window.savedBoard=document.querySelector(".junqi-board")')
    page.get_by_role('button', name='网页全屏', exact=True).click()
    for width,height in [(1440,1000),(320,640),(390,844),(568,320),(844,390),(768,1000)]:
        page.set_viewport_size({'width':width,'height':height})
        page.wait_for_function('''() => document.querySelector('.junqi-board').classList.contains('is-horizontal') === (innerWidth>=560 && innerHeight<=600)''')
        page.wait_for_timeout(100)
        fit(page,True)
        assert army(page)==original
        assert page.evaluate('window.savedBoard===document.querySelector(".junqi-board")')
        if width in [320,844]: page.screenshot(path=str(out/f'fullscreen-{width}.png'))
    page.get_by_role('button',name='退出全屏',exact=True).click()
    expect(page.get_by_role('button',name='网页全屏',exact=True)).to_be_focused()
    page.set_viewport_size({'width':1440,'height':1100})
    page.locator('[data-at="30"]').click()
    page.locator('[data-at="25"]').click()
    page.get_by_role('button',name='重新开始',exact=True).click()
    page.wait_for_timeout(650)
    assert army(page)==original
    expect(page.get_by_role('button',name='开始对局',exact=True)).to_be_enabled()
    page.get_by_role('button',name='开始对局',exact=True).click()
    page.locator('[data-at="30"]').click()
    page.locator('[data-at="25"]').click()
    page.get_by_role('link',name='全部游戏',exact=True).click()
    page.wait_for_timeout(650)
    expect(page.locator('.junqi-board')).to_have_count(0)
    assert not errors,errors
    context.close()
    print('Setup, real capture, whole-turn undo, stale replies, keyboard, fullscreen and navigation passed',flush=True)

    for palette in ['fufu-blue','hutao-red']:
        for theme in ['dark','light']:
            context=browser.new_context(viewport={'width':1440,'height':1100},reduced_motion='reduce')
            context.add_init_script(f"Math.random=()=>0;try {{localStorage.setItem('homepage-theme','{theme}');localStorage.setItem('homepage-palette','{palette}')}} catch {{}}")
            page=open_game(context)
            for width in [1440,1024,768,760,480,390,320]:
                page.set_viewport_size({'width':width,'height':1100})
                page.wait_for_timeout(50)
                fit(page)
                if width in [1440,320]:page.locator('.junqi-surface').screenshot(path=str(out/f'{palette}-{theme}-{width}.png'))
            colors=page.locator('.junqi-piece').evaluate_all('els=>[...new Set(els.map(el=>getComputedStyle(el).color))]')
            assert len(colors)==2,'Both armies must remain distinct in every palette/theme'
            context.close()
    print('Four palette/theme combinations and seven viewport widths passed',flush=True)

    context=browser.new_context(viewport={'width':390,'height':900},has_touch=True,is_mobile=True,reduced_motion='reduce')
    context.add_init_script('Math.random=()=>0')
    page=open_game(context)
    page.locator('[data-at="30"]').tap()
    expect(page.locator('[data-at="30"]')).to_have_attribute('aria-pressed','true')
    page.locator('[data-at="31"]').tap()
    expect(page.locator('.junqi-cell.is-selected')).to_have_count(0)
    page.get_by_role('button',name='开始对局',exact=True).tap()
    page.locator('[data-at="30"]').tap()
    expect(page.locator('.junqi-cell.is-target')).not_to_have_count(0)
    context.close()
    print('Touch setup and station selection passed',flush=True)

    context=browser.new_context(viewport={'width':1440,'height':1100},reduced_motion='no-preference')
    context.add_init_script("Math.random=()=>0;try {if(!localStorage.getItem('homepage-theme'))localStorage.setItem('homepage-theme','dark')} catch {}")
    page=open_game(context)
    page.get_by_role('button',name='开始对局',exact=True).click()
    original=army(page)
    page.evaluate('''() => {const animate=Element.prototype.animate;
        Element.prototype.animate=function(...args){const result=animate.apply(this,args);if(this.classList.contains('junqi-flight'))result.pause();return result}}''')
    page.locator('[data-at="30"]').click()
    source=page.locator('[data-at="30"]').bounding_box()
    page.locator('[data-at="25"]').click()
    expect(page.locator('.junqi-flight')).to_have_count(1)
    expect(page.locator('.junqi-surface')).to_have_attribute('aria-busy','true')
    ghost=page.locator('.junqi-flight').bounding_box()
    assert abs(ghost['x']+ghost['width']/2-source['x']-source['width']/2)<2
    assert abs(ghost['y']+ghost['height']/2-source['y']-source['height']/2)<2
    page.get_by_role('button',name='悔棋',exact=True).click()
    expect(page.locator('.junqi-flight')).to_have_count(0)
    assert army(page)==original
    page.get_by_role('button',name='网页全屏',exact=True).click()
    page.set_viewport_size({'width':844,'height':390})
    expect(page.locator('.junqi-board')).to_have_class('junqi-board is-horizontal')
    page.wait_for_timeout(100)
    page.locator('[data-at="30"]').click()
    source=page.locator('[data-at="30"]').bounding_box()
    page.locator('[data-at="25"]').click()
    expect(page.locator('.junqi-flight')).to_have_count(1)
    ghost=page.locator('.junqi-flight').bounding_box()
    assert abs(ghost['x']+ghost['width']/2-source['x']-source['width']/2)<2, 'Scaled flight origin'
    assert abs(ghost['y']+ghost['height']/2-source['y']-source['height']/2)<2, 'Scaled flight origin'
    page.get_by_role('button',name='悔棋',exact=True).click()
    assert army(page)==original
    page.get_by_role('button',name='退出全屏',exact=True).click()
    page.set_viewport_size({'width':1440,'height':1100})
    page.locator('[data-at="30"]').click()
    page.locator('[data-at="25"]').click()
    expect(page.locator('.junqi-flight')).to_have_count(1)
    page.emulate_media(reduced_motion='reduce')
    expect(page.locator('.junqi-flight')).to_have_count(0)
    expect(page.locator('.junqi-surface')).to_have_attribute('aria-busy','false')
    page.get_by_role('button',name='悔棋',exact=True).click()
    assert army(page)==original
    page.get_by_role('button',name='主题设置',exact=True).click()
    page.get_by_role('group',name='配色方案').get_by_role('button',name='胡桃红',exact=True).click()
    page.keyboard.press('Escape')
    wait_theme_settled(page)
    set_theme_mode(page,'light')
    assert army(page)==original
    page.reload(wait_until='networkidle')
    expect(page.locator('html')).to_have_attribute('data-theme','light')
    expect(page.locator('html')).to_have_attribute('data-palette','hutao-red')
    context.close()
    browser.close()
    print('Actual moving layer, cancellation, reduced motion and live theme persistence passed',flush=True)
