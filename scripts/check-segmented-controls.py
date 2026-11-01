"""Check shared selection indicators, wrapping, keyboard input and existing option behavior."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:5173').rstrip('/')
out = Path('artifacts/segmented')
out.mkdir(parents=True, exist_ok=True)

aligned = '''() => [...document.querySelectorAll('.seg:not(.seg--multiple)')].every(group => {
    if (!group.offsetWidth || group.closest('[inert]')) return true;
    const selected = group.querySelector('.seg__item[aria-checked="true"],.seg__item[aria-pressed="true"],.seg__item[aria-selected="true"]');
    const thumb = group.querySelector('.seg__thumb');
    if (!selected) return !thumb || +getComputedStyle(thumb).opacity === 0;
    if (!thumb || +getComputedStyle(thumb).opacity !== 1) return false;
    const a = selected.getBoundingClientRect(), b = thumb.getBoundingClientRect();
    return ['x','y','width','height'].every(key => Math.abs(a[key]-b[key]) <= 1.1);
})'''


def settled(page):
    page.wait_for_function(aligned)


def sample(page, selector, index):
    return page.evaluate('''async ({selector,index}) => {
        const group = document.querySelector(selector), thumb = group.querySelector('.seg__thumb');
        const samples = [], start = performance.now();
        function record() {
            const t = thumb.getBoundingClientRect(), g = group.getBoundingClientRect();
            samples.push({time: performance.now()-start,x:t.x-g.x,y:t.y-g.y,width:t.width});
        }
        record(); group.querySelectorAll('.seg__item')[index].click();
        while (performance.now()-start<340) { await new Promise(requestAnimationFrame); record(); }
        return samples;
    }''', {'selector': selector, 'index': index})


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='no-preference')
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(base + '/tool', wait_until='networkidle')
    group = page.get_by_role('group', name='工具分类', exact=True)
    options = group.locator('button')
    count = options.count()
    motions = {}
    for width in [1440, 390]:
        page.set_viewport_size({'width': width, 'height': 1000})
        options.first.click()
        settled(page)
        frames = sample(page, '.tool-filters', count-1)
        positions = {(round(frame['x'], 1), round(frame['y'], 1)) for frame in frames}
        assert len(positions) >= 4, ('indicator jumped without intermediate frames', width, frames)
        if width == 390:
            assert frames[-1]['y'] > frames[0]['y'], 'Wrapped options did not move the indicator between rows'
        settled(page)
        expect(options.last).to_have_attribute('aria-pressed', 'true')
        motions[str(width)] = frames
    # Last selection wins, including while the previous movement is unfinished.
    page.evaluate('''async () => {
        const buttons = document.querySelectorAll('.tool-filters button');
        for (const index of [0,8,1,7,2]) { buttons[index].click(); await new Promise(r=>setTimeout(r,35)); }
    }''')
    settled(page)
    expect(options.nth(2)).to_have_attribute('aria-pressed', 'true')
    options.nth(2).focus()
    page.keyboard.press('Home')
    expect(options.first).to_be_focused()
    expect(options.first).to_have_attribute('aria-pressed', 'true')
    page.keyboard.press('End')
    expect(options.last).to_be_focused()
    expect(options.last).to_have_attribute('aria-pressed', 'true')
    page.keyboard.press('ArrowRight')
    expect(options.first).to_be_focused()
    expect(options.first).to_have_attribute('aria-pressed', 'true')
    search = page.get_by_role('searchbox', name='搜索工具')
    search.fill('JSON')
    options.last.click()
    options.first.click()
    expect(search).to_have_value('JSON')
    expect(page.locator('.tool-card').first).to_be_visible()
    search.fill('')
    options.last.click()
    selected_category = options.last.inner_text()
    page.wait_for_timeout(400)
    assert page.locator('.tool-card-bottom > span:first-child').all_text_contents() == [selected_category] * page.locator('.tool-card').count()
    for palette in ['fufu-blue', 'hutao-red']:
        for theme in ['dark', 'light']:
            page.evaluate('([palette,theme]) => {document.documentElement.dataset.palette=palette;document.documentElement.dataset.theme=theme}', [palette, theme])
            for width in [320, 390, 480, 481, 768, 1024, 1440]:
                page.set_viewport_size({'width': width, 'height': 1000})
                settled(page)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (palette, theme, width)
                if width in [390, 1440]:
                    page.locator('.directory-toolbar').screenshot(path=str(out / f'tools-{palette}-{theme}-{width}.png'))
    options.first.click()
    page.wait_for_timeout(30)
    page.emulate_media(reduced_motion='reduce')
    settled(page)
    options.last.click()
    settled(page)
    assert group.locator('.seg__thumb').evaluate('el => el.getAnimations().length') == 0
    print('Tool categories: moving/wrapping indicator, filtering, keyboard, rapid input, four themes and reduced motion passed', flush=True)

    # Existing Freemium modes retain icons, radio semantics and functional state.
    page.goto(base + '/tools/html-preview', wait_until='networkidle')
    for group in page.get_by_role('radiogroup').all():
        choices = group.get_by_role('radio')
        choices.first.focus()
        page.keyboard.press('End')
        expect(choices.last).to_be_checked()
        expect(choices.last).to_be_focused()
    settled(page)

    page.goto(base + '/tools/codex-jsonl-cleaner', wait_until='networkidle')
    page.get_by_role('button', name='导入教程', exact=True).click()
    group = page.get_by_role('radiogroup', name='教程适用系统')
    group.get_by_role('radio', name='Windows', exact=True).click()
    page.keyboard.press('ArrowRight')
    expect(group.get_by_role('radio', name='macOS', exact=True)).to_be_checked()
    expect(page.locator('.codex-import-platform')).to_contain_text('Finder')
    settled(page)

    page.goto(base + '/tools/cron-parser', wait_until='networkidle')
    group = page.get_by_role('group', name='常用示例')
    page.locator('#cron-input').fill('*/7 * * * *')
    expect(group.locator('[aria-pressed="true"]')).to_have_count(0)
    settled(page)
    group.locator('button').first.click()
    expect(page.locator('#cron-input')).to_have_value(group.locator('button').first.get_attribute('title'))
    settled(page)

    page.goto(base + '/tools/regex-tester', wait_until='networkidle')
    group = page.get_by_role('group', name='标志', exact=True)
    expect(group.locator('button').first).to_have_attribute('aria-pressed', 'true')
    other = group.locator('[aria-pressed="false"]').first
    other.click()
    expect(group.locator('button').first).to_have_attribute('aria-pressed', 'true')
    assert group.locator('[aria-pressed="true"]').count() >= 2
    group.locator('button').first.focus()
    page.keyboard.press('End')
    expect(group.locator('button').last).to_be_focused()
    for width in [320, 390, 768, 1440]:
        page.set_viewport_size({'width': width, 'height': 1000})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    print('Tool modes, Codex platform, Cron presets and independent Regex flags passed', flush=True)

    page.goto(base + '/projects/gaze/guide/cli', wait_until='networkidle')
    group = page.locator('.gaze-code-tabs').first
    group.get_by_role('tab').first.focus()
    page.keyboard.press('End')
    last = group.get_by_role('tab').last
    expect(last).to_be_focused()
    expect(last).to_have_attribute('aria-selected', 'true')
    panel = page.locator('[role="tabpanel"]').filter(has=page.locator('code')).last
    assert page.locator('[role="tabpanel"]').count() > 0
    assert page.evaluate('''() => [...document.querySelectorAll('[role=tab]')].every(tab => {
        const panel = document.getElementById(tab.getAttribute('aria-controls'));
        return panel && (tab.getAttribute('aria-selected') !== 'true' || panel.getAttribute('aria-labelledby') === tab.id);
    })''')
    settled(page)
    page.goto(base + '/projects/gaze/guide/installation', wait_until='networkidle')
    for width in [320, 390, 768, 1024, 1440]:
        page.set_viewport_size({'width': width, 'height': 1000})
        page.locator('.gaze-code-tabs').first.get_by_role('tab').last.click()
        settled(page)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        if width in [390, 1440]:
            page.locator('.gaze-code:has(.gaze-code-tabs)').first.screenshot(path=str(out / f'gaze-final-{width}.png'))
    page.goto(base + '/projects/rdp-access-auth', wait_until='networkidle')
    page.get_by_role('button', name='通行密钥', exact=True).click()
    expect(page.locator('.auth-demo')).to_have_attribute('data-method', 'passkey')
    page.get_by_role('button', name='失败流程', exact=True).click()
    expect(page.locator('.auth-demo')).to_have_attribute('data-phase', 'failure')
    settled(page)
    for width in [320, 390, 768, 1440]:
        page.set_viewport_size({'width': width, 'height': 1000})
        settled(page)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    print('Gaze tabs/linked panels and RDP methods/scenarios passed', flush=True)

    page.set_viewport_size({'width': 390, 'height': 844})
    trigger = page.get_by_role('button', name='选择配色方案', exact=True)
    trigger.click()
    settled(page)
    page.get_by_role('button', name='胡桃红', exact=True).click()
    expect(page.locator('html')).to_have_attribute('data-palette', 'hutao-red')
    expect(page.get_by_role('button', name='胡桃红', exact=True)).to_be_focused()
    expect(trigger).to_have_attribute('aria-expanded', 'true')
    blue = page.get_by_role('button', name='芙芙蓝', exact=True).bounding_box()
    red = page.get_by_role('button', name='胡桃红', exact=True).bounding_box()
    assert abs(blue['y'] - red['y']) < 1 and red['x'] >= blue['x'] + blue['width'] - 1
    settled(page)
    page.locator('.palette-popover').screenshot(path=str(out / 'palette-final.png'))
    page.keyboard.press('Escape')
    expect(trigger).to_be_focused()

    touch = browser.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True, reduced_motion='reduce')
    phone = touch.new_page()
    phone.on('pageerror', lambda error: errors.append(str(error)))
    phone.goto(base + '/games/minesweeper', wait_until='networkidle')
    mode = phone.get_by_role('group', name='扫雷操作模式')
    mode.get_by_role('button', name='插旗', exact=True).tap()
    phone.locator('.mine-cell').first.tap()
    expect(phone.locator('.mine-cell.is-flag')).to_have_count(1)
    mode.get_by_role('button', name='翻开', exact=True).tap()
    expect(phone.locator('.mine-cell.is-flag')).to_have_count(1)
    phone.get_by_role('button', name='网页全屏', exact=True).tap()
    for width, height in [(320, 568), (390, 844), (844, 390)]:
        phone.set_viewport_size({'width': width, 'height': height})
        settled(phone)
        mode.get_by_role('button', name='插旗', exact=True).tap()
        settled(phone)
        assert phone.locator('.game-play-content').evaluate('el=>el.scrollWidth <= el.clientWidth')
    phone.get_by_role('button', name='退出全屏', exact=True).tap()
    settled(phone)
    assert not errors, errors
    (out / 'motion.json').write_text(json.dumps(motions, indent=2))
    browser.close()
print('Shared segmented controls: geometry, input behavior, responsive layout and accessibility checks passed')
