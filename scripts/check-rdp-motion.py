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
    page.get_by_role('button', name='显示示例密码').click()
    assert '•' not in page.locator('.demo-password').inner_text()
    page.get_by_role('button', name='隐藏示例密码').click()
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
    # All authentication methods remain selectable even over the success result.
    for theme in ['dark', 'light']:
        page.evaluate("theme => document.documentElement.dataset.theme = theme", theme)
        for width in [320, 390, 768, 1024, 1440]:
            page.set_viewport_size({'width': width, 'height': 1000})
            for label, method in [('固定密码', 'password'), ('临时密码', 'temporary'), ('通行密钥', 'passkey')]:
                page.get_by_role('button', name=label, exact=True).click()
                assert demo.get_attribute('data-method') == method
                page.get_by_role('heading', name='认证成功', exact=True).wait_for()
                assert page.locator('.demo-rotation').count() == (1 if method == 'temporary' else 0)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (theme, width, method)
                result = page.locator('.demo-result')
                assert result.evaluate('(e) => e.scrollHeight <= e.clientHeight'), (theme, width, method, 'result overflow')
                page.get_by_role('button', name='失败流程').click()
                expected = {'password': '密码不正确', 'temporary': '已使用', 'passkey': '取消或超时'}[method]
                assert expected in page.locator('.demo-error').inner_text()
                if width == 390:
                    demo.screenshot(path=str(out / f'rdp-demo-{method}-{theme}.png'))
    for width, height in [(1024, 720), (1280, 720), (1366, 768), (1440, 900), (1920, 1080)]:
        page.set_viewport_size({'width': width, 'height': height})
        for label in ['固定密码', '临时密码', '通行密钥']:
            page.get_by_role('button', name=label, exact=True).click()
            for result in ['成功流程', '失败流程']:
                page.get_by_role('button', name=result).click()
                page.evaluate('scrollTo({top: 0, behavior: "instant"})')
                for selector in ['.auth-demo', '.rdp-hero-copy']:
                    rect = page.locator(selector).bounding_box()
                    assert rect['y'] >= 0 and rect['y'] + rect['height'] <= height, (width, height, label, result, selector, rect)
        page.screenshot(path=str(out / f'rdp-first-screen-{width}.png'))
    page.emulate_media(reduced_motion='no-preference')
    page.locator('.demo-playback').wait_for()
    page.set_viewport_size({'width': 1440, 'height': 1000})
    page.get_by_role('button', name='临时密码', exact=True).click()
    demo.scroll_into_view_if_needed()
    assert page.locator('.demo-temporary .demo-input').count() == 3
    page.wait_for_function("document.querySelector('.auth-demo').dataset.phase === 'checking'")
    page.get_by_role('heading', name='认证成功', exact=True).wait_for()
    page.get_by_role('button', name='通行密钥', exact=True).click()
    assert '请在设备上确认' in page.locator('.demo-passkey').inner_text()
    page.wait_for_function("document.querySelector('.auth-demo').dataset.phase === 'checking'")
    assert '设备已确认' in page.locator('.demo-passkey').inner_text()
    page.get_by_role('heading', name='认证成功', exact=True).wait_for()
    page.get_by_role('button', name='失败流程').click()
    page.get_by_role('heading', name='认证失败', exact=True).wait_for()
    page.wait_for_function("document.querySelector('.auth-demo').dataset.method === 'password'", timeout=10000)
    assert all(method == 'GET' and url.startswith(base) for method, url in requests), requests
    assert not errors, errors
    browser.close()
print('Three authentication methods, rotation, device confirmation, automatic cycling, replay/pause, reduced motion, both themes, narrow layouts, desktop first-screen fit and no authentication requests: passed.')
