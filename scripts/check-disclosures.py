"""Exercise disclosure motion, document flow, reversals and keyboard state in a browser."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:5173').rstrip('/')
out = Path('artifacts/disclosures')
out.mkdir(parents=True, exist_ok=True)


def sample_toggle(page, button, panel, following):
    page.locator(button).first.focus()
    return page.evaluate('''async ({button, panel, following}) => {
        const region = document.querySelector(panel), next = document.querySelector(following);
        const samples = [], start = performance.now();
        function sample() {
            samples.push({time: performance.now() - start,
                height: region.getBoundingClientRect().height,
                next: next.getBoundingClientRect().top + scrollY});
        }
        sample(); document.querySelector(button).click();
        while (performance.now() - start < 430) {
            await new Promise(requestAnimationFrame); sample();
        }
        return samples;
    }''', {'button': button, 'panel': panel, 'following': following})


def assert_motion(samples, opening, label):
    first, last = samples[0], samples[-1]
    low, high = sorted([first['height'], last['height']])
    assert high - low > 20, (label, 'no height change', samples)
    assert len({round(s['height'], 1) for s in samples if low + 1 < s['height'] < high - 1}) >= 3, (label, 'no intermediate heights')
    assert (last['height'] > first['height']) == opening, label
    assert (last['next'] > first['next']) == opening, (label, 'following content did not move')
    # Both opening and closing must move the following content continuously, including gaps.
    delta = abs(last['next'] - first['next'])
    assert max(abs(b['next'] - a['next']) for a, b in zip(samples, samples[1:])) < delta * .65, (label, 'layout jumped')
    assert abs(last['height'] if not opening else first['height']) < 1, label


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1440, 'height': 1000}, reduced_motion='no-preference')
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    cases = [
        ('codex', '/tools/codex-jsonl-cleaner', 'button[aria-controls="codex-import-guide"]', '.codex-cleaner-panel > .collapse-panel', '.codex-cleaner-editor', 1440),
        ('advanced', '/tools/js-obfuscator', 'button[aria-controls="obfuscator-options"]', '.tool-page__body > .collapse-panel', '.tool-page__body > .split', 1440),
        ('find', '/tools/json-formatter', '.pane__foot button[aria-label="查找"]', '.pane > .collapse-panel', '.pane__body', 1440),
        ('mine', '/games/minesweeper', '.mine-custom-toggle', '.mine-custom > .collapse-panel', '.mine-stage', 1440),
        ('agent', '/projects/rdp-access-auth/wiki', '.wiki-agent summary', '.wiki-agent > .collapse-panel', '.wiki-section', 1440),
        ('rdp-directory', '/projects/rdp-access-auth/wiki', '.wiki-mobile-toc', '.rdp-toc > .collapse-panel', '.rdp-doc', 390),
        ('gaze-directory', '/projects/gaze/guide/installation', '.gaze-mobile-nav', '.gaze-sidebar > .collapse-panel', '.gaze-doc', 390),
    ]
    report = {}
    for name, path, button, panel, following, width in cases:
        page.set_viewport_size({'width': width, 'height': 1000})
        page.goto(base + path, wait_until='networkidle')
        if name == 'mine':
            page.locator('select[aria-labelledby="mine-level-label"]').select_option('custom')
            page.wait_for_timeout(400)
            page.locator(button).click()
        page.wait_for_timeout(450)
        opening = sample_toggle(page, button, panel, following)
        assert_motion(opening, True, name)
        closing = sample_toggle(page, button, panel, following)
        assert_motion(closing, False, name)
        assert abs(opening[0]['next'] - closing[-1]['next']) < 2, (name, 'spacing did not return')
        report[name] = {'open': opening, 'close': closing}
        # Reverse several times mid-flight. The last action must win, with no stale callbacks.
        page.evaluate('''async (button) => {
            const toggle = document.querySelector(button);
            for (let i = 0; i < 5; i++) { toggle.click(); await new Promise(r => setTimeout(r, 55)); }
        }''', button)
        page.wait_for_timeout(400)
        expect(page.locator(panel).first).to_have_class('collapse-panel is-open is-settled')
        assert page.locator(panel).first.evaluate('(el) => el.getBoundingClientRect().height') > 20
        page.locator(button).first.click()
        expect(page.locator(panel).first).to_have_attribute('inert', '')
        page.wait_for_timeout(400)
        assert page.locator(panel).first.evaluate('(el) => el.getBoundingClientRect().height') == 0
        # Changing reduced-motion during an expansion finishes immediately.
        page.locator(button).first.click()
        page.wait_for_timeout(40)
        page.emulate_media(reduced_motion='reduce')
        expect(page.locator(panel).first).to_have_class('collapse-panel is-open is-settled is-instant')
        page.locator(button).first.click()
        expect(page.locator(panel).first).to_have_class('collapse-panel is-settled is-instant')
        assert page.locator(panel).first.evaluate('(el) => el.getBoundingClientRect().height') == 0
        page.emulate_media(reduced_motion='no-preference')
        page.locator(button).first.click()
        page.wait_for_timeout(400)
        for theme in ['dark', 'light']:
            page.evaluate('(theme) => document.documentElement.dataset.theme = theme', theme)
            for check_width in [320, 390, 768, 1024, 1440]:
                page.set_viewport_size({'width': check_width, 'height': 1000})
                page.wait_for_timeout(80)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (name, theme, check_width)
                if check_width in [390, 1440] and name != 'codex':
                    page.locator(panel).first.screenshot(path=str(out / f'{name}-{theme}-{check_width}.png'))
        print(name, 'open, close, flow, reversal, inert and reduced motion passed', flush=True)

    page.set_viewport_size({'width': 1440, 'height': 1000})
    page.goto(base + '/tools/codex-jsonl-cleaner', wait_until='networkidle')
    button = page.locator('button[aria-controls="codex-import-guide"]')
    button.click()
    page.wait_for_timeout(350)
    page.get_by_role('radio', name='macOS', exact=True).click()
    # Programmatic close while focus remains inside must return it to the opener.
    button.evaluate('(el) => el.click()')
    expect(button).to_be_focused()
    page.wait_for_timeout(350)
    button.click()
    expect(page.get_by_role('radio', name='macOS', exact=True)).to_be_checked()
    for theme in ['dark', 'light']:
        page.evaluate('(theme) => document.documentElement.dataset.theme = theme', theme)
        for width in [320, 390, 768, 1024, 1440]:
            page.set_viewport_size({'width': width, 'height': 1000})
            page.wait_for_timeout(350)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (theme, width)
            assert page.locator('#codex-import-guide').evaluate('el => el.scrollHeight <= el.closest(".collapse-panel").clientHeight + 1')
            if width in [390, 1440]:
                page.locator('.codex-cleaner-panel').first.screenshot(path=str(out / f'codex-{theme}-{width}.png'))
    # A collapsing mobile directory must not leave an anchor behind the header.
    page.set_viewport_size({'width': 390, 'height': 844})
    page.goto(base + '/projects/rdp-access-auth/wiki', wait_until='networkidle')
    page.locator('.wiki-mobile-toc').click()
    page.wait_for_timeout(350)
    page.locator('.rdp-toc a[href="#section-7"]').click()
    page.wait_for_timeout(1200)
    top = page.locator('#section-7').evaluate('el => el.getBoundingClientRect().top')
    assert 145 <= top <= 185, ('anchor after animated close', top)
    # Desktop navigation remains visible when resizing from a collapsed mobile directory.
    for path, directory in [('/projects/rdp-access-auth/wiki', '#wiki-directory'), ('/projects/gaze/guide/installation', '#gaze-directory')]:
        page.set_viewport_size({'width': 390, 'height': 844})
        page.goto(base + path, wait_until='networkidle')
        page.set_viewport_size({'width': 1024, 'height': 1000})
        expect(page.locator(directory)).to_be_visible()
        page.wait_for_timeout(400)
        assert page.locator(directory).evaluate('el => !el.inert')
    # The nested custom-settings animation also fits inside the scaled game fullscreen.
    page.set_viewport_size({'width': 390, 'height': 844})
    page.goto(base + '/games/minesweeper', wait_until='networkidle')
    page.locator('select[aria-labelledby="mine-level-label"]').select_option('custom')
    page.wait_for_timeout(350)
    page.get_by_role('spinbutton', name='棋盘边长').fill('12')
    page.get_by_role('spinbutton', name='地雷数量').fill('24')
    page.get_by_role('button', name='应用并开局').click()
    page.get_by_role('button', name='网页全屏', exact=True).click()
    for width, height in [(320, 568), (390, 844), (1440, 900)]:
        page.set_viewport_size({'width': width, 'height': height})
        page.locator('.mine-custom-toggle').click()
        page.wait_for_timeout(400)
        expect(page.get_by_role('spinbutton', name='棋盘边长')).to_have_value('12')
        assert page.locator('.game-play-content').evaluate('el => el.scrollWidth <= el.clientWidth'), width
        page.locator('.mine-custom-toggle').click()
        page.wait_for_timeout(400)
        assert page.locator('.mine-custom > .collapse-panel').evaluate('el => el.getBoundingClientRect().height') == 0
        assert page.locator('.mine-cell').count() == 144
    page.get_by_role('button', name='退出全屏', exact=True).click()
    assert not errors, errors
    (out / 'motion.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    browser.close()
print('Disclosure motion, responsive layout, focus and anchor checks passed')
