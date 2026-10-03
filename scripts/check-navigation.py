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
        expect(page.locator('link[rel="icon"]')).to_have_attribute('href', '/images/rdp-access-auth.png' if project else '/favicon.svg')
        assert page.locator('body').evaluate('(el) => el.classList.contains("rdp-site")') == project
        intact()

    page.get_by_role('button', name='打开网易云音乐播放器').click()
    page.wait_for_function('document.querySelector("audio")?.currentTime > 0')
    page.evaluate('window.navigationProbe.audio = document.querySelector("audio")')
    page.get_by_role('button', name='关闭音乐播放器').click()
    page.get_by_role('navigation', name='主导航', exact=True).get_by_role('link', name='项目', exact=True).click()
    expect(page.locator('.project-card')).to_have_count(4)
    expect(page).to_have_title('项目目录 · a彬彬a')
    metadata('/project')
    assert page.evaluate('window.navigationProbe.header === document.querySelector(".header")')
    assert page.evaluate('window.navigationProbe.audio === document.querySelector("audio") && !document.querySelector("audio").paused')
    page.wait_for_function('document.activeElement === document.querySelector("main")')
    page.wait_for_function('scrollY === 0')

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
    page.locator('.rdp-toc a[href="#section-3"]').click()
    page.wait_for_url('**/wiki#section-3')
    page.go_back()
    page.wait_for_url('**/wiki#deployment')
    metadata('/projects/rdp-access-auth/wiki', True)

    page.locator('.rdp-footer a[href="/"]').click()
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
        page.goto(base + path, wait_until='networkidle')
        expect(page.locator(marker)).to_be_visible()
        page.reload(wait_until='networkidle')
        expect(page.locator(marker)).to_be_visible()
        page.locator('main').evaluate('(el) => el.scrollIntoView()')
        page.wait_for_function('Array.from(document.querySelectorAll("img")).filter(img => img.getBoundingClientRect().top < innerHeight).every(img => img.complete && img.naturalWidth > 0)')
    assert not errors, errors
    browser.close()
print('No document reloads; metadata, history/scroll, anchors, shared music, native links and direct/reloaded routes passed.')
