"""Exercise real book assets, immersive reading, persistence and recovery."""
import json
import os
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:4173').rstrip('/')
books = json.loads(Path('src/books/library.json').read_text())
out = Path('artifacts/books')
out.mkdir(parents=True, exist_ok=True)
key = 'homepage-reading:' + books[0]['id']
settings_key = 'homepage-reader-settings'
bookmark_key = 'homepage-bookmarks:' + books[0]['id']

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, color_scheme='dark', reduced_motion='reduce')
    page = context.new_page()
    errors, downloads = [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('request', lambda r: downloads.append(r.url) if '/books/' in r.url and r.url.endswith('.json') else None)

    def ready():
        expect(page.locator('.reader-text-layout')).to_be_visible()
        page.wait_for_timeout(200)

    def stored(storage_key=key):
        return page.evaluate('(key) => JSON.parse(localStorage.getItem(key))', storage_key)

    def no_overflow():
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), page.viewport_size

    def scroll_paragraph(number, offset=.2):
        page.locator(f'[data-paragraph="{number}"]').evaluate('(e,offset)=>scrollTo({top:scrollY+e.getBoundingClientRect().top+e.offsetHeight*offset-88,behavior:"instant"})', offset)
        page.wait_for_timeout(250)
        assert stored()['paragraph'] == number, stored()

    def close_panel():
        page.get_by_role('button', name='关闭阅读面板').click()

    def open_panel(tab):
        name = {'toc': '章节目录', 'search': '全文搜索', 'bookmarks': '我的书签', 'info': '书籍简介'}[tab]
        if page.viewport_size['width'] <= 760:
            page.get_by_role('button', name='阅读工具', exact=True).click()
            if tab != 'toc':
                page.get_by_role('radiogroup', name='阅读面板').get_by_role('radio', name={'search': '搜索', 'bookmarks': '书签', 'info': '简介'}[tab], exact=True).click()
        else:
            page.get_by_role('button', name=name, exact=True).click()

    def change_setting(group, value):
        page.get_by_role('button', name='阅读设置', exact=True).click()
        page.get_by_role('radiogroup', name=group, exact=True).get_by_role('radio', name=value, exact=True).click()
        page.wait_for_timeout(220)
        close_panel()

    def page_state():
        return page.locator('.reader-viewport').evaluate('(e)=>({left:e.scrollLeft,width:e.clientWidth,total:e.scrollWidth})')

    def shelf_screenshot(path):
        for img in page.locator('.book-cover img').all():
            img.scroll_into_view_if_needed()
            expect(img).to_have_js_property('complete', True)
            assert img.evaluate('(e)=>e.naturalWidth > 0')
        page.evaluate('scrollTo({top:0,behavior:"instant"})')
        page.screenshot(path=str(path), full_page=True)

    page.goto(base + '/book', wait_until='networkidle')
    expect(page.locator('.book-card')).to_have_count(len(books))
    assert not downloads, 'Shelf fetched novel text eagerly'
    page.evaluate('window.booksHeader = document.querySelector(".header")')
    search = page.get_by_role('searchbox', name='搜索小说', exact=True)
    search.fill('一颗小花芽')
    expect(page.locator('.book-card')).to_have_count(2)
    search.fill('与教父同行')
    expect(page.locator('.book-card')).to_have_count(1)
    search.fill('不存在xyz')
    expect(page.get_by_text('这里暂时还没有书')).to_be_visible()
    page.get_by_role('button', name='查看全部小说').click()
    page.get_by_role('radio', name='在读', exact=True).click()
    expect(page.locator('.book-card')).to_have_count(0)
    page.get_by_role('radio', name='未读', exact=True).click()
    expect(page.locator('.book-card')).to_have_count(7)
    page.get_by_role('radio', name='全部', exact=True).click()
    page.get_by_role('button', name='列表视图').click()
    expect(page.locator('.library-grid')).to_have_class('library-grid is-list')
    page.get_by_role('combobox', name='书架排序').select_option('title')
    assert page.locator('.book-card h2').all_text_contents() != [b['title'] for b in books]
    page.get_by_role('combobox', name='书架排序').select_option('collection')
    page.get_by_role('button', name='卡片视图').click()
    # Physical clicks on every visible part, including padding, reach one details button.
    card = page.locator('.book-card').first
    for layout in ['列表视图', '卡片视图']:
        page.get_by_role('button', name=layout, exact=True).click()
        card.scroll_into_view_if_needed()
        expect(card.get_by_role('button', name='书籍简介', exact=True)).to_have_count(0)
        for selector in ['.book-card-cover', 'h2', '.book-author', '.book-description', '.book-alias', '.book-category', None]:
            box = card.locator(selector).bounding_box() if selector else card.bounding_box()
            x = box['x'] + (box['width'] / 2 if selector else 24)
            y = box['y'] + (box['height'] / 2 if selector else box['height'] - 16)
            page.mouse.click(x, y)
            expect(page.locator('.book-details')).to_be_visible()
            expect(page.locator('.book-details-synopsis')).to_contain_text('在哈利的11岁暑假，教父从天而降。')
            assert page.url.endswith('/book')
            page.keyboard.press('Escape')
            expect(card.locator('.book-card-details')).to_be_focused()
        link_box = card.locator('.book-card-bottom a').bounding_box()
        card_box = card.bounding_box()
        assert link_box['x'] + link_box['width'] > card_box['x'] + card_box['width'] - 35
    # One keyboard details stop per card; both native activation keys work.
    expect(card.get_by_role('button')).to_have_count(1)
    for keypress in ['Enter', 'Space']:
        card.locator('.book-card-details').focus()
        page.keyboard.press(keypress)
        expect(page.locator('.book-details-synopsis')).to_be_visible()
        page.keyboard.press('Escape')
        expect(card.locator('.book-card-details')).to_be_focused()
    assert all('-index.json' in url for url in downloads), downloads
    card.locator('.book-card-details').click()
    page.screenshot(path=str(out / 'book-details-desktop.png'))
    page.keyboard.press('Escape')
    # Touch gestures use the same full-card target, with the reading link as an exception.
    touch_context = browser.new_context(viewport={'width': 320, 'height': 844}, has_touch=True, reduced_motion='reduce')
    touch_page = touch_context.new_page()
    touch_page.on('pageerror', lambda error: errors.append(str(error)))
    for layout in ['卡片视图', '列表视图']:
        touch_page.goto(base + '/book', wait_until='networkidle')
        touch_page.get_by_role('button', name=layout, exact=True).tap()
        touch_card = touch_page.locator('.book-card').first
        touch_card.scroll_into_view_if_needed()
        for selector in ['.book-card-cover', '.book-description', None]:
            box = touch_card.locator(selector).bounding_box() if selector else touch_card.bounding_box()
            touch_page.touchscreen.tap(box['x'] + (box['width'] / 2 if selector else 24), box['y'] + (box['height'] / 2 if selector else box['height'] - 16))
            expect(touch_page.locator('.book-details')).to_be_visible()
            expect(touch_page.locator('#book-details-title')).to_have_text(books[0]['title'])
            touch_page.get_by_role('button', name='关闭书籍详情', exact=True).tap()
        touch_card.locator('.book-card-bottom a').tap()
        expect(touch_page.locator('.reader-text-layout')).to_be_visible()
        expect(touch_page.locator('.book-details[open]')).to_have_count(0)
    touch_context.close()
    page.locator('.book-card-bottom a').first.click()
    ready()
    assert len(set(downloads)) == 2, downloads
    assert page.evaluate('booksHeader === document.querySelector(".header")')
    expect(page.locator('.header')).not_to_be_visible()
    scroll_paragraph(12)
    saved = stored()
    page.reload(wait_until='networkidle')
    ready()
    assert stored()['paragraph'] == saved['paragraph'], (saved, stored())
    assert abs(stored()['offset'] - saved['offset']) < .04
    page.get_by_role('button', name='阅读设置', exact=True).click()
    page.get_by_role('button', name='放大字号').click()
    page.wait_for_timeout(250)
    assert stored()['paragraph'] == 12, stored()
    page.get_by_role('button', name='米白', exact=True).click()
    page.wait_for_timeout(200)
    page.screenshot(path=str(out / 'reader-settings-desktop.png'))
    close_panel()
    change_setting('正文字体', '宋体')
    assert stored()['paragraph'] == 12, stored()
    page.reload(wait_until='networkidle')
    ready()
    assert stored(settings_key)['fontSize'] == 22
    assert stored(settings_key)['font'] == 'serif'
    expect(page.locator('.reader-root')).to_have_attribute('data-reading-theme', 'paper')
    page.get_by_role('button', name='为当前位置添加书签').click()
    assert len(stored(bookmark_key)) == 1
    open_panel('bookmarks')
    expect(page.locator('.reader-bookmark')).to_have_count(1)
    close_panel()
    scroll_paragraph(20)
    open_panel('bookmarks')
    page.locator('.reader-bookmark a').click()
    ready()
    assert stored()['paragraph'] == 12, stored()
    scroll_paragraph(16)
    page.reload(wait_until='networkidle')
    ready()
    assert stored()['paragraph'] == 16
    scroll_paragraph(12)
    open_panel('bookmarks')
    page.get_by_role('button', name='删除书签：', exact=False).click()
    expect(page.locator('.reader-bookmark')).to_have_count(0)
    close_panel()
    assert stored(bookmark_key) == []
    page.locator('.reader-back').click()
    expect(page.locator('.library-continue')).to_contain_text(books[0]['title'])
    page.get_by_role('radio', name='在读', exact=True).click()
    expect(page.locator('.book-card')).to_have_count(1)
    page.locator('.library-continue a').click()
    ready()
    assert stored()['paragraph'] == 12
    open_panel('info')
    expect(page.locator('.reader-synopsis')).to_contain_text('在哈利的11岁暑假，教父从天而降。')
    close_panel()

    # Search uses literal text and explicit submission; a result navigates to its paragraph.
    open_panel('search')
    before = len(downloads)
    page.get_by_role('searchbox', name='搜索小说正文').fill('邓布利多')
    page.wait_for_timeout(100)
    assert len(downloads) == before
    page.locator('.reader-full-search').get_by_role('button', name='搜索', exact=True).click()
    expect(page.locator('.reader-search-results a').first).to_be_visible(timeout=30000)
    expect(page.locator('.reader-search-results mark').first).to_have_text('邓布利多')
    result = page.locator('.reader-search-results a').nth(2)
    href = result.get_attribute('href')
    result.click()
    ready()
    destination = parse_qs(urlparse(href).query)
    assert stored()['paragraph'] == int(destination['paragraph'][0]) - 1
    assert 'paragraph=' not in page.url
    expect(page.locator('.reader-paragraph mark').first).to_have_text('邓布利多')
    open_panel('search')
    page.get_by_role('searchbox', name='搜索小说正文').fill('[.*不存在')
    page.locator('.reader-full-search').get_by_role('button', name='搜索', exact=True).click()
    expect(page.get_by_text('找到 0 个段落', exact=True)).to_be_visible(timeout=30000)
    close_panel()

    # TOC, history restoration, immediate save on departure and browser isolation.
    open_panel('toc')
    expect(page.get_by_role('searchbox', name='搜索章节')).to_be_focused()
    page.keyboard.press('Escape')
    expect(page.locator('.reader-directory-button')).to_be_focused()
    open_panel('toc')
    page.get_by_role('searchbox', name='搜索章节').fill('chapter25')
    page.get_by_role('navigation', name='小说目录').get_by_role('link').first.click()
    ready()
    expect(page.locator('h1')).to_have_text('第25章 chapter25')
    expect(page.locator('#chapter-title')).to_be_focused()
    scroll_paragraph(8, 0)
    history_y = page.evaluate('scrollY')
    page.get_by_role('button', name='下一章', exact=True).click()
    ready()
    assert stored()['chapter'] == 25
    page.go_back()
    ready()
    assert stored()['chapter'] == 24
    page.wait_for_function('(y)=>Math.abs(scrollY-y)<3', arg=history_y)
    page.locator('.skip-link').focus()
    page.keyboard.press('Enter')
    expect(page.locator('main')).to_be_focused()
    page.locator('[data-paragraph="10"]').evaluate('(e)=>scrollTo({top:scrollY+e.getBoundingClientRect().top-88,behavior:"instant"})')
    page.locator('.reader-back').click()
    expect(page.locator('.book-card')).to_have_count(7)
    assert stored()['paragraph'] == 10, stored()
    first_saved = stored().copy()
    page.locator('.book-card-bottom a').nth(1).click()
    ready()
    assert stored() == first_saved
    returning = browser.new_context(storage_state=context.storage_state(), viewport={'width': 390, 'height': 844}, reduced_motion='reduce')
    returning_page = returning.new_page()
    returning_page.goto(base + '/books/' + books[0]['id'], wait_until='networkidle')
    returning_page.wait_for_timeout(300)
    resumed = returning_page.evaluate('(key)=>JSON.parse(localStorage.getItem(key))', key)
    assert resumed['paragraph'] == 10, resumed
    returning.close()
    fresh = browser.new_context(reduced_motion='reduce')
    fresh_page = fresh.new_page()
    fresh_page.goto(base + '/books/' + books[0]['id'], wait_until='networkidle')
    expect(fresh_page.locator('h1')).to_have_text('第1章 chapter01')
    fresh.close()

    # True column pagination: every paragraph fragment is reachable, reflow keeps location.
    page.goto(base + '/books/' + books[0]['id'] + '?chapter=1&paragraph=1', wait_until='networkidle')
    ready()
    page.get_by_role('button', name='阅读设置', exact=True).click()
    page.get_by_role('button', name='恢复默认设置').click()
    page.wait_for_timeout(200)
    close_panel()
    change_setting('阅读方式', '左右翻页')
    visited = set()
    states = []
    while True:
        state = page_state()
        states.append(state['left'])
        fragments = page.locator('.reader-viewport').evaluate('''(e)=>{
          const bounds=e.getBoundingClientRect();
          return [...e.querySelectorAll('[data-paragraph]')].flatMap(p=>[...p.getClientRects()].flatMap((r,i)=>r.left>=bounds.left-2 && r.right<=bounds.right+2 ? [p.dataset.paragraph+':'+i] : []));
        }''')
        visited.update(fragments)
        if state['left'] + state['width'] >= state['total'] - 2:
            break
        page.get_by_role('button', name='下一页', exact=True).click()
        page.wait_for_timeout(30)
        assert len(states) < 100
    total = page.locator('.reader-paragraph').evaluate_all('(es)=>es.reduce((n,e)=>n+e.getClientRects().length,0)')
    assert len(visited) == total, (len(visited), total)
    assert len(states) > 2
    page.get_by_role('button', name='下一页', exact=True).click()
    ready()
    assert stored()['chapter'] == 1
    page.go_back()
    ready()
    assert page_state()['left'] == states[-1], 'History lost the paginated reading position'
    page.go_forward()
    ready()
    assert stored()['chapter'] == 1
    page.get_by_role('button', name='上一页', exact=True).click()
    ready()
    assert stored()['chapter'] == 0
    assert page_state()['left'] == states[-1]
    page.get_by_role('button', name='上一页', exact=True).click()
    saved = stored()
    page.reload(wait_until='networkidle')
    ready()
    assert stored()['paragraph'] == saved['paragraph'], (stored(), saved)
    page.set_viewport_size({'width': 390, 'height': 844})
    page.wait_for_timeout(400)
    current = stored()
    # A narrower page may start earlier within the same paragraph, but must still show it.
    assert current['paragraph'] <= saved['paragraph'], (current, saved)
    node = page.locator(f'[data-paragraph="{saved["paragraph"]}"]')
    assert node.evaluate('(e)=>[...e.getClientRects()].some(r=>r.right>18 && r.left<innerWidth-18)')
    page.screenshot(path=str(out / 'reader-pages-mobile.png'))
    state = page_state()
    cdp = context.new_cdp_session(page)
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': 315, 'y': 400}]})
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': 190, 'y': 405}]})
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
    page.wait_for_timeout(150)
    assert page_state()['left'] > state['left'], (state, page_state())
    page.get_by_role('button', name='专注阅读', exact=True).click()
    expect(page.locator('.reader-topbar')).not_to_be_visible()
    expect(page.get_by_role('button', name='退出专注')).to_be_focused()
    page.keyboard.press('ArrowLeft')
    page.keyboard.press('Escape')
    expect(page.get_by_role('button', name='专注阅读', exact=True)).to_be_focused()
    for _ in range(3):
        page.get_by_role('button', name='专注阅读', exact=True).click()
        expect(page.get_by_role('button', name='退出专注')).to_be_focused()
        page.keyboard.press('Escape')
        expect(page.get_by_role('button', name='专注阅读', exact=True)).to_be_focused()
    change_setting('阅读方式', '上下滚动')
    position = stored()
    page.reload(wait_until='networkidle')
    ready()
    assert stored()['paragraph'] == position['paragraph'], (stored(), position)

    # Every book's first and last section; completing the last section marks it read.
    for book in books:
        for number in [1, book['chapterCount']]:
            page.goto(f'{base}/books/{book["id"]}?chapter={number}', wait_until='networkidle')
            ready()
            assert stored('homepage-reading:' + book['id'])['chapter'] == number - 1
            assert page.locator('.reader-paragraph').count() > 0
        expect(page.locator('.reader-end')).to_be_attached()
    page.evaluate('scrollTo({top:document.documentElement.scrollHeight,behavior:"instant"})')
    page.wait_for_timeout(250)
    page.locator('.reader-back').click()
    page.get_by_role('radio', name='已读', exact=True).click()
    expect(page.locator('.book-card h2')).to_contain_text(['异案调查组'])

    # Missing resources and late results never overwrite the saved position.
    target = books[0]
    saved = stored()
    failed_pattern = f'**/books/{target["id"]}/{target["revision"]}-0.json'
    context.route(failed_pattern, lambda route: route.fulfill(status=503, body='unavailable'))
    page.goto(f'{base}/books/{target["id"]}?chapter=2', wait_until='networkidle')
    expect(page.get_by_role('button', name='重新加载', exact=True)).to_be_visible()
    assert stored() == saved
    context.unroute(failed_pattern)
    page.get_by_role('button', name='重新加载', exact=True).click()
    ready()
    expect(page.locator('h1')).to_have_text('第2章 chapter02')
    delayed = []
    pattern = f'**/books/{target["id"]}/{target["revision"]}-1.json'
    context.route(pattern, lambda route: delayed.append(route))
    page.goto(f'{base}/books/{target["id"]}?chapter=30', wait_until='domcontentloaded')
    expect(page.get_by_text('正在打开书页…', exact=True)).to_be_visible()
    page.locator('.reader-back').click()
    expect(page.locator('.book-card')).to_have_count(7)
    page.locator('.book-card-bottom a').nth(4).click()
    ready()
    for pending in delayed:
        try:
            pending.fulfill(path=f'public/books/{target["id"]}/{target["revision"]}-1.json', content_type='application/json')
        except Exception:
            pass
    context.unroute(pattern)
    expect(page.locator('.reader-identity')).to_contain_text(books[4]['title'])

    # Cancel a search while a later chunk is pending; late responses cannot add results.
    page.goto(f'{base}/books/{target["id"]}?chapter=1', wait_until='networkidle')
    ready()
    pending_search = []
    context.route(pattern, lambda route: pending_search.append(route))
    open_panel('search')
    page.get_by_role('searchbox', name='搜索小说正文').fill('不会存在的检索词xyz')
    page.locator('.reader-full-search').get_by_role('button', name='搜索', exact=True).click()
    expect(page.get_by_role('button', name='取消', exact=True)).to_be_visible()
    page.wait_for_timeout(100)
    page.get_by_role('button', name='取消', exact=True).click()
    page.get_by_role('searchbox', name='搜索小说正文').fill('新查询')
    for pending in pending_search:
        try:
            pending.fulfill(path=f'public/books/{target["id"]}/{target["revision"]}-1.json', content_type='application/json')
        except Exception:
            pass
    context.unroute(pattern)
    expect(page.locator('.reader-search-results a')).to_have_count(0)
    close_panel()
    page.evaluate('(key)=>localStorage.setItem(key,"{bad")', key)
    page.goto(base + '/books/' + target['id'] + '?chapter=999999', wait_until='networkidle')
    ready()
    expect(page.locator('h1')).to_have_text('第1章 chapter01')
    blocked = browser.new_context(reduced_motion='reduce')
    blocked.add_init_script('Storage.prototype.getItem = function(){throw Error("blocked")}; Storage.prototype.setItem = function(){throw Error("blocked")};')
    blocked_page = blocked.new_page()
    blocked_page.goto(base + '/books/' + target['id'], wait_until='networkidle')
    expect(blocked_page.locator('.reader-text-layout')).to_be_visible()
    expect(blocked_page.locator('.reader-storage-warning')).to_be_visible()
    blocked.close()

    # Fresh visual checks of shelf, full description, panels and reading at all required widths.
    for theme in ['dark', 'light']:
        for width in [320, 390, 768, 900, 901, 1024, 1440]:
            page.set_viewport_size({'width': width, 'height': 844})
            page.evaluate('(theme)=>{localStorage.setItem("homepage-theme",theme);localStorage.removeItem("homepage-reader-settings")}', theme)
            page.goto(base + '/book', wait_until='networkidle')
            no_overflow()
            if width <= 760:
                assert page.locator('.library-continue h2').bounding_box()['width'] >= 140, 'Continue card squeezed the book title'
            for layout in ['列表视图', '卡片视图']:
                page.get_by_role('button', name=layout, exact=True).click()
                for card in page.locator('.book-card').all():
                    if not card.locator('.book-card-progress').count():
                        continue
                    # Read both boxes in one frame while viewport scroll restoration may run.
                    bounds = card.evaluate('e=>({progress:e.querySelector(".book-card-progress").getBoundingClientRect().toJSON(),link:e.querySelector(".book-card-bottom a").getBoundingClientRect().toJSON(),track:e.querySelector(".book-progress-track").getBoundingClientRect().width})')
                    progress_box, link_box = bounds['progress'], bounds['link']
                    assert abs(progress_box['y'] + progress_box['height'] / 2 - link_box['y'] - link_box['height'] / 2) < 1, (width, layout, progress_box, link_box)
                    assert progress_box['x'] + progress_box['width'] <= link_box['x'], (width, layout)
                    assert bounds['track'] >= 16, (width, layout)
                no_overflow()
                if layout == '列表视图' and width in [320, 1440]:
                    page.locator('.book-card').first.screenshot(path=str(out / f'progress-list-{theme}-{width}.png'))
            if width in [390, 1440]:
                shelf_screenshot(out / f'shelf-{theme}-{width}.png')
            page.locator('.book-card-details').nth(3).click()
            expect(page.locator('.book-details-synopsis')).to_contain_text('芙宁娜')
            box = page.get_by_role('dialog').bounding_box()
            assert 0 <= box['x'] and box['x'] + box['width'] <= width
            assert 0 <= box['y'] and box['y'] + box['height'] <= 845
            page.keyboard.press('Escape')
            page.locator('.book-card-bottom a').nth(3).click()
            ready()
            no_overflow()
            if width in [390, 1440]:
                page.screenshot(path=str(out / f'reader-{theme}-{width}.png'))
            open_panel('toc')
            box = page.get_by_role('dialog').bounding_box()
            assert 0 <= box['x'] and box['x'] + box['width'] <= width
            assert 0 <= box['y'] and box['y'] + box['height'] <= 845
            expect(page.get_by_role('searchbox', name='搜索章节')).to_be_focused()
            page.get_by_role('radiogroup', name='阅读面板').get_by_role('radio', name='简介', exact=True).click()
            assert page.locator('.reader-synopsis').inner_text().strip()
            if width == 390:
                page.screenshot(path=str(out / f'reader-info-{theme}-mobile.png'))
            close_panel()
            page.get_by_role('button', name='阅读设置', exact=True).click()
            for paper in ['浅绿', '夜读', '跟随网站']:
                page.get_by_role('button', name=paper, exact=True).click()
            # Selected and keyboard focus rings must fit inside the scrolling region.
            for option in page.locator('.reader-paper-options button').all():
                option.focus()
                bounds = option.evaluate('e=>{const c=e.closest(".reader-settings"), r=e.getBoundingClientRect(), clip=c.getBoundingClientRect(), s=getComputedStyle(e), ring=parseFloat(s.outlineWidth)+Math.max(0,parseFloat(s.outlineOffset));return {left:r.left-ring,right:r.right+ring,clipLeft:clip.left,clipRight:clip.left+c.clientWidth,scroll:c.scrollLeft}}')
                assert bounds['left'] >= bounds['clipLeft'] - .5 and bounds['right'] <= bounds['clipRight'] + .5, (width, theme, bounds)
                assert bounds['scroll'] == 0, (width, theme, bounds)
            if width in [320, 1440]:
                page.locator('.reader-panel').screenshot(path=str(out / f'paper-options-{theme}-{width}.png'))
            page.get_by_role('button', name='恢复默认设置').click()
            close_panel()
    assert not errors, errors
    print('Books v2: library/details, all current chapter assets, progress/history/isolation, bookmarks, literal search/cancel, settings, column pagination/touch/focus, recovery and responsive themes passed.')
    browser.close()
