"""Check author-note folding against real source paragraphs and reading positions."""
import json
import os
import re
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:4173').rstrip('/')
books = {b['id']: b for b in json.loads(Path('src/books/library.json').read_text())}
out = Path('artifacts/books')
out.mkdir(parents=True, exist_ok=True)
settings_key = 'homepage-reader-settings'


def source(book_id, chapter):
    book = books[book_id]
    chunk = json.loads(Path(f"public/books/{book_id}/{book['revision']}-{chapter // book['chunkSize']}.json").read_text())
    return chunk[chapter % book['chunkSize']]


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, color_scheme='dark', reduced_motion='reduce')
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))

    def ready():
        expect(page.locator('.reader-text-layout')).to_be_visible()
        page.wait_for_timeout(220)

    def stored(book_id):
        return page.evaluate('(key)=>JSON.parse(localStorage.getItem(key))', 'homepage-reading:' + book_id)

    def scroll_to(number, book_id):
        page.locator(f'[data-paragraph="{number}"]').evaluate('(e)=>scrollTo({top:scrollY+e.getBoundingClientRect().top-87,behavior:"instant"})')
        page.wait_for_timeout(250)
        assert stored(book_id)['paragraph'] == number, stored(book_id)

    def open_panel(name):
        page.get_by_role('button', name=name, exact=True).click()

    def close_panel():
        page.get_by_role('button', name='关闭阅读面板').click()

    def page_numbers():
        return tuple(map(int, re.search(r'本章 (\d+) / (\d+) 页', page.locator('.reader-position').inner_text()).groups()))

    def visit(book_id, chapter, paragraph=None, mode='scroll', theme='site'):
        page.goto(base + '/book')
        page.evaluate('([key,mode,theme])=>{localStorage.clear();localStorage.setItem(key,JSON.stringify({mode,theme}))}', [settings_key, mode, theme])
        query = f'?chapter={chapter + 1}'
        if paragraph is not None:
            query += f'&paragraph={paragraph + 1}'
        page.goto(base + f'/books/{book_id}' + query, wait_until='networkidle')
        ready()
        # Even hidden comments remain byte-for-byte identical in the DOM.
        rendered = page.locator('[data-paragraph]').evaluate_all('(nodes)=>nodes.map(n=>[Number(n.dataset.paragraph),n.textContent])')
        assert rendered == list(map(list, enumerate(source(book_id, chapter)))), (book_id, chapter, rendered[:2])

    visit('furina-at-hogwarts', 15)
    note = page.locator('[data-note-start="23"]')
    expect(note).not_to_have_attribute('open', '')
    expect(note.locator('[data-paragraph="24"]')).not_to_be_visible()
    expect(page.locator('[data-paragraph="22"]')).to_be_visible()
    summary = note.locator('summary')
    summary.click()
    expect(note.locator('[data-paragraph="24"]')).to_be_visible()
    expect(summary).to_have_attribute('aria-expanded', 'true')
    summary.focus()
    page.keyboard.press('Space')
    expect(note.locator('[data-paragraph="24"]')).not_to_be_visible()
    page.keyboard.press('Enter')
    expect(note.locator('[data-paragraph="24"]')).to_be_visible()
    page.screenshot(path=str(out / 'author-note-dark-desktop.png'))

    # Full-text search still includes hidden notes, and selecting a result opens it.
    summary.click()
    open_panel('全文搜索')
    page.get_by_role('searchbox', name='搜索小说正文').fill('清明节快乐')
    page.locator('.reader-full-search').get_by_role('button', name='搜索', exact=True).click()
    result = page.locator('.reader-search-results a').filter(has_text='清明节快乐')
    expect(result).to_have_count(1, timeout=30000)
    assert 'paragraph=25' in result.get_attribute('href')
    result.click()
    ready()
    expect(page.locator('[data-note-start="23"] [data-paragraph="24"]')).to_be_visible()
    expect(page.locator('[data-paragraph="24"] mark')).to_have_text('清明节快乐')
    expect(page.locator('[data-paragraph="24"]')).to_be_focused()

    # Source indices stay stable before, within and after a middle-chapter note.
    bid = 'backroons-escape'
    visit(bid, 130, 100)
    note = page.locator('[data-note-start="82"]')
    expect(note).to_have_attribute('open', '')
    scroll_to(100, bid)
    saved = stored(bid)
    page.get_by_role('button', name='为当前位置添加书签').click()
    bookmark = page.evaluate('(key)=>JSON.parse(localStorage.getItem(key))', 'homepage-bookmarks:' + bid)[0]
    assert bookmark['paragraph'] == 100
    assert bookmark['excerpt'] in source(bid, 130)[100]
    page.reload(wait_until='networkidle')
    ready()
    expect(page.locator('[data-note-start="82"]')).to_have_attribute('open', '')
    assert stored(bid)['paragraph'] == saved['paragraph']
    page.locator('[data-note-start="82"] summary').click()
    page.wait_for_timeout(400)
    open_panel('我的书签')
    page.locator('.reader-bookmark a').click()
    ready()
    expect(page.locator('[data-note-start="82"]')).to_have_attribute('open', '')
    expect(page.locator('[data-paragraph="100"]')).to_be_focused()
    assert stored(bid)['paragraph'] == 100
    page.get_by_role('button', name='下一章', exact=True).click()
    ready()
    page.go_back()
    ready()
    expect(page.locator('[data-note-start="82"]')).to_have_attribute('open', '')
    assert stored(bid)['paragraph'] == 100

    # Beginning/middle annotations do not shift later paragraph numbers or fold guides.
    visit('furina-at-hogwarts', 0)
    expect(page.locator('[data-paragraph="0"]')).not_to_be_visible()
    scroll_to(12, 'furina-at-hogwarts')
    visit(bid, 135)
    scroll_to(70, bid)
    expect(page.locator('[data-paragraph="65"]')).not_to_be_visible()
    expect(page.locator('[data-paragraph="67"]')).to_be_visible()
    visit('sirius-and-harry', 135)
    expect(page.locator('[data-paragraph="47"]')).to_be_visible()
    expect(page.locator('[data-paragraph="48"]')).not_to_be_visible()
    visit('hidden-professor', 643)
    expect(page.locator('[data-note-start="0"]')).to_have_attribute('open', '')
    visit('anomaly-investigations', 0)
    expect(page.locator('.reader-author-note')).to_have_count(0)
    visit('tom-at-hogwarts', 97)
    expect(page.locator('[data-paragraph="10"] .reader-inline-note')).to_contain_text('此神奇动物是作者编的')

    # Native opening (browser Find) updates the visible state and accessibility label.
    visit('furina-at-hogwarts', 15)
    note = page.locator('[data-note-start="23"]')
    note.evaluate('(e)=>e.open=true')
    expect(note.locator('summary')).to_have_attribute('aria-expanded', 'true')
    expect(note.locator('[data-paragraph="24"]')).to_be_visible()

    # Repeated reversals and leaving during an animation must not disable progress saving.
    page.emulate_media(reduced_motion='no-preference')
    visit('furina-at-hogwarts', 0)
    summary = page.locator('[data-note-start="0"] summary')
    summary.click()
    page.wait_for_timeout(70)
    height = page.locator('[data-note-start="0"] .collapse-panel').evaluate('(e)=>e.getBoundingClientRect().height')
    assert height > 0
    page.screenshot(path=str(out / 'author-note-opening.png'))
    summary.click()
    summary.click()
    page.wait_for_timeout(420)
    expect(summary).to_have_attribute('aria-expanded', 'true')
    # Two activation events in one frame exercise cancellation before opening starts.
    summary.evaluate('(e)=>{e.click();e.click();e.click()}')
    page.wait_for_timeout(420)
    expect(summary).to_have_attribute('aria-expanded', 'false')
    scroll_to(12, 'furina-at-hogwarts')
    summary.click()
    page.get_by_role('button', name='下一章', exact=True).click()
    ready()
    scroll_to(12, 'furina-at-hogwarts')
    page.emulate_media(reduced_motion='reduce')

    # Long author Q&A must fragment into columns instead of overflowing vertically.
    for width in [320, 1440]:
        page.set_viewport_size({'width': width, 'height': 900})
        visit('backroons-escape', 130, 100, mode='pages')
        note = page.locator('[data-note-start="82"]')
        expect(note).to_have_attribute('open', '')
        bounds = page.locator('.reader-viewport').bounding_box()
        fragments = note.locator('[data-paragraph]').evaluate_all('(nodes)=>nodes.flatMap(n=>Array.from(n.getClientRects(),r=>({paragraph:n.dataset.paragraph,top:r.top,bottom:r.bottom,left:r.left,right:r.right})))')
        assert all(r['top'] >= bounds['y'] - 1 and r['bottom'] <= bounds['y'] + bounds['height'] + 1 for r in fragments), (width, bounds, fragments[:3], fragments[-3:])
        page.screenshot(path=str(out / f'author-note-pages-{width}.png'))
        expected = note.locator('[data-paragraph]').evaluate_all('(nodes)=>nodes.flatMap(n=>Array.from(n.getClientRects(),(_,i)=>n.dataset.paragraph+":"+i))')
        while page_numbers()[0] > 1:
            page.get_by_role('button', name='上一页', exact=True).click()
        visited = set()
        total = page_numbers()[1]
        assert 1 < total < 150
        while True:
            visible = note.evaluate('''e=>{const b=e.closest('.reader-viewport').getBoundingClientRect();return [...e.querySelectorAll('[data-paragraph]')].flatMap(n=>[...n.getClientRects()].flatMap((r,i)=>r.left>=b.left-1&&r.right<=b.right+1?[n.dataset.paragraph+':'+i]:[]))}''')
            visited.update(visible)
            if page_numbers()[0] == total:
                break
            page.get_by_role('button', name='下一页', exact=True).click()
        assert visited == set(expected), (width, set(expected) - visited)
        summary = note.locator('summary')
        summary.click()
        page.wait_for_timeout(240)
        expect(note.locator('[data-paragraph="100"]')).not_to_be_visible()
        assert page_numbers()[1] < total
        summary.focus()
        before = page_numbers()[0]
        page.keyboard.press('Space')
        page.wait_for_timeout(240)
        expect(note.locator('[data-paragraph="100"]')).to_be_visible()
        assert page_numbers()[1] == total
        assert page_numbers()[0] == before
        # Restoring a paragraph inside an expanded long note reaches the same page.
        page.goto(base + f'/books/{bid}?chapter=131&paragraph=101', wait_until='networkidle')
        ready()
        saved = stored(bid)
        page.reload(wait_until='networkidle')
        ready()
        expect(page.locator('[data-note-start="82"]')).to_have_attribute('open', '')
        assert stored(bid)['paragraph'] == saved['paragraph'], (width, saved, stored(bid))

    # The disclosure and inline annotations fit every supported width and paper theme.
    for width in [320, 390, 768, 1024, 1440]:
        page.set_viewport_size({'width': width, 'height': 900})
        for theme in ['dark', 'light']:
            page.emulate_media(color_scheme=theme)
            for paper in ['site', 'paper', 'green', 'night']:
                visit('furina-at-hogwarts', 15, theme=paper)
                summary = page.locator('[data-note-start="23"] summary')
                summary.click()
                expect(page.locator('[data-paragraph="24"]')).to_be_visible()
                assert summary.bounding_box()['height'] >= 44
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, theme, paper)
                if width in [320, 1440] and paper in ['site', 'paper']:
                    page.screenshot(path=str(out / f'author-note-{theme}-{paper}-{width}.png'))
        visit('tom-at-hogwarts', 97)
        annotation = page.locator('[data-paragraph="10"] .reader-inline-note')
        annotation.scroll_into_view_if_needed()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        if width == 320:
            page.screenshot(path=str(out / 'author-note-inline-mobile.png'))
    assert not errors, errors
    browser.close()
    print('Author notes: exact text, default folding, search/bookmark/progress/history restoration, keyboard/native opening, rapid reversals, long-page reachability and responsive paper themes passed.')
