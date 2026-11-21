"""Doudizhu table, complete rounds, pointer selection, palettes and fullscreen regression."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from browser_theme import set_theme_mode, wait_theme_settled

expect.set_options(timeout=15000)
base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:4173').rstrip('/')
out = Path('artifacts/doudizhu')
out.mkdir(parents=True, exist_ok=True)


def open_table(context):
    page = context.new_page()
    page.set_default_timeout(10000)
    page.goto(base + '/games/doudizhu', wait_until='networkidle')
    expect(page.locator('.dd-card')).to_have_count(17)
    return page


def deal(page):
    page.get_by_role('button', name='叫 3 分', exact=True).click()
    expect(page.locator('.dd-card')).to_have_count(20)
    expect(page.get_by_role('button', name='提示', exact=True)).to_be_enabled()


def hand_ids(page):
    return page.locator('.dd-card').evaluate_all('els => els.map(el => el.dataset.cardId)')


def sweep_points(page, first=4, last=7):
    page.locator('.dd-hand').scroll_into_view_if_needed()
    boxes = [page.locator('.dd-card').nth(i).bounding_box() for i in (first, last)]
    return [(box['x'] + 6, box['y'] + 36) for box in boxes]


def mouse_sweep(page, release=True):
    start, end = sweep_points(page)
    page.mouse.move(*start)
    page.mouse.down()
    page.mouse.move(*end, steps=12)
    if release:
        page.mouse.up()


def assert_fit(page, fullscreen=False):
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Page overflow'
    assert page.locator('.dd-hand, .dd-hand-row').evaluate_all(
        'els => els.every(el => el.scrollWidth <= el.clientWidth + 1)'
    ), ('All cards must fit without horizontal scrolling', page.locator('.dd-hand, .dd-hand-row').evaluate_all('els => els.map(el => [el.className, el.clientWidth, el.scrollWidth])'))
    assert page.locator('.dd-card .playing-card').evaluate_all('''els => els.every(el => {
        const card = el.getBoundingClientRect();
        const area = el.closest('.dd-hand').getBoundingClientRect();
        return card.left >= area.left - 1 && card.right <= area.right + 1
            && Math.abs(card.height - card.width * 1.4) < 1;
    })'''), 'Clipped cards or incorrect proportions'
    if fullscreen:
        assert page.locator('.doudizhu-surface .game-button, .dd-card .playing-card').evaluate_all(
            '''els => els.every(el => {const r = el.getBoundingClientRect();
            return r.left >= -1 && r.top >= -1 && r.right <= innerWidth + 1 && r.bottom <= innerHeight + 1;})'''
        ), 'Fullscreen must show every card and control'
    else:
        assert page.locator('.doudizhu-surface .game-button').evaluate_all(
            'els => els.every(el => el.getBoundingClientRect().width >= 44 && el.getBoundingClientRect().height >= 44)'
        ), 'Action touch targets'
        tops = page.locator('.dd-actions .game-button').evaluate_all(
            'els => els.map(el => el.getBoundingClientRect().top)'
        )
        assert max(tops) - min(tops) < 1, 'Keep all four actions on one row'


with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'),
        args=['--no-sandbox'],
    )
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
    context.add_init_script("Math.random = () => 0; try { localStorage.setItem('homepage-theme', 'dark') } catch {}")
    errors = []
    context.on('page', lambda page: page.on('pageerror', lambda error: errors.append(str(error))))
    page = open_table(context)
    expect(page.locator('.dd-bottom .playing-card-face')).to_have_count(0)
    expect(page.locator('.dd-card:enabled')).to_have_count(0)
    deal(page)
    expect(page.locator('.dd-bottom .playing-card-face')).to_have_count(3)
    assert page.locator('.dd-card .is-red').count() > 0
    colors = page.locator('.dd-card .playing-card').evaluate_all(
        'els => [...new Set(els.map(el => getComputedStyle(el).color))]'
    )
    assert len(colors) == 2, 'Red and black suits must be distinct'
    assert_fit(page)

    # One Tab entry, native Space selection, local arrows and Escape.
    page.locator('.dd-card[tabindex="0"]').focus()
    page.keyboard.press('ArrowRight')
    expect(page.locator('.dd-card').nth(1)).to_be_focused()
    page.keyboard.press('Space')
    expect(page.locator('.dd-card[aria-pressed="true"]')).to_have_count(1)
    page.keyboard.press('End')
    expect(page.locator('.dd-card').last).to_be_focused()
    page.keyboard.press('Home')
    expect(page.locator('.dd-card').first).to_be_focused()
    page.keyboard.press('Escape')
    expect(page.locator('.dd-card[aria-pressed="true"]')).to_have_count(0)
    page.locator('.header .brand').focus()
    page.keyboard.press('ArrowRight')
    expect(page.locator('.dd-card[aria-pressed="true"]')).to_have_count(0)

    # Select a four-of-a-kind through actual mouse input; sweeping it again clears it.
    mouse_sweep(page)
    expect(page.locator('.dd-card[aria-pressed="true"]')).to_have_count(4)
    expect(page.locator('.dd-selection')).to_contain_text('炸弹')
    mouse_sweep(page)
    expect(page.locator('.dd-card[aria-pressed="true"]')).to_have_count(0)
    mouse_sweep(page, release=False)
    expect(page.locator('.dd-card[aria-pressed="true"]')).to_have_count(4)
    page.locator('.dd-hand').dispatch_event('pointercancel', {'pointerId': 1})
    page.mouse.up()
    expect(page.locator('.dd-card[aria-pressed="true"]')).to_have_count(0)
    mouse_sweep(page)
    page.get_by_role('button', name='出牌', exact=True).click()
    expect(page.locator('.dd-card')).to_have_count(16)
    expect(page.locator('.dd-trick-0 .dd-play-card')).to_have_count(4)
    expect(page.locator('.dd-multiplier')).to_contain_text('×2')
    expect(page.locator('.dd-card:enabled')).to_have_count(0)
    expect(page.get_by_role('button', name='提示', exact=True)).to_be_enabled()

    # Teleport keeps the same table and hand, including across portrait/landscape changes.
    original = hand_ids(page)
    page.evaluate('window.savedTable = document.querySelector(".doudizhu-surface")')
    page.get_by_role('button', name='网页全屏', exact=True).click()
    assert page.evaluate('window.savedTable === document.querySelector(".doudizhu-surface")')
    for width, height in [(1440, 1000), (320, 640), (844, 390)]:
        page.set_viewport_size({'width': width, 'height': height})
        page.wait_for_function('''() => !document.querySelector('.dd-hand-leave-active, .dd-hand-enter-active, .dd-hand-move')''')
        page.wait_for_timeout(100)
        assert_fit(page, fullscreen=True)
        assert hand_ids(page) == original
    page.get_by_role('button', name='退出全屏', exact=True).click()
    expect(page.get_by_role('button', name='网页全屏', exact=True)).to_be_focused()
    page.set_viewport_size({'width': 1440, 'height': 1000})

    # Play a full legal match through the public Hint / Play / Pass controls.
    for turn in range(80):
        if page.locator('.game-result').count():
            break
        expect(page.get_by_role('button', name='提示', exact=True)).to_be_enabled()
        page.get_by_role('button', name='提示', exact=True).click()
        action = '出牌' if page.get_by_role('button', name='出牌', exact=True).is_enabled() else '不出'
        page.get_by_role('button', name=action, exact=True).click()
        page.wait_for_function('''() => document.querySelector('.game-result') ||
            ![...document.querySelectorAll('.dd-actions button')].find(el => el.textContent.includes('提示'))?.disabled''')
    expect(page.locator('.game-result')).to_be_visible()
    page.locator('.doudizhu-surface').screenshot(path=str(out / 'finished.png'))
    page.get_by_role('button', name='再来一局', exact=True).click()
    expect(page.locator('.dd-card')).to_have_count(17)
    expect(page.locator('.dd-play-card')).to_have_count(0)
    page.get_by_role('button', name='不叫', exact=True).click()
    page.get_by_role('button', name='重新发牌', exact=True).click()
    page.wait_for_timeout(750)
    expect(page.locator('.dd-round-heading')).to_contain_text('你叫分')
    page.get_by_role('link', name='全部游戏', exact=True).click()
    expect(page.locator('.doudizhu-surface')).to_have_count(0)
    assert not errors, errors
    context.close()
    print('Match, mouse, cancellation, keyboard, restart and fullscreen passed', flush=True)

    # The previous scrollable hand fails this viewport matrix with 20 cards.
    for palette in ['fufu-blue', 'hutao-red']:
        for theme in ['dark', 'light']:
            context = browser.new_context(reduced_motion='reduce', viewport={'width': 1440, 'height': 1000})
            context.add_init_script(f"Math.random=()=>0; try {{ localStorage.setItem('homepage-theme','{theme}'); localStorage.setItem('homepage-palette','{palette}') }} catch {{}}")
            page = open_table(context)
            deal(page)
            for width in [1440, 1100, 760, 600, 375, 320]:
                page.set_viewport_size({'width': width, 'height': 1000})
                page.wait_for_timeout(60)
                assert_fit(page)
                if width > 600:
                    left, table, right = [page.locator(selector).bounding_box() for selector in ['.dd-seat-left', '.dd-table', '.dd-seat-right']]
                    assert left['x'] + left['width'] <= table['x'] + 1
                    assert table['x'] + table['width'] <= right['x'] + 1
                if width in [1440, 320]:
                    page.locator('.doudizhu-surface').screenshot(path=str(out / f'{palette}-{theme}-{width}.png'))
            context.close()
    print('Four palettes/themes across six viewport widths passed', flush=True)

    # Real touch input, vertical native scrolling and cancellation on orientation changes.
    context = browser.new_context(viewport={'width': 375, 'height': 900}, has_touch=True, is_mobile=True, reduced_motion='reduce')
    context.add_init_script('Math.random=()=>0')
    page = open_table(context)
    deal(page)
    expect(page.locator('.dd-hand-row')).to_have_count(2)
    cdp = context.new_cdp_session(page)
    start, end = sweep_points(page)
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': start[0], 'y': start[1]}]})
    for step in range(1, 9):
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': start[0] + (end[0] - start[0]) * step / 8, 'y': start[1]}]})
        page.wait_for_timeout(20)
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
    page.wait_for_timeout(100)
    expect(page.locator('.dd-card[aria-pressed="true"]')).to_have_count(4)
    page.get_by_role('button', name='重选', exact=True).tap()
    expect(page.locator('.dd-card[aria-pressed="true"]')).to_have_count(0)
    start, end = sweep_points(page)
    scroll = page.evaluate('scrollY')
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': start[0], 'y': start[1]}]})
    for step in range(1, 7):
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': start[0], 'y': start[1] - step * 10}]})
        page.wait_for_timeout(20)
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
    expect(page.locator('.dd-card[aria-pressed="true"]')).to_have_count(0)
    page.wait_for_function('start => scrollY !== start', arg=scroll)
    context.close()
    print('Touch range selection and native scrolling passed', flush=True)

    context = browser.new_context(reduced_motion='reduce')
    context.add_init_script('let ddSeed=3; Math.random=()=>{ddSeed=(Math.imul(ddSeed,1664525)+1013904223)>>>0;return ddSeed/2**32}')
    page = open_table(context)
    page.get_by_role('button', name='不叫', exact=True).click()
    expect(page.locator('.game-result')).to_contain_text('都不叫')
    expect(page.locator('.dd-card:enabled')).to_have_count(0)
    page.get_by_role('button', name='再来一局', exact=True).click()
    expect(page.get_by_role('button', name='叫 3 分', exact=True)).to_be_enabled()
    context.close()

    context = browser.new_context(viewport={'width': 1440, 'height': 1000})
    context.add_init_script("Math.random=()=>0;try { if (!localStorage.getItem('homepage-theme')) localStorage.setItem('homepage-theme','dark') } catch {}")
    page = open_table(context)
    deal(page)
    page.wait_for_timeout(350)
    page.locator('.dd-card').nth(2).click()
    page.wait_for_timeout(60)
    value = page.locator('.dd-card.is-selected .playing-card').evaluate('el => parseFloat(getComputedStyle(el).translate.split(" ")[1])')
    assert -16 < value < 0, ('Selection transition', value)
    page.wait_for_timeout(200)
    before = hand_ids(page)
    page.get_by_role('button', name='主题设置', exact=True).click()
    page.get_by_role('group', name='配色方案').get_by_role('button', name='胡桃红', exact=True).click()
    page.keyboard.press('Escape')
    wait_theme_settled(page)
    set_theme_mode(page, 'light')
    assert page.evaluate('''() => {
        const probe = document.createElement('span');
        probe.style.color = 'var(--primary-action)';
        document.body.append(probe);
        const expected = getComputedStyle(probe).color;
        probe.remove();
        return getComputedStyle(document.querySelector('.dd-primary')).backgroundColor === expected;
    }'''), 'Primary button must follow the live palette'
    assert hand_ids(page) == before, 'Theme changes must preserve the deal'
    page.reload(wait_until='networkidle')
    expect(page.locator('html')).to_have_attribute('data-palette', 'hutao-red')
    expect(page.locator('html')).to_have_attribute('data-theme', 'light')
    set_theme_mode(page, 'auto')
    for theme in ['dark', 'light']:
        page.emulate_media(color_scheme=theme)
        expect(page.locator('html')).to_have_attribute('data-theme', theme)
        expect(page.locator('html')).to_have_attribute('data-palette', 'hutao-red')
    context.close()
    browser.close()
    print('All-pass deal, motion and live theme switching passed', flush=True)
