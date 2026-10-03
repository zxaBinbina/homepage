"""Check project pages on the dev or preview server; requires Python Playwright."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:5173').rstrip('/')
out = Path('artifacts')
out.mkdir(exist_ok=True)
errors = []
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    context = browser.new_context(color_scheme='dark', reduced_motion='reduce')
    page = context.new_page()
    page.on('pageerror', lambda error: errors.append(str(error)))
    for route, label in [('/projects/rdp-access-auth', 'official'), ('/projects/rdp-access-auth/wiki', 'wiki')]:
        for theme in ['dark', 'light']:
            page.goto(base + route, wait_until='networkidle')
            page.evaluate('(theme) => localStorage.setItem("homepage-theme", theme)', theme)
            page.reload(wait_until='networkidle')
            assert page.locator('html').get_attribute('data-theme') == theme
            assert 'RDP Access Auth' in page.title()
            assert page.locator('h1').count() == 1
            assert page.locator('.rdp-mark').evaluate('(img) => img.tagName === \"IMG\" && img.complete && img.naturalWidth > 0')
            assert not page.locator('img').evaluate_all('(images) => images.filter(img => !img.complete || !img.naturalWidth).map(img => img.src)')
            assert page.get_by_role('link', name='萌ICP备20264016号').get_attribute('href') == 'https://icp.gov.moe/?keyword=20264016'
            assert page.locator('link[rel=canonical]').get_attribute('href') == 'https://zxabinbina.cc.cd' + route + '/'
            assert page.locator('.rdp-header [aria-current=page]').count() == 1
            assert page.evaluate('getComputedStyle(document.querySelector(".rdp-header")).display') == 'flex'
            for width in [320, 390, 480, 760, 768, 1024, 1440]:
                page.set_viewport_size({'width': width, 'height': 960})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (route, theme, width)
                if width in [390, 1440]:
                    page.screenshot(path=str(out / f'rdp-{label}-{theme}-{width}.png'), full_page=True)
            if label == 'wiki':
                for link in page.locator('.rdp-toc nav a').all():
                    assert page.locator(link.get_attribute('href')).count() == 1
                page.locator('.rdp-toc a[href="#deployment"]').click()
                page.wait_for_timeout(150)
                assert page.locator('#deployment').evaluate('(e) => Math.abs(e.getBoundingClientRect().top - 110) < 3')
                assert 'git clone https://github.com/zxaBinbina/rdp-access-auth.git' in page.locator('.rdp-doc').inner_text()
                assert page.locator('.rdp-doc pre').count() >= 10
            page.get_by_role('button', name='切换浅色主题' if theme == 'dark' else '切换深色主题').click()
            page.reload(wait_until='networkidle')
            assert page.locator('html').get_attribute('data-theme') != theme
    page.goto(base)
    card = page.locator('a.project-card[href="/projects/rdp-access-auth/"]')
    card.wait_for(state='attached')
    assert card.count() == 1 and card.get_attribute('target') is None
    card.click()
    page.get_by_role('link', name='开始部署').click()
    assert page.url.endswith('/wiki/#deployment')
    page.reload(wait_until='networkidle')
    assert page.locator('#deployment').evaluate('(e) => Math.abs(e.getBoundingClientRect().top - 110) < 3')
    # Shared theme: follow system until an explicit preference is saved.
    for route in ['/', '/projects/rdp-access-auth/', '/projects/rdp-access-auth/wiki/']:
        fresh = browser.new_context(color_scheme='dark')
        view = fresh.new_page()
        view.goto(base + route, wait_until='networkidle')
        view.emulate_media(color_scheme='light')
        view.wait_for_function("document.documentElement.dataset.theme === 'light'")
        assert view.locator('meta[name="theme-color"]').get_attribute('content') == '#f4f6fa'
        view.get_by_role('button', name='切换深色主题').click()
        view.emulate_media(color_scheme='dark')
        view.emulate_media(color_scheme='light')
        assert view.locator('html').get_attribute('data-theme') == 'dark'
        view.goto(base + '/projects/rdp-access-auth/wiki/', wait_until='networkidle')
        assert view.locator('html').get_attribute('data-theme') == 'dark'
        fresh.close()
    assert not errors, errors
    browser.close()
print('Project pages: direct URLs, homepage entry, deployment link, directory anchors, metadata, theme persistence, reduced motion and 320–1440px layouts passed.')
