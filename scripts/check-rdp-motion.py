"""Exercise the simulated authentication and motion preferences in a real browser."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:4174').rstrip('/')
out = Path('artifacts')
out.mkdir(exist_ok=True)
errors, requests = [], []
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1440, 'height': 1000}, color_scheme='dark', reduced_motion='no-preference')
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('request', lambda request: requests.append((request.method, request.url)))
    page.goto(base + '/projects/rdp-access-auth/', wait_until='networkidle')
    demo = page.get_by_role('region', name='认证流程动画演示')
    page.wait_for_function("document.querySelector('.demo-password').textContent.includes('•')")
    page.get_by_role('button', name='暂停演示').click()
    paused = page.locator('.demo-password').inner_text()
    phase = demo.get_attribute('data-phase')
    page.wait_for_timeout(650)
    assert page.locator('.demo-password').inner_text() == paused and demo.get_attribute('data-phase') == phase
    page.get_by_role('button', name='播放演示').click()
    page.wait_for_function("document.querySelector('.auth-demo').dataset.phase === 'checking'")
    page.get_by_role('heading', name='认证成功', exact=True).wait_for()
    page.get_by_role('button', name='暂停演示').click()
    assert '6 小时内' in page.locator('.demo-result-detail').inner_text()
    page.screenshot(path=str(out / 'rdp-demo-success.png'))
    page.get_by_role('button', name='失败流程').click()
    page.get_by_role('heading', name='认证失败', exact=True).wait_for()
    page.get_by_role('button', name='暂停演示').click()
    page.screenshot(path=str(out / 'rdp-demo-failure.png'))
    page.get_by_role('button', name='重播演示').click()
    assert demo.get_attribute('data-phase') == 'typing'
    page.locator('.rdp-footer').scroll_into_view_if_needed()
    page.wait_for_timeout(700)
    state = page.locator('.demo-password').inner_text()
    page.wait_for_timeout(600)
    assert page.locator('.demo-password').inner_text() == state, 'Offscreen animation kept advancing'
    # Motion can be disabled while the page is open; all content stays visible.
    page.emulate_media(reduced_motion='reduce')
    demo.scroll_into_view_if_needed()
    assert page.get_by_role('button', name='暂停演示').count() == 0
    assert '已减少动态效果' in page.locator('.demo-caption').inner_text()
    page.get_by_role('button', name='成功流程').click()
    page.get_by_role('heading', name='认证成功', exact=True).wait_for()
    page.get_by_role('button', name='失败流程').click()
    page.get_by_role('heading', name='认证失败', exact=True).wait_for()
    page.wait_for_timeout(600)
    assert demo.get_attribute('data-phase') == 'failure'
    for width in [320, 390, 768, 1024, 1440]:
        page.set_viewport_size({'width': width, 'height': 1000})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
        assert page.locator('.demo-controls').evaluate('(e) => e.scrollWidth <= e.clientWidth'), width
    assert all(method == 'GET' and url.startswith(base) for method, url in requests), requests
    assert not errors, errors
    browser.close()
print('Typing, checking, success/failure, replay, pause, offscreen suspension, live reduced-motion preference, layout and no authentication requests: passed.')
