"""Check explicit/automatic themes and the persistent horizontal palette popup."""
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright, expect
from browser_theme import set_theme_mode, wait_theme_settled

BASE = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:4173').rstrip('/')
OUT = Path(__file__).resolve().parent.parent / 'artifacts/theme'
OUT.mkdir(parents=True, exist_ok=True)
COLORS = {
    ('fufu-blue', 'dark'): '#141521', ('fufu-blue', 'light'): '#f4f6fa',
    ('hutao-red', 'dark'): '#3a1b19', ('hutao-red', 'light'): '#fcf0e1',
}
errors = []
results = []


def assert_theme(page, mode, effective, palette='fufu-blue'):
    expect(page.locator('html')).to_have_attribute('data-theme-mode', mode)
    expect(page.locator('html')).to_have_attribute('data-theme', effective)
    expect(page.locator('html')).to_have_attribute('data-palette', palette)
    button = page.locator('.theme-toggle')
    expect(button).to_have_attribute('data-mode', mode)
    icon = {'dark': 'moon', 'light': 'sun', 'auto': 'monitor'}[mode]
    expect(button.locator(f'.lucide-{icon}-icon')).to_have_count(1)
    label = {'dark': '深色模式', 'light': '浅色模式', 'auto': '自动模式（跟随系统）'}[mode]
    assert button.get_attribute('aria-label').startswith('当前为' + label + '，')
    expect(page.locator('meta[name="theme-color"]')).to_have_attribute('content', COLORS[(palette, effective)])


def settled_popup(page):
    wait_theme_settled(page)
    expect(page.locator('.palette-popover')).to_be_visible()
    page.wait_for_function("!document.querySelector('.palette-popover').classList.contains('palette-popover-enter-active')")
    page.wait_for_function('''() => {
        const popup = document.querySelector('.palette-popover');
        const a = popup.querySelector('[aria-pressed=true]').getBoundingClientRect();
        const b = popup.querySelector('.seg__thumb').getBoundingClientRect();
        return ['x','y','width','height'].every(k => Math.abs(a[k]-b[k]) < 1);
    }''')


def popup_bounds(page, width):
    settled_popup(page)
    box = page.locator('.palette-popover').bounding_box()
    assert box['x'] >= 15 and box['x'] + box['width'] <= width - 15, (width, box)
    blue = page.get_by_role('button', name='芙芙蓝', exact=True).bounding_box()
    red = page.get_by_role('button', name='胡桃红', exact=True).bounding_box()
    assert abs(blue['y'] - red['y']) < 1 and red['x'] >= blue['x'] + blue['width'] - 1
    assert abs(blue['width'] - red['width']) < 1
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')


