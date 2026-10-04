"""Check the Wiki search, mobile directory, copying and Agent prompt."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:4174').rstrip('/')
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, color_scheme='dark', reduced_motion='reduce', permissions=['clipboard-read', 'clipboard-write'])
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(base + '/projects/rdp-access-auth/wiki', wait_until='networkidle')
    assert page.locator('.wiki-section-heading').count() == 19
    assert page.locator('.wiki-section-heading').first.inner_text() == '部署前准备'
    assert page.locator('.wiki-deploy-step').count() == 6
    assert page.get_by_text('当前阅读', exact=True).count() == 0
    page.set_viewport_size({'width': 1440, 'height': 700})
    for motion in ['reduce', 'no-preference']:
        page.emulate_media(reduced_motion=motion)
        for section_id in ['section-13', 'deployment']:
            page.locator('#' + section_id).evaluate('(el) => el.scrollIntoView({behavior: "instant"})')
            document_position = page.evaluate('scrollY')
            page.wait_for_function("""(id) => {
                const toc = document.querySelector('.rdp-toc');
                const active = toc.querySelector('a[aria-current="location"]');
                if (!active || active.hash !== '#' + id) return false;
                const outer = toc.getBoundingClientRect(), inner = active.getBoundingClientRect();
                return inner.top >= outer.top && inner.bottom <= outer.bottom;
            }""", arg=section_id)
            page.wait_for_timeout(300)
            assert abs(page.evaluate('scrollY') - document_position) < 2, 'Directory following moved the document'
            if section_id == 'section-13':
                assert page.locator('.rdp-toc').evaluate('(el) => el.scrollTop') > 0
    page.emulate_media(reduced_motion='reduce')
    page.set_viewport_size({'width': 1440, 'height': 1000})
    page.get_by_role('searchbox', name='搜索文档').fill('rdp-auth deploy --gui')
    assert page.locator('.rdp-toc nav a').count() == 1
    assert '打开部署向导' in page.locator('.rdp-toc nav a').inner_text()
    page.get_by_role('searchbox', name='搜索文档').fill('不存在的搜索内容')
    assert page.locator('.rdp-toc nav a').count() == 0
    assert '没有找到' in page.locator('.wiki-search-count').inner_text()
    page.get_by_role('button', name='清空搜索').click()
    assert page.locator('.rdp-toc nav a').count() == 19
    page.locator('.wiki-agent summary').click()
    page.get_by_role('button', name='复制部署提示词').click()
    assert page.evaluate('navigator.clipboard.readText()') == Path('docs/rdp-agent-deploy.md').read_text()
    page.locator('.wiki-agent summary').click()
    install = page.locator('.wiki-section').filter(has=page.locator('#section-4'))
    install.get_by_role('button', name='复制代码').click()
    install_code = page.evaluate('navigator.clipboard.readText()')
    assert 'rdp-access-auth-0.2.0-1.fc44.x86_64.rpm' in install_code
    assert 'rdp-access-auth_0.2.0_py314_amd64.deb' in install_code
    assert 'sha256sum -c' in install_code
    page.evaluate('Object.defineProperty(navigator, "clipboard", {value: {writeText: () => Promise.reject(new Error("blocked"))}, configurable:true})')
    install.get_by_role('button').click()
    assert '复制失败' in install.locator('[role=status]').inner_text()
    for width in [320, 390, 768, 1024, 1440]:
        page.set_viewport_size({'width': width, 'height': 1000})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
    page.set_viewport_size({'width': 390, 'height': 844})
    page.goto(base + '/projects/rdp-access-auth/wiki', wait_until='networkidle')
    toggle = page.get_by_role('button', name='文档目录', exact=True)
    assert toggle.get_attribute('aria-expanded') == 'false'
    assert page.locator('#wiki-directory').get_attribute('inert') is not None
    toggle.click()
    page.get_by_role('searchbox', name='搜索文档').fill('auth_mode')
    page.locator('.rdp-toc nav a[href="#section-7"]').click()
    assert toggle.get_attribute('aria-expanded') == 'false'
    assert page.url.endswith('#section-7')
    assert page.locator('#section-7').evaluate('(el) => el.getBoundingClientRect().top') >= 145
    page.reload(wait_until='networkidle')
    assert page.locator('#section-7').evaluate('(el) => el.getBoundingClientRect().top') >= 145
    toggle.click()
    page.get_by_role('searchbox', name='搜索文档').focus()
    page.keyboard.press('Escape')
    assert toggle.get_attribute('aria-expanded') == 'false'
    assert toggle.evaluate('(el) => el === document.activeElement')
    page.locator('.wiki-agent summary').click()
    assert page.get_by_role('button', name='复制部署提示词').is_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors, errors
    browser.close()
print('Wiki: deployment-first reading, full-text section search, empty state, exact code/prompt copying, clipboard fallback, mobile directory, Escape and old deep links passed.')
