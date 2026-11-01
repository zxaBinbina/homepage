"""Check visible color interpolation, interruption and the RDP desktop's four palettes."""
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright, expect
from browser_theme import set_theme_mode, wait_theme_settled

BASE = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:4173').rstrip('/')
OUT = Path(__file__).resolve().parent.parent / 'artifacts/theme-motion'
OUT.mkdir(parents=True, exist_ok=True)
errors = []
samples = {}


def sample(page, button, selectors):
    return page.evaluate('''async ({button, selectors}) => {
        const root = document.documentElement, frames = [], start = performance.now();
        const targets = Object.fromEntries(Object.entries(selectors).map(([key, [selector, property, pseudo]]) =>
            [key, [document.querySelector(selector), property, pseudo]]));
        const record = () => frames.push({time: performance.now()-start,
            ...Object.fromEntries(Object.entries(targets).map(([key, [el, property, pseudo]]) =>
                [key, getComputedStyle(el, pseudo)[property]]))});
        record(); document.querySelector(button).click();
        const duration = root.getAnimations().find(a => a.id === 'theme-colors')?.effect.getTiming().duration;
        while (performance.now()-start < 1400) { await new Promise(requestAnimationFrame); record(); }
        return {duration, frames};
    }''', {'button': button, 'selectors': selectors})


def assert_progress(result, keys):
    assert 900 <= result['duration'] <= 1200, result['duration']
    frames = result['frames']
    middle = min(frames, key=lambda frame: abs(frame['time'] - 500))
    for key in keys:
        assert frames[0][key] != frames[-1][key], (key, 'no change')
        assert middle[key] not in (frames[0][key], frames[-1][key]), (key, 'snapped', middle)
        assert len({frame[key] for frame in frames}) >= 6, (key, 'missing intermediate colors')


