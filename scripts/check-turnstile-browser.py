"""Exercise the real Cloudflare test widget and local server-side Siteverify."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:8788').rstrip('/')
out = Path('artifacts/rooms'); out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1440, 'height': 1100}, color_scheme='dark', reduced_motion='reduce')
    page.goto(base + '/games/gomoku', wait_until='networkidle')
    page.get_by_role('radio', name='朋友联机', exact=True).click()
    page.get_by_label('你的昵称', exact=True).fill('真实组件测试')
    expect(page.locator('.room-turnstile')).to_be_visible(timeout=60000)
    expect(page.get_by_role('button', name='创建房间', exact=True)).to_be_enabled(timeout=60000)
    page.locator('.room-surface').screenshot(path=str(out / 'turnstile-real-dark-desktop.png'))
    page.get_by_role('button', name='创建房间', exact=True).click()
    expect(page.locator('.room-number')).to_be_visible(timeout=20000)
    page.get_by_role('button', name='离开房间', exact=True).click()
    page.get_by_role('button', name='确认离开', exact=True).click()
    page.set_viewport_size({'width': 320, 'height': 1100})
    page.get_by_role('radio', name='朋友联机', exact=True).click()
    expect(page.locator('.room-turnstile')).to_be_visible(timeout=60000)
    expect(page.get_by_role('button', name='创建房间', exact=True)).to_be_enabled(timeout=60000)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.locator('.room-surface').screenshot(path=str(out / 'turnstile-real-320.png'))
    browser.close()
print('Real Cloudflare test widget, server-side Siteverify and 320px compact layout: passed. Production keys still require separate verification.')
