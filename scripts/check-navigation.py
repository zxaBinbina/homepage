"""Verify same-origin navigation on the dev or production preview server."""
import io
import os
import wave
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:5173').rstrip('/')
audio = io.BytesIO()
with wave.open(audio, 'wb') as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(8000)
    wav.writeframes(b'\0\0' * 8000 * 60)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
    context.route('**/song/media/**', lambda route: route.fulfill(body=audio.getvalue(), content_type='audio/wav'))
    context.route('**/api/music/lyrics?*', lambda route: route.fulfill(json={'lines': [], 'instrumental': True}))
    page = context.new_page()
    errors, documents = [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('request', lambda request: documents.append(request.url) if request.resource_type == 'document' else None)
    page.goto(base + '/', wait_until='networkidle')
    page.evaluate('window.navigationProbe = {header: document.querySelector(".header")}')

    def intact():
        assert page.evaluate('!!window.navigationProbe'), 'The document was replaced'
        assert len(documents) == 1, documents

    def metadata(path, project=False):
        title = page.title()
        expect(page.locator('meta[property="og:title"]')).to_have_attribute('content', title)
        expect(page.locator('meta[itemprop="name"]')).to_have_attribute('content', title)
        description = page.locator('meta[name="description"]').get_attribute('content')
        expect(page.locator('meta[property="og:description"]')).to_have_attribute('content', description)
        expect(page.locator('link[rel="canonical"]')).to_have_attribute('href', 'https://zxabinbina.cc.cd' + path)
        expect(page.locator('meta[property="og:url"]')).to_have_attribute('content', 'https://zxabinbina.cc.cd' + path)
        structured = page.locator('#site-structured-data').evaluate('(el) => JSON.parse(el.textContent)')
        assert structured['@graph'][1]['url'] == 'https://zxabinbina.cc.cd' + path
        assert structured['@graph'][1]['name'] == title
        image = 'https://zxabinbina.cc.cd/images/' + ('rdp-access-auth.png' if project else 'share-avatar.jpg')
        for selector in ['meta[property="og:image"]', 'meta[property="og:image:secure_url"]', 'meta[itemprop="image"]']:
            expect(page.locator(selector)).to_have_attribute('content', image)
        expect(page.locator('meta[property="og:image:type"]')).to_have_attribute('content', 'image/png' if project else 'image/jpeg')
        expect(page.locator('meta[property="og:image:width"]')).to_have_attribute('content', '512' if project else '256')
        expect(page.locator('meta[property="og:image:height"]')).to_have_attribute('content', '394' if project else '256')
        assert structured['@graph'][1]['primaryImageOfPage']['url'] == image
        expect(page.locator('link[rel="icon"]')).to_have_attribute('href', '/images/rdp-access-auth.png' if project else '/favicon.svg')
        assert page.locator('body').evaluate('(el) => el.classList.contains("rdp-site")') == project
        assert page.evaluate('location.pathname === "/" || !location.pathname.endsWith("/")')
        assert page.locator('a[href]').evaluate_all('''links => links.every(link => {
            const url = new URL(link.href);
            return url.origin !== location.origin || url.pathname === '/' || !url.pathname.endsWith('/');
        })''')
        intact()

    page.get_by_role('button', name='打开网易云音乐播放器').click()
    page.wait_for_function('document.querySelector("audio")?.currentTime > 0')
    page.evaluate('window.navigationProbe.audio = document.querySelector("audio")')
    page.get_by_role('button', name='关闭音乐播放器').click()
    page.get_by_role('navigation', name='主导航', exact=True).get_by_role('link', name='项目', exact=True).click()
    expect(page.locator('.project-card')).to_have_count(9)
    expect(page).to_have_title('项目目录 · a彬彬a')
    metadata('/project')
    assert page.evaluate('window.navigationProbe.header === document.querySelector(".header")')
    assert page.evaluate('window.navigationProbe.audio === document.querySelector("audio") && !document.querySelector("audio").paused')
    page.wait_for_function('document.activeElement === document.querySelector("main")')
    page.wait_for_function('scrollY === 0')

    page.get_by_role('navigation', name='主导航', exact=True).get_by_role('link', name='工具', exact=True).click()
    expect(page.locator('.tool-card')).to_have_count(12)
    metadata('/tool')
    page.locator('.tool-card[href="/tools/json"]').click()
    expect(page.locator('.tool-main')).to_be_visible()
    metadata('/tools/json')
    page.get_by_role('link', name='全部工具', exact=True).click()
    expect(page.locator('.tool-card')).to_have_count(12)
    page.locator('.tool-card[href="/tools/color"]').click()
    expect(page.locator('.tool-main h1')).to_have_text('颜色转换')
    metadata('/tools/color')
    assert page.evaluate('window.navigationProbe.header === document.querySelector(".header")')
    assert page.evaluate('window.navigationProbe.audio === document.querySelector("audio") && !document.querySelector("audio").paused')
    page.get_by_role('navigation', name='主导航', exact=True).get_by_role('link', name='项目', exact=True).click()
    expect(page.locator('.project-card')).to_have_count(9)

    page.get_by_role('navigation', name='主导航', exact=True).get_by_role('link', name='游戏', exact=True).click()
    expect(page.locator('.game-card')).to_have_count(9)
    metadata('/game')
    for path, title in [('2048', '2048'), ('minesweeper', '扫雷'), ('solitaire', '纸牌接龙'), ('tetris', '经典俄罗斯方块黑白版'), ('sudoku', '数独经典版'), ('xiangqi', '中国象棋单机版'), ('gomoku', '五子棋单机版'), ('snake', '贪吃蛇'), ('popstar', '消灭星星经典版')]:
        page.locator(f'.game-card[href="/games/{path}"]').click()
        expect(page.locator('.game-heading h1')).to_have_text(title)
        expect(page.locator('.game-surface')).to_be_visible()
        metadata('/games/' + path)
        expect(page.locator('.desktop-nav [aria-current="page"]')).to_have_text('游戏')
        assert page.evaluate('window.navigationProbe.header === document.querySelector(".header")')
        assert page.evaluate('window.navigationProbe.audio === document.querySelector("audio") && !document.querySelector("audio").paused')
        page.get_by_role('link', name='全部游戏', exact=True).click()
        expect(page.locator('.game-card')).to_have_count(9)
    page.get_by_role('navigation', name='主导航', exact=True).get_by_role('link', name='项目', exact=True).click()
    expect(page.locator('.project-card')).to_have_count(9)

    card = page.locator('.project-rdp')
    card.scroll_into_view_if_needed()
    before = page.evaluate('scrollY')
    card.click()
    expect(page.locator('.auth-demo')).to_have_count(1)
    metadata('/projects/rdp-access-auth', True)
    page.go_back()
    expect(page.locator('.directory-toolbar')).to_be_visible()
    page.wait_for_function('(y) => Math.abs(scrollY - y) < 3', arg=before)
    metadata('/project')
    page.go_forward()
    expect(page.get_by_role('link', name='开始部署')).to_be_visible()
    page.get_by_role('link', name='开始部署').click()
    expect(page.locator('#deployment')).to_be_visible()
    page.wait_for_function('Math.abs(document.querySelector("#deployment").getBoundingClientRect().top - 110) < 3')
    metadata('/projects/rdp-access-auth/wiki', True)
    expect(page.locator('#deployment')).to_be_focused()
    page.locator('.rdp-toc a[href="#section-2"]').click()
    page.wait_for_url('**/wiki#section-2')
    page.go_back()
    page.wait_for_url('**/wiki#deployment')
    metadata('/projects/rdp-access-auth/wiki', True)
    page.get_by_role('navigation', name='项目导航').get_by_role('link', name='概览', exact=True).click()
    expect(page.locator('.auth-demo')).to_be_visible()
    metadata('/projects/rdp-access-auth', True)
    page.get_by_role('navigation', name='项目导航').get_by_role('link', name='Wiki', exact=True).click()
    expect(page.locator('.wiki-page')).to_be_visible()
    metadata('/projects/rdp-access-auth/wiki', True)

    page.locator('.footer a[href="/"]').click()
    expect(page.locator('.hero')).to_be_visible()
    metadata('/')
    page.get_by_role('navigation', name='主导航', exact=True).get_by_role('link', name='项目', exact=True).click()
    expect(page.locator('.directory-toolbar')).to_be_visible()
    page.locator('.nav-contact').click()
    page.wait_for_url('**/#contact')
    expect(page.locator('#contact')).to_be_focused()
    metadata('/')

    # Absolute same-origin URLs and queries use the same router.
    page.evaluate('(href) => { const a = document.createElement("a"); a.id="navigation-test"; a.href=href; a.textContent="test"; document.body.append(a); a.click() }', base + '/project?source=test')
    page.wait_for_url('**/project?source=test')
    expect(page.locator('.directory-toolbar')).to_be_visible()
    metadata('/project')

    # Observe whether the router cancelled default navigation, then suppress native navigation
    # solely in this test so external sites/downloads/new tabs do not have to be opened.
    for attrs in [
        {'href': 'https://mcyzw.top/'},
        {'href': '/images/share-cover.jpg'},
        {'href': '/api/music/lyrics?id=1'},
        {'href': '/', 'target': '_blank'},
        {'href': '/', 'download': ''},
        {'href': '/', 'ctrlKey': True},
        {'href': '/', 'metaKey': True},
        {'href': '/', 'button': 1},
    ]:
        prevented = page.evaluate('''(attrs) => {
            const a = document.createElement('a');
            for (const [key, value] of Object.entries(attrs))
                if (!['ctrlKey', 'metaKey', 'button'].includes(key)) a.setAttribute(key, value);
            document.body.append(a);
            let intercepted;
            document.addEventListener('click', event => {
                intercepted = event.defaultPrevented;
                event.preventDefault();
            }, {once: true});
            a.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, ...attrs}));
            a.remove();
            return intercepted;
        }''', attrs)
        assert prevented is False, attrs
    intact()

    for path, marker in [('/project', '.directory-toolbar'), ('/projects/rdp-access-auth', '.auth-demo'), ('/projects/rdp-access-auth/wiki#deployment', '#deployment')]:
        clean = path.split('#')[0]
        response = context.request.get(base + clean)
        assert response.status == 200
        assert f'href="https://zxabinbina.cc.cd{clean}"' in response.text(), 'Wrong raw HTML metadata'
        for suffix in ['/', '/index.html', '.html']:
            redirect = context.request.get(base + clean + suffix + '?source=legacy', max_redirects=0)
            assert redirect.status == 301, (clean, suffix, redirect.status)
            assert redirect.headers['location'] == clean + '?source=legacy'
        page.goto(base + path, wait_until='networkidle')
        expect(page.locator(marker)).to_be_visible()
        page.reload(wait_until='networkidle')
        expect(page.locator(marker)).to_be_visible()
        page.locator('main').evaluate('(el) => el.scrollIntoView()')
        page.wait_for_function('Array.from(document.querySelectorAll("img")).filter(img => img.getBoundingClientRect().top < innerHeight).every(img => img.complete && img.naturalWidth > 0)')
    page.goto(base + '/projects/rdp-access-auth/wiki/?source=legacy#deployment', wait_until='networkidle')
    page.wait_for_url('**/wiki?source=legacy#deployment')
    expect(page.locator('#deployment')).to_be_focused()
    page.wait_for_function('Math.abs(document.querySelector("#deployment").getBoundingClientRect().top - 110) < 3')
    # Normal motion exposes header remounts that reduced-motion navigation would hide.
    page.emulate_media(reduced_motion='no-preference')
    for width, theme in [(1440, 'dark'), (390, 'light')]:
        page.set_viewport_size({'width': width, 'height': 1000})
        page.evaluate('(theme) => localStorage.setItem("homepage-theme", theme)', theme)
        page.goto(base + '/projects/rdp-access-auth', wait_until='networkidle')
        page.wait_for_function('document.querySelector(".rdp-header").getAnimations().every(a => a.playState === "finished")')
        page.evaluate('''window.rdpHeaderProbe = {
            header: document.querySelector('.rdp-header'),
            logo: document.querySelector('.rdp-mark'),
            footer: document.querySelector('.footer'),
            animation: document.querySelector('.rdp-header').getAnimations()[0]
        }''')
        for label, selector in [('Wiki', '.wiki-page'), ('概览', '.auth-demo'), ('Wiki', '.wiki-page')]:
            page.get_by_role('navigation', name='项目导航').get_by_role('link', name=label, exact=True).click()
            expect(page.locator(selector)).to_be_visible()
            expect(page.locator('main')).to_be_focused()
            expect(page.locator('.rdp-header [aria-current="page"]')).to_have_text(label)
            assert page.evaluate('''rdpHeaderProbe.header === document.querySelector('.rdp-header') &&
                rdpHeaderProbe.logo === document.querySelector('.rdp-mark') &&
                rdpHeaderProbe.footer === document.querySelector('.footer')'''), 'RDP header/footer remounted'
            assert page.evaluate('''rdpHeaderProbe.header.getAnimations()[0] === rdpHeaderProbe.animation &&
                rdpHeaderProbe.header.getAnimations().every(a => a.playState === 'finished') &&
                Number(getComputedStyle(rdpHeaderProbe.header).opacity) === 1'''), 'RDP header replayed its entrance'
        page.screenshot(path=f'artifacts/rdp-navigation-{theme}-{width}.png')
    assert not errors, errors
    browser.close()
print('No document reloads; RDP navigation, slashless URLs, legacy redirects, raw metadata, history/scroll, anchors, shared music and native links passed.')
