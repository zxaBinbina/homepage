"""Verify collection previews with real mouse and touch input through the card button."""
import json
import os
from pathlib import Path
from playwright.sync_api import expect, sync_playwright

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:4173').rstrip('/')
books = {book['id']: book for book in json.loads(Path('src/books/library.json').read_text())}
collection = next(c for c in json.loads(Path('src/books/collections.json').read_text()) if c['id'] == 'harry-potter')
covers = [books[id]['cover'] for id in collection['volumes']]
out = Path('artifacts/books')
out.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='no-preference', color_scheme='dark')
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))

    def shelf(target):
        target.goto(base + '/book', wait_until='networkidle')
        target.get_by_role('searchbox', name='搜索小说', exact=True).fill('哈利波特（分册）')
        card = target.locator('[data-book-id="harry-potter"]')
        expect(card).to_be_visible()
        expect(card.locator('.book-alias')).to_have_count(0)
        card.scroll_into_view_if_needed()
        target.wait_for_function('Array.from(document.querySelectorAll(".book-collection-cover img")).every(img=>img.complete&&img.naturalWidth>0)')
        assert card.locator('img').evaluate_all('images=>images.map(img=>img.getAttribute("src"))') == covers
        return card

    def front(target, source, selector='[data-book-id="harry-potter"] .book-collection-cover'):
        target.wait_for_function('''({source,selector})=>Array.from(document.querySelector(selector).children).some(cover=>getComputedStyle(cover).zIndex==='7'&&cover.querySelector('img').getAttribute('src')===source)''', arg={'source':source,'selector':selector}, timeout=2200)

    def point(card):
        bounds = card.locator('.book-card-cover').bounding_box()
        return {'x': bounds['x'] + bounds['width'] / 2, 'y': bounds['y'] + bounds['height'] / 2}

    card = shelf(page)
    pos = point(card)
    page.mouse.move(pos['x'], pos['y'])
    for index in list(range(1, 7)) + [0]:
        front(page, covers[index])
        assert card.locator('.book-collection-cover').evaluate('e=>e.getAnimations({subtree:true}).some(a=>a.playState==="running")'), 'No cover transition'
        if index == 2:
            page.wait_for_timeout(380)
            card.screenshot(path=str(out / 'hp-stack-preview-dark-1440.png'))
    page.mouse.move(card.bounding_box()['x'] + card.bounding_box()['width'] - 12, pos['y'])
    front(page, covers[0])
    page.wait_for_timeout(1350)
    front(page, covers[0])

    page.mouse.move(pos['x'], pos['y'])
    front(page, covers[1])
    page.emulate_media(reduced_motion='reduce')
    front(page, covers[0])
    page.wait_for_timeout(1350)
    front(page, covers[0])
    durations = card.locator('.book-cover').first.evaluate('e=>getComputedStyle(e).transitionDuration')
    assert all(float(duration.removesuffix('s')) <= .001 for duration in durations.split(',')), durations
    page.emulate_media(reduced_motion='no-preference')
    page.mouse.move(0, 0)

    for width in [320, 390, 768, 1024, 1440]:
        page.set_viewport_size({'width': width, 'height': 900})
        for theme in ['dark', 'light']:
            page.emulate_media(color_scheme=theme)
            for layout, name in [('cards', '卡片视图'), ('list', '列表视图')]:
                page.get_by_role('button', name=name, exact=True).click()
                page.mouse.move(0, 0)
                card.scroll_into_view_if_needed()
                page.wait_for_timeout(380)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                assert card.locator('.book-collection-cover').evaluate('''e=>{const frame=e.getBoundingClientRect();return Array.from(e.children).every(cover=>{const b=cover.getBoundingClientRect();return b.left>=frame.left-.5&&b.right<=frame.right+.5&&b.top>=frame.top-.5&&b.bottom<=frame.bottom+.5})}'''), (width, theme, layout)
                if width in [320, 390, 1440]:
                    card.screenshot(path=str(out / f'hp-stack-{theme}-{width}-{layout}.png'))

    page.set_viewport_size({'width': 1440, 'height': 900})
    page.get_by_role('button', name='卡片视图', exact=True).click()
    card.scroll_into_view_if_needed()
    pos = point(card)
    page.mouse.click(pos['x'], pos['y'])
    dialog = page.locator('.book-collection-dialog')
    expect(dialog).to_be_visible()
    dialog_cover = dialog.locator('.book-collection-cover')
    expect(dialog_cover.locator('img')).to_have_count(7)
    assert dialog_cover.locator('img').evaluate_all('images=>images.map(img=>img.getAttribute("src"))') == covers
    dialog_cover.hover(force=True)
    front(page, covers[1], '.book-collection-dialog .book-collection-cover')
    page.wait_for_timeout(380)
    dialog.screenshot(path=str(out / 'hp-stack-dialog-preview-dark-1440.png'))
    page.keyboard.press('Escape')
    expect(dialog).not_to_be_visible()
    expect(card.locator('.book-card-details')).to_be_focused()
    front(page, covers[0], '.book-collection-dialog .book-collection-cover')
    page.mouse.move(0, 0)
    page.mouse.move(pos['x'], pos['y'])
    front(page, covers[1])
    page.locator('.header').get_by_role('link', name='首页', exact=True).first.click()
    expect(page.locator('.book-collection-cover')).to_have_count(0)
    page.wait_for_timeout(1300)
    card = shelf(page)
    front(page, covers[0])

    touch_context = browser.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True, reduced_motion='no-preference')
    touch = touch_context.new_page()
    touch.on('pageerror', lambda error: errors.append(str(error)))
    card = shelf(touch)
    cdp = touch_context.new_cdp_session(touch)
    pos = point(card)
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{**pos, 'id': 1}]})
    front(touch, covers[1])
    touch.wait_for_timeout(380)
    card.screenshot(path=str(out / 'hp-stack-preview-touch-390.png'))
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
    front(touch, covers[0])
    expect(touch.locator('.book-collection-dialog')).not_to_be_visible()
    touch.wait_for_timeout(1400)
    front(touch, covers[0])
    touch.touchscreen.tap(pos['x'], pos['y'])
    expect(touch.locator('.book-collection-dialog')).to_be_visible()
    touch.get_by_role('button', name='关闭分册选择', exact=True).tap()
    expect(touch.locator('.book-collection-dialog')).not_to_be_visible()

    card.scroll_into_view_if_needed()
    pos = point(card)
    scroll_before = touch.evaluate('scrollY')
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{**pos, 'id': 2}]})
    touch.wait_for_timeout(60)
    for distance in [20, 45, 80]:
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': pos['x'], 'y': pos['y'] - distance, 'id': 2}]})
        touch.wait_for_timeout(50)
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
    touch.wait_for_timeout(1400)
    front(touch, covers[0])
    assert touch.evaluate('scrollY') > scroll_before, 'Cover prevented native touch scrolling'
    expect(touch.locator('.book-collection-dialog')).not_to_be_visible()
    assert not errors, errors
    browser.close()
    print('Cover preview passed: seven ordered covers and wraparound, hover/leave, transition/reduced motion, real touch hold/release/tap/scroll, alias search, native card focus, navigation cleanup and responsive themes/layouts.')
