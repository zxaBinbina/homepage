"""Exercise real collection covers, volume selection, metadata and isolated progress."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:4173').rstrip('/')
books = {b['id']: b for b in json.loads(Path('src/books/library.json').read_text())}
collections = json.loads(Path('src/books/collections.json').read_text())
collection = next(c for c in collections if c['id'] == 'harry-potter')
volumes = [books[id] for id in collection['volumes']]
out = Path('artifacts/books')
out.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce', color_scheme='dark')
    page = context.new_page()
    errors, text_requests = [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('request', lambda r: text_requests.append(r.url) if '/books/' in r.url and r.url.endswith('.json') else None)
    card = page.locator('[data-book-id="harry-potter"]')
    dialog = page.locator('.book-collection-dialog')

    def ready():
        expect(page.locator('.reader-text-layout')).to_be_visible()
        page.wait_for_timeout(220)

    def stored(book):
        return page.evaluate('(key)=>JSON.parse(localStorage.getItem(key))', 'homepage-reading:' + book['id'])

    def choose():
        card.get_by_role('button', name='选择分册', exact=True).click()
        expect(dialog).to_be_visible()

    def no_overflow():
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert dialog.evaluate('e=>e.scrollWidth<=e.clientWidth')
        assert dialog.locator('.book-details-scroll').evaluate('e=>e.scrollWidth<=e.clientWidth')

    page.goto(base + '/book', wait_until='networkidle')
    expect(page.locator('.book-card')).to_have_count(10)
    expect(card).to_have_count(1)
    expect(page.locator('.library-heading')).to_contain_text('10 部 · 16 册')
    assert not text_requests, text_requests
    for book in volumes:
        expect(page.locator(f'.book-card[data-book-id="{book["id"]}"]')).to_have_count(0)
    search = page.get_by_role('searchbox', name='搜索小说', exact=True)
    for book in volumes:
        search.fill(book['title'])
        expect(page.locator('.book-card')).to_have_count(1)
        expect(card).to_be_visible()
    search.fill('马爱农')
    expect(card).to_be_visible()
    search.fill('')
    for key in ['Enter', 'Space']:
        card.locator('.book-card-details').focus()
        page.keyboard.press(key)
        expect(dialog).to_be_visible()
        expect(dialog.locator('.book-volume')).to_have_count(7)
        expect(dialog).to_contain_text('作者：J.K.罗琳')
        expect(dialog).to_contain_text('译者：苏农、马爱农和马爱新')
        assert dialog.locator('.book-volume').evaluate_all('(links)=>links.map(a=>a.getAttribute("href"))') == ['/books/' + b['id'] for b in volumes]
        page.keyboard.press('Escape')
        expect(card.locator('.book-card-details')).to_be_focused()
    choose()
    for image in dialog.locator('.book-volume img').all():
        image.scroll_into_view_if_needed()
        expect(image).to_have_js_property('complete', True)
        assert image.evaluate('e=>e.naturalWidth>0')
    assert not text_requests, 'Selecting a collection fetched chapter text before choosing a volume'
    dialog.get_by_role('button', name='关闭分册选择').click()
    expect(card.get_by_role('button', name='选择分册', exact=True)).to_be_focused()

    # Every volume is reachable from the same card and displays the supplied synopsis.
    first_saved = None
    for n, book in enumerate(volumes):
        choose()
        dialog.locator('.book-volume').nth(n).click()
        ready()
        assert page.url.endswith('/books/' + book['id'])
        index = json.loads(Path(f'public/books/{book["id"]}/{book["revision"]}-index.json').read_text())
        expect(page.locator('#chapter-title')).to_have_text(index['chapters'][0]['title'])
        page.get_by_role('button', name='书籍简介', exact=True).click()
        expect(page.locator('.reader-book-info')).to_contain_text('译者：苏农、马爱农和马爱新')
        assert page.locator('.reader-synopsis p').all_text_contents() == index['synopsis']
        expect(page.locator('.reader-source-link')).to_have_count(0)
        page.get_by_role('button', name='关闭阅读面板').click()
        page.locator('[data-paragraph="12"]').evaluate('e=>scrollTo({top:scrollY+e.getBoundingClientRect().top-87,behavior:"instant"})')
        page.wait_for_timeout(250)
        assert stored(book)['paragraph'] == 12, stored(book)
        if n == 0:
            page.get_by_role('button', name='为当前位置添加书签').click()
            page.reload(wait_until='networkidle')
            ready()
            assert stored(book)['paragraph'] == 12
        else:
            assert stored(volumes[0]) == first_saved
        page.locator('.reader-back').click()
        expect(card).to_be_visible()
        if n == 0:
            first_saved = stored(book).copy()
        expect(page.locator('.library-continue')).to_contain_text(book['title'])
    assert page.evaluate('localStorage.getItem("homepage-reading:harry-potter")') is None
    assert len(page.evaluate('(key)=>JSON.parse(localStorage.getItem(key))', 'homepage-bookmarks:' + volumes[0]['id'])) == 1
    assert page.evaluate('(key)=>localStorage.getItem(key)', 'homepage-bookmarks:' + volumes[1]['id']) is None
    page.get_by_role('combobox', name='书架排序').select_option('recent')
    expect(page.locator('.book-card').first).to_have_attribute('data-book-id', 'harry-potter')
    page.get_by_role('radio', name='在读', exact=True).click()
    expect(page.locator('.book-card')).to_have_count(1)
    page.get_by_role('radio', name='已读', exact=True).click()
    expect(page.locator('.book-card')).to_have_count(0)
    page.get_by_role('radio', name='全部', exact=True).click()

    # A single finished volume cannot mark all seven read; all seven can.
    for count in [1, 7]:
        page.evaluate('''volumes=>volumes.forEach((b,n)=>localStorage.setItem('homepage-reading:'+b.id,JSON.stringify({version:1,revision:b.revision,chapter:b.chapterCount-1,title:'最后一章',paragraph:0,offset:0,fraction:1,updatedAt:Date.now()+n})))''', volumes[:count])
        page.reload(wait_until='networkidle')
        page.get_by_role('radio', name='已读', exact=True).click()
        expect(card).to_have_count(0 if count == 1 else 1)
        page.get_by_role('radio', name='全部', exact=True).click()
    expect(card.locator('.book-card-progress')).to_contain_text('100%')

    for width in [320, 390, 768, 1024, 1440]:
        page.set_viewport_size({'width': width, 'height': 900})
        for theme in ['dark', 'light']:
            page.emulate_media(color_scheme=theme)
            for layout in ['卡片视图', '列表视图']:
                page.get_by_role('button', name=layout, exact=True).click()
                choose()
                no_overflow()
                for row in dialog.locator('.book-volume').all():
                    row.scroll_into_view_if_needed()
                    assert row.bounding_box()['height'] >= 44
                dialog.locator('.book-details-scroll').evaluate('e=>e.scrollTop=0')
                if width in [320, 1440] and layout == '卡片视图':
                    page.screenshot(path=str(out / f'hp-collection-{theme}-{width}.png'))
                dialog.get_by_role('button', name='关闭分册选择').click()
                expect(card.get_by_role('button', name='选择分册', exact=True)).to_be_focused()
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.emulate_media(reduced_motion='no-preference')
    choose()
    page.wait_for_timeout(250)
    dialog.get_by_role('button', name='关闭分册选择').click()
    page.wait_for_timeout(45)
    assert dialog.evaluate('e=>e.open&&e.getAnimations().length>0')
    expect(dialog).not_to_be_visible()
    expect(card.get_by_role('button', name='选择分册', exact=True)).to_be_focused()
    assert not errors, errors
    browser.close()
    print('Collections: one card/seven volumes, matching local covers, supplied synopsis/credits, independent progress/bookmarks, grouped search/status/sort, keyboard/focus/motion and responsive themes passed.')
