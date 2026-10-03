"""Browser smoke checks. Requires Python Playwright and Google Chrome."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / 'artifacts'
OUT.mkdir(exist_ok=True)
errors = []
results = []
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), headless=True, args=['--no-sandbox'])
    context = browser.new_context(color_scheme='dark',viewport={'width': 1440, 'height': 1000}, permissions=['clipboard-read', 'clipboard-write'])
    page = context.new_page()
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:5173'), wait_until='networkidle')
    assert page.title() == 'a彬彬a · 在代码与方块之间'
    assert page.locator('.project-card').count() == 4
    for section in ['about', 'projects', 'world', 'contact']:
        page.locator('#' + section).scroll_into_view_if_needed()
        page.wait_for_timeout(300)
    page.wait_for_timeout(700)
    assert page.locator('a[href="https://icp.gov.moe/?keyword=20264016"]').inner_text() == '萌ICP备20264016号'
    assert page.locator('a[href="https://icp.gov.moe/?keyword=20264016"]').get_attribute('target') == '_blank'
    broken = page.locator('img').evaluate_all('(els) => els.filter(e => !e.complete || !e.naturalWidth).map(e => e.src)')
    assert not broken, broken
    page.locator('.address-button').click()
    assert page.locator('[role=status]').inner_text() == '服务器地址已复制'
    assert page.evaluate('navigator.clipboard.readText()') == 'play.mcyzw.top'
    page.get_by_role('button', name='切换浅色主题').click()
    assert page.locator('html').get_attribute('data-theme') == 'light'
    page.reload(wait_until='networkidle')
    assert page.locator('html').get_attribute('data-theme') == 'light'
    page.screenshot(path=str(OUT / 'desktop-light.png'))
    page.get_by_role('button', name='切换深色主题').click()
    for section in ['home','about','projects','world','contact']:
        page.locator('#'+section).scroll_into_view_if_needed()
        page.wait_for_timeout(250)
    page.evaluate('window.scrollTo({top:0,behavior:"instant"})')
    page.wait_for_timeout(700)
    page.screenshot(path=str(OUT / 'desktop.png'), full_page=True)
    results += ['Desktop, images, ICP link, clipboard, theme toggle and persistence: passed']
    for width in [320, 390, 768, 1024, 1440]:
        page.set_viewport_size({'width':width, 'height':844})
        page.wait_for_timeout(300)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), f'overflow at {width}'
    page.set_viewport_size({'width':390, 'height':844})
    page.evaluate('window.scrollTo({top:0,behavior:"instant"})')
    page.get_by_role('button',name='打开菜单').click()
    assert page.locator('#mobile-nav').is_visible()
    page.locator('#mobile-nav a[href="#about"]').click()
    page.locator('#mobile-nav').wait_for(state='detached')
    page.wait_for_timeout(800)
    assert page.evaluate('Math.abs(document.querySelector("#about").getBoundingClientRect().top - 110) < 3')
    page.get_by_role('button',name='打开菜单').click()
    page.keyboard.press('Escape')
    page.locator('#mobile-nav').wait_for(state='detached')
    page.evaluate('window.scrollTo({top:0,behavior:"instant"})')
    page.wait_for_timeout(400)
    page.screenshot(path=str(OUT / 'mobile.png'), full_page=True)
    results += ['320 / 390 / 768 / 1024 / 1440px: no horizontal overflow', 'Mobile menu, section navigation and Escape: passed']
    context.grant_permissions([])
    page.evaluate('Object.defineProperty(navigator, "clipboard", {value: {writeText: () => Promise.reject(new Error("blocked"))}, configurable:true})')
    page.locator('.address-button').click()
    assert '请手动复制：play.mcyzw.top' in page.locator('[role=status]').inner_text()
    results += ['Clipboard failure fallback: passed']
    assert not errors, errors
    results += ['Browser JavaScript errors: none']
    print(json.dumps(results,ensure_ascii=False,indent=2))
    browser.close()