with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'),
        args=['--no-sandbox'],
    )
    context = browser.new_context(color_scheme='dark', viewport={'width': 1440, 'height': 900})
    page = context.new_page()
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(BASE, wait_until='networkidle')
    assert_theme(page, 'auto', 'dark')
    page.emulate_media(color_scheme='light')
    assert_theme(page, 'auto', 'light')
    page.locator('.theme-toggle').click()
    assert_theme(page, 'dark', 'dark')
    page.emulate_media(color_scheme='dark')
    page.emulate_media(color_scheme='light')
    assert_theme(page, 'dark', 'dark')
    page.locator('.theme-toggle').click()
    assert_theme(page, 'light', 'light')
    page.emulate_media(color_scheme='dark')
    assert_theme(page, 'light', 'light')
    page.locator('.theme-toggle').click()
    assert_theme(page, 'auto', 'dark')
    assert page.evaluate('localStorage.getItem("homepage-theme")') == 'auto'
    page.reload(wait_until='networkidle')
    assert_theme(page, 'auto', 'dark')
    page.emulate_media(color_scheme='light')
    assert_theme(page, 'auto', 'light')
    results.append('Three-mode cycle, current-mode icons, live OS updates and auto persistence passed')
    print(results[-1], flush=True)

    # Keep the same popup and focus during repeated selections; measure the actual moving thumb.
    trigger = page.get_by_role('button', name='选择配色方案', exact=True)
    trigger.click()
    settled_popup(page)
    page.evaluate('window.palettePopup = document.querySelector(".palette-popover")')
    page.get_by_role('button', name='胡桃红', exact=True).click()
    expect(trigger).to_have_attribute('aria-expanded', 'true')
    expect(page.get_by_role('button', name='胡桃红', exact=True)).to_be_focused()
    assert page.evaluate('window.palettePopup === document.querySelector(".palette-popover")')
    assert_theme(page, 'auto', 'light', 'hutao-red')
    settled_popup(page)
    samples = page.evaluate('''async () => {
        const popup = document.querySelector('.palette-popover');
        const thumb = popup.querySelector('.seg__thumb'), values = [];
        values.push(thumb.getBoundingClientRect().x);
        popup.querySelector('button').click();
        const start = performance.now();
        while (performance.now() - start < 360) {
            await new Promise(requestAnimationFrame);
            values.push(thumb.getBoundingClientRect().x);
        }
        return values;
    }''')
    assert abs(samples[0] - samples[-1]) > 40
    assert any(samples[-1] + 2 < x < samples[0] - 2 for x in samples)
    assert page.evaluate('window.palettePopup === document.querySelector(".palette-popover")')
    page.get_by_role('button', name='芙芙蓝', exact=True).focus()
    page.keyboard.press('ArrowRight')
    expect(page.get_by_role('button', name='胡桃红', exact=True)).to_be_focused()
    expect(trigger).to_have_attribute('aria-expanded', 'true')
    page.keyboard.press('Escape')
    expect(page.locator('.palette-popover')).to_have_count(0)
    expect(trigger).to_be_focused()
    trigger.click()
    settled_popup(page)
    page.mouse.click(4, 500)
    expect(page.locator('.palette-popover')).to_have_count(0)
    trigger.click()
    settled_popup(page)
    trigger.click()
    expect(page.locator('.palette-popover')).to_have_count(0)
    trigger.click()
    settled_popup(page)
    page.locator('.theme-toggle').focus()
    page.keyboard.press('Enter')
    expect(page.locator('.palette-popover')).to_have_count(0)
    results.append('Horizontal animated selection, retained popup/focus, arrows, outside click, trigger and Escape passed')
    print(results[-1], flush=True)

    for mode in ['dark', 'light']:
        set_theme_mode(page, mode)
        trigger.click()
        for palette, name in [('fufu-blue', '芙芙蓝'), ('hutao-red', '胡桃红')]:
            page.get_by_role('button', name=name, exact=True).click()
            for width in [320, 390, 759, 761, 768, 1024, 1050, 1051, 1440]:
                page.set_viewport_size({'width': width, 'height': 900})
                popup_bounds(page, width)
                if width in [320, 1440]:
                    page.screenshot(path=str(OUT / f'{palette}-{mode}-{width}.png'))
            assert_theme(page, mode, mode, palette)
        page.keyboard.press('Escape')
    page.emulate_media(reduced_motion='reduce')
    trigger.click()
    page.get_by_role('button', name='芙芙蓝', exact=True).click()
    settled_popup(page)
    assert page.locator('.palette-popover .seg__thumb').evaluate(
        'el => getComputedStyle(el).transitionDuration.split(",").every(duration => parseFloat(duration) <= 0.001)')
    page.keyboard.press('Escape')
    expect(page.locator('.palette-popover')).to_have_count(0)
    results.append('Both palettes in dark/light, 320–1440px resizing and reduced motion passed')
    print(results[-1], flush=True)

    set_theme_mode(page, 'auto')
    for route in ['/tool', '/game', '/projects/rdp-access-auth', '/projects/gaze', '/']:
        # Exercise the same SPA navigation handler used by links, keeping shared state alive.
        page.evaluate('''path => {
            const link = document.createElement('a'); link.href = path;
            document.body.append(link); link.click(); link.remove();
        }''', route)
        page.wait_for_url(BASE + route)
        expect(page.locator('.theme-toggle')).to_have_count(1)
        page.emulate_media(color_scheme='dark')
        assert_theme(page, 'auto', 'dark')
        page.emulate_media(color_scheme='light')
        assert_theme(page, 'auto', 'light')
    context.close()
    results.append('Shared automatic mode across homepage, tools, games, RDP and Gaze passed')
    print(results[-1], flush=True)

    # Block application modules, then inspect the inline first-paint state before Vue can run.
    for saved, system, palette in [
        (None, 'dark', 'fufu-blue'), (None, 'light', 'fufu-blue'),
        ('dark', 'light', 'hutao-red'), ('light', 'dark', 'fufu-blue'),
        ('auto', 'light', 'hutao-red'), ('auto', 'dark', 'hutao-red'),
        ('invalid', 'light', 'fufu-blue'), ('blocked', 'light', 'fufu-blue'),
    ]:
        context = browser.new_context(color_scheme=system)
        if saved == 'blocked':
            context.add_init_script("Object.defineProperty(window, 'localStorage', {get() { throw new Error('storage blocked') }})")
        elif saved is not None:
            context.add_init_script(f'localStorage.setItem("homepage-theme", {json.dumps(saved)}); localStorage.setItem("homepage-palette", {json.dumps(palette)})')
        view = context.new_page()
        view.on('pageerror', lambda error: errors.append(str(error)))
        view.route('**/*.js', lambda route: route.abort())
        view.goto(BASE, wait_until='load')
        mode = saved if saved in ('dark', 'light') else 'auto'
        effective = mode if mode != 'auto' else system
        expect(view.locator('html')).to_have_attribute('data-theme-mode', mode)
        expect(view.locator('html')).to_have_attribute('data-theme', effective)
        expect(view.locator('meta[name="theme-color"]')).to_have_attribute('content', COLORS[(palette, effective)])
        view.unroute('**/*.js')
        view.reload(wait_until='networkidle')
        assert_theme(view, mode, effective, palette)
        if saved == 'blocked':
            set_theme_mode(view, 'dark')
            assert_theme(view, 'dark', 'dark')
            set_theme_mode(view, 'auto')
            assert_theme(view, 'auto', 'light')
        context.close()
    results.append('First-paint/runtime parity, old preferences, invalid preference and blocked storage passed')
    print(results[-1], flush=True)
    assert not errors, errors
    browser.close()
    (OUT / 'checks.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