with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    context = browser.new_context(color_scheme='dark', viewport={'width': 1440, 'height': 900})
    page = context.new_page()
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(BASE, wait_until='networkidle')
    assert page.locator('html').evaluate('el => !el.getAnimations().some(a => a.id === "theme-colors")')
    set_theme_mode(page, 'dark')
    selectors = {
        'canvas': ['html', 'backgroundColor'], 'background': ['body', 'backgroundColor'],
        'text': ['body', 'color'], 'header': ['.app-header-transition', 'backgroundColor'],
        'border': ['.app-header-transition', 'borderBottomColor'], 'gradient': ['h1 span', 'backgroundImage'],
    }
    samples['dark-light'] = sample(page, '.theme-toggle', selectors)
    assert_progress(samples['dark-light'], ['canvas', 'background', 'text', 'header', 'border'])
    assert samples['dark-light']['frames'][-1]['background'] == 'rgb(244, 246, 250)'
    page.get_by_role('button', name='选择配色方案', exact=True).click()
    samples['blue-red'] = sample(page, '.palette-option:last-of-type', selectors)
    assert_progress(samples['blue-red'], list(selectors))
    expect(page.locator('.palette-popover')).to_be_visible()
    print('One-second background/text/border/gradient interpolation and persistent popup passed', flush=True)

    # Reverse an unfinished transition in the same event turn: the visible color must not jump.
    page.get_by_role('button', name='芙芙蓝', exact=True).click()
    page.wait_for_timeout(350)
    before, after = page.evaluate('''() => {
        const before = getComputedStyle(document.body).backgroundColor;
        document.querySelector('.palette-option:last-of-type').click();
        return [before, getComputedStyle(document.body).backgroundColor];
    }''')
    assert before == after, (before, after)
    wait_theme_settled(page)
    expect(page.locator('body')).to_have_css('background-color', 'rgb(252, 240, 225)')
    assert page.evaluate('localStorage.getItem("homepage-palette")') == 'hutao-red'
    page.get_by_role('button', name='胡桃红', exact=True).click()
    assert page.locator('html').evaluate('el => !el.getAnimations().some(a => a.id === "theme-colors")')
    page.keyboard.press('Escape')

    # Automatic OS updates use the same transition, including when interrupted by reduced motion.
    set_theme_mode(page, 'auto')
    page.emulate_media(color_scheme='light')
    page.wait_for_function('document.documentElement.getAnimations().some(a => a.id === "theme-colors")')
    page.emulate_media(reduced_motion='reduce')
    wait_theme_settled(page)
    expect(page.locator('body')).to_have_css('background-color', 'rgb(252, 240, 225)')
    set_theme_mode(page, 'dark')
    expect(page.locator('body')).to_have_css('background-color', 'rgb(58, 27, 25)')
    page.emulate_media(reduced_motion='no-preference')
    page.locator('.theme-toggle').click()
    page.wait_for_timeout(200)
    page.evaluate('''() => {
        Object.defineProperty(document, 'hidden', {configurable: true, value: true});
        document.dispatchEvent(new Event('visibilitychange'));
    }''')
    wait_theme_settled(page)
    expect(page.locator('body')).to_have_css('background-color', 'rgb(252, 240, 225)')
    page.evaluate('''() => { delete document.hidden; document.dispatchEvent(new Event('visibilitychange')); }''')
    print('Continuous reversal, same-option selection, automatic mode and motion/background cleanup passed', flush=True)

    page.goto(BASE + '/projects/rdp-access-auth', wait_until='networkidle')
    page.locator('.exposure-demo').scroll_into_view_if_needed()
    page.emulate_media(reduced_motion='reduce')
    rdp_colors = {}
    for mode in ['dark', 'light']:
        set_theme_mode(page, mode)
        for palette, name in [('fufu-blue', '芙芙蓝'), ('hutao-red', '胡桃红')]:
            page.get_by_role('button', name='选择配色方案', exact=True).click()
            page.get_by_role('button', name=name, exact=True).click()
            page.keyboard.press('Escape')
            rdp_colors[f'{palette}-{mode}'] = page.evaluate('''() => Object.fromEntries([
                ['sky', '.exposure-wallpaper', 'backgroundImage'],
                ['taskbar', '.exposure-taskbar', 'backgroundColor'],
                ['notice', '.exposure-notice', 'backgroundColor'],
                ['icon', '.exposure-notice-icon', 'backgroundImage'],
            ].map(([key, selector, property]) => [key, getComputedStyle(document.querySelector(selector))[property]]))''')
            for width in [320, 390, 768, 1024, 1440]:
                page.set_viewport_size({'width': width, 'height': 1000})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                assert page.locator('.exposure-demo').evaluate('''demo => {
                    const bounds = demo.getBoundingClientRect();
                    return [...demo.querySelectorAll('.exposure-desktop,.exposure-notice,.exposure-taskbar')]
                        .every(el => { const box = el.getBoundingClientRect();
                            return box.left >= bounds.left && box.right <= bounds.right;
                        });
                }'''), ('clipped desktop content', palette, mode, width)
                if width in [390, 1440]:
                    page.locator('.exposure-demo').screenshot(path=str(OUT / f'rdp-{palette}-{mode}-{width}.png'))
    for mode in ['dark', 'light']:
        for key in ['sky', 'taskbar', 'notice', 'icon']:
            assert rdp_colors[f'fufu-blue-{mode}'][key] != rdp_colors[f'hutao-red-{mode}'][key], (mode, key)
    for palette in ['fufu-blue', 'hutao-red']:
        for key in ['sky', 'taskbar', 'notice']:
            assert rdp_colors[f'{palette}-dark'][key] != rdp_colors[f'{palette}-light'][key], (palette, key)
    page.emulate_media(reduced_motion='no-preference')
    page.get_by_role('button', name='选择配色方案', exact=True).click()
    samples['rdp-red-blue'] = sample(page, '.palette-option:first-of-type', {
        'sky': ['.exposure-wallpaper', 'backgroundImage'],
        'mountains': ['.exposure-wallpaper', 'backgroundImage', '::before'],
        'taskbar': ['.exposure-taskbar', 'backgroundColor'],
        'notice': ['.exposure-notice', 'backgroundColor'],
        'icon': ['.exposure-notice-icon', 'backgroundImage'],
    })
    assert_progress(samples['rdp-red-blue'], ['sky', 'mountains', 'taskbar', 'notice', 'icon'])
    print('RDP wallpaper, mountains, notifications, taskbar and accents: four themes and 320–1440px passed', flush=True)
    context.close()

    for feature in ['registerProperty', 'animate']:
        fallback = browser.new_context(color_scheme='dark')
        fallback.add_init_script(
            "CSS.registerProperty = undefined" if feature == 'registerProperty'
            else "Element.prototype.animate = undefined")
        view = fallback.new_page()
        view.on('pageerror', lambda error: errors.append(str(error)))
        view.goto(BASE, wait_until='networkidle')
        set_theme_mode(view, 'light')
        expect(view.locator('body')).to_have_css('background-color', 'rgb(244, 246, 250)')
        fallback.close()
    print('Browsers without optional animation APIs remain usable; no JavaScript errors', flush=True)
    assert not errors, errors
    (OUT / 'frames.json').write_text(json.dumps(samples, indent=2) + '\n')
    browser.close()
