"""Browser smoke checks. Requires Python Playwright and Google Chrome."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / 'artifacts'
OUT.mkdir(exist_ok=True)


def assert_cursor_palette(page, base_url, palette):
    cursor_values = page.locator('html').evaluate(
        """(el) => {
          const style = getComputedStyle(el)
          return ['--cursor-normal', '--cursor-link', '--cursor-text', '--cursor-busy', '--cursor-grabbing']
            .map((property) => style.getPropertyValue(property))
        }"""
    )
    assert all(f'/cursors/{palette}/' in value for value in cursor_values), cursor_values
    applied_cursors = page.evaluate("""() => {
      const animatedBusy = document.body.classList.contains('has-animated-busy-cursor')
      document.body.classList.remove('has-animated-busy-cursor')
      const anchor = document.createElement('a')
      const input = document.createElement('input')
      const busy = document.createElement('div')
      const dragging = document.createElement('div')
      busy.setAttribute('aria-busy', 'true')
      dragging.draggable = true
      document.body.append(anchor, input, busy, dragging)
      const cursors = [document.body, anchor, input, busy, dragging]
        .map((element) => getComputedStyle(element).cursor)
      anchor.remove()
      input.remove()
      busy.remove()
      dragging.remove()
      if (animatedBusy) document.body.classList.add('has-animated-busy-cursor')
      return cursors
    }""")
    assert all(f'/cursors/{palette}/' in value for value in applied_cursors), applied_cursors
    assets = ['normal.png', 'link.png', 'text.png', 'busy.png', 'busy.gif']
    for asset in assets:
        response = page.request.get(f'{base_url}/cursors/{palette}/{asset}')
        assert response.ok, f'{palette}/{asset}: HTTP {response.status}'


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
    assert page.locator('html').get_attribute('data-palette') == 'fufu-blue'
    base_url = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:5173').rstrip('/')
    assert_cursor_palette(page, base_url, 'fufu-blue')
    page.evaluate("""() => {
      const target = document.createElement('div')
      target.dataset.cursorTest = ''
      target.setAttribute('aria-busy', 'true')
      target.textContent = '加载中'
      Object.assign(target.style, { position: 'fixed', left: '4px', top: '90px', zIndex: '300', width: '100px', height: '32px' })
      document.body.append(target)
    }""")
    assert page.locator('.theme-toggle').evaluate('(e) => e.previousElementSibling.classList.contains("palette-picker")')
    page.get_by_role('button', name='选择配色方案').click()
    page.get_by_role('button', name='胡桃红').click()
    assert page.locator('html').get_attribute('data-palette') == 'hutao-red'
    assert_cursor_palette(page, base_url, 'hutao-red')
    page.mouse.move(12, 100)
    page.locator('.animated-busy-cursor').wait_for()
    assert page.locator('.animated-busy-cursor').get_attribute('src').endswith('/cursors/hutao-red/busy.gif')
    page.get_by_role('button', name='选择配色方案').click()
    page.get_by_role('button', name='芙芙蓝').click()
    page.mouse.move(12, 100)
    page.wait_for_function("document.querySelector('.animated-busy-cursor')?.src.endsWith('/cursors/fufu-blue/busy.gif')")
    assert page.locator('.animated-busy-cursor').get_attribute('src').endswith('/cursors/fufu-blue/busy.gif')
    assert_cursor_palette(page, base_url, 'fufu-blue')
    page.get_by_role('button', name='选择配色方案').click()
    page.get_by_role('button', name='胡桃红').click()
    page.mouse.move(12, 100)
    page.wait_for_function("document.querySelector('.animated-busy-cursor')?.src.endsWith('/cursors/hutao-red/busy.gif')")
    assert page.locator('.animated-busy-cursor').get_attribute('src').endswith('/cursors/hutao-red/busy.gif')
    assert_cursor_palette(page, base_url, 'hutao-red')
    page.locator('[data-cursor-test]').evaluate('(e) => e.remove()')
    page.wait_for_timeout(350)
    palette_bg = page.locator('body').evaluate('(e) => [getComputedStyle(e).backgroundColor, getComputedStyle(e).getPropertyValue("--bg")]')
    assert palette_bg[1] == '#3a1b19', palette_bg
    assert page.locator('.primary').evaluate('(e) => getComputedStyle(e).backgroundColor') == 'rgb(201, 71, 55)'
    assert page.locator('.browser-art').evaluate('(e) => getComputedStyle(e).backgroundColor') == 'rgb(41, 27, 27)'
    assert page.locator('html').evaluate('(e) => getComputedStyle(e).getPropertyValue("--number-level-5").trim()') == '#7b595e'
    page.get_by_role('button', name='切换浅色主题').click()
    assert page.locator('html').get_attribute('data-theme') == 'light'
    page.wait_for_timeout(350)
    assert page.locator('body').evaluate('(e) => getComputedStyle(e).backgroundColor') == 'rgb(252, 240, 225)'
    assert page.locator('html').evaluate('(e) => getComputedStyle(e).getPropertyValue("--star-blue").trim()') == '#7b595e'
    assert page.locator('html').evaluate('(e) => getComputedStyle(e).getPropertyValue("--number-level-6").trim()') == '#a83d33'
    assert page.locator('meta[name="theme-color"]').get_attribute('content') == '#fcf0e1'
    page.reload(wait_until='networkidle')
    assert page.locator('html').get_attribute('data-theme') == 'light'
    assert page.locator('html').get_attribute('data-palette') == 'hutao-red'
    page.get_by_role('button', name='选择配色方案').click()
    page.get_by_role('button', name='芙芙蓝').click()
    assert page.locator('html').get_attribute('data-palette') == 'fufu-blue'
    page.wait_for_timeout(350)
    assert page.locator('body').evaluate('(e) => getComputedStyle(e).backgroundColor') == 'rgb(244, 246, 250)'
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
    page.set_viewport_size({'width':320, 'height':844})
    page.get_by_role('button', name='选择配色方案').click()
    palette_box = page.locator('.palette-popover').bounding_box()
    assert palette_box['x'] >= 0 and palette_box['x'] + palette_box['width'] <= 320, palette_box
    page.keyboard.press('Escape')
    page.locator('.palette-popover').wait_for(state='detached')
    page.set_viewport_size({'width':390, 'height':844})
    page.evaluate('window.scrollTo({top:0,behavior:"instant"})')
    page.get_by_role('button',name='打开菜单').click()
    assert page.locator('#mobile-nav').is_visible()
    page.locator('#mobile-nav a[href="#contact"]').click()
    page.locator('#mobile-nav').wait_for(state='detached')
    page.wait_for_timeout(800)
    assert page.url.endswith('#contact')
    assert page.locator('#contact h2').is_visible()
    page.get_by_role('button',name='打开菜单').click()
    page.keyboard.press('Escape')
    page.locator('#mobile-nav').wait_for(state='detached')
    page.evaluate('window.scrollTo({top:0,behavior:"instant"})')
    page.wait_for_timeout(400)
    page.screenshot(path=str(OUT / 'mobile.png'), full_page=True)
    results += ['320 / 390 / 768 / 1024 / 1440px: no horizontal overflow', 'Mobile menu, section navigation and Escape: passed']
    base_url = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:5173').rstrip('/')
    for route in ['/projects/rdp-access-auth', '/projects/gaze']:
        page.goto(base_url + route, wait_until='networkidle')
        assert page.locator('.palette-picker').count() == 1
        page.get_by_role('button', name='选择配色方案').click()
        page.get_by_role('button', name='胡桃红').click()
        assert page.locator('html').get_attribute('data-palette') == 'hutao-red'
        current_theme = page.locator('html').get_attribute('data-theme')
        page.get_by_role('button', name='切换浅色主题' if current_theme == 'dark' else '切换深色主题').click()
        assert page.locator('html').get_attribute('data-theme') != current_theme
        assert page.locator('html').get_attribute('data-palette') == 'hutao-red'
        page.wait_for_timeout(700)
        expected_action = 'rgb(201, 71, 55)' if page.locator('html').get_attribute('data-theme') == 'dark' else 'rgb(168, 61, 51)'
        selector = '.rdp-button.primary' if route.endswith('rdp-access-auth') else '.gaze-button.primary'
        action_colors = page.locator(selector).evaluate_all('(els) => els.map((e) => getComputedStyle(e).backgroundColor)')
        assert action_colors and all(color == expected_action for color in action_colors), action_colors
        if route.endswith('rdp-access-auth'):
            assert page.locator('.demo-submit').evaluate('(e) => getComputedStyle(e).backgroundColor') == expected_action
        page.get_by_role('button', name='选择配色方案').click()
        page.get_by_role('button', name='芙芙蓝').click()
        assert page.locator('html').get_attribute('data-palette') == 'fufu-blue'
        assert_cursor_palette(page, base_url, 'fufu-blue')
    results += ['RDP and Gaze navigation palette controls and shared theme state: passed']
    page.goto(base_url, wait_until='networkidle')
    context.grant_permissions([])
    page.evaluate('Object.defineProperty(navigator, "clipboard", {value: {writeText: () => Promise.reject(new Error("blocked"))}, configurable:true})')
    page.locator('.address-button').click()
    assert '请手动复制：play.mcyzw.top' in page.locator('[role=status]').inner_text()
    results += ['Clipboard failure fallback: passed']
    assert not errors, errors
    results += ['Browser JavaScript errors: none']
    print(json.dumps(results,ensure_ascii=False,indent=2))
    browser.close()
