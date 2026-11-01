"""Check error documents against a built preview; mock only the host's 404 response."""
import os
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, expect
from browser_theme import set_theme_mode

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'artifacts'
OUT.mkdir(exist_ok=True)
BASE = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:4173').rstrip('/')
CODES = (400, 401, 403, 404, 408, 429, 500, 502, 503, 504)
RETRY = (408, 500, 502, 503, 504)

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'),
        args=['--no-sandbox'],
    )
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, color_scheme='dark')
    page = context.new_page()
    errors, failed_assets, audio_requests = [], [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('requestfailed', lambda request: failed_assets.append(request.url)
            if request.resource_type in ('script', 'stylesheet') else None)
    page.on('response', lambda response: failed_assets.append(response.url)
            if response.status >= 400 and response.request.resource_type in ('script', 'stylesheet') else None)
    page.on('request', lambda request: audio_requests.append(request.url)
            if request.resource_type == 'media' or '/song/media/' in request.url else None)

    def assert_error(code):
        expect(page.locator('.error-code')).to_have_text([str(code)])
        expect(page.locator('#error-title')).to_be_visible()
        expect(page.locator('main')).to_have_count(1)
        expect(page.locator('.header')).to_be_visible()
        expect(page.locator('.footer')).to_have_count(1)
        expect(page.locator('.desktop-nav [aria-current="page"]')).to_have_count(0)
        expect(page.locator('meta[name="robots"]')).to_have_attribute('content', 'noindex')
        assert page.title().startswith(f'{code} · '), page.title()
        assert page.get_by_role('button', name='重新加载', exact=True).count() == int(code in RETRY)

    def settle_motion():
        page.wait_for_function('''() => {
            const error = document.querySelector('.error-page');
            return error && error.getAnimations({subtree: true})
                .every(animation => animation.playState === 'finished');
        }''')

    def follow(path):
        page.evaluate('''path => {
            const link = document.createElement('a');
            link.href = path; document.body.append(link); link.click(); link.remove();
        }''', path)

    for code in CODES:
        page.goto(f'{BASE}/{code}', wait_until='networkidle')
        assert_error(code)
        page.reload(wait_until='networkidle')
        assert_error(code)
        for suffix in ('/', '.html', '/index.html'):
            response = context.request.get(f'{BASE}/{code}{suffix}?source=legacy', max_redirects=0)
            assert response.status == 301, (code, suffix, response.status)
            assert response.headers['location'] == f'/{code}?source=legacy'

    # A top-level unknown route exercises Vue's catch-all with the preview's SPA fallback.
    page.goto(BASE + '/__unknown_page__?source=test', wait_until='networkidle')
    assert_error(404)
    assert urlparse(page.url).path == '/__unknown_page__'

    # Cloudflare serves the built 404 document at the original URL. Keeping this URL
    # nested catches relative entry-script/CSS paths that a direct /404 visit would miss.
    context.route(BASE + '/__missing__/**', lambda route: route.fulfill(
        status=404, content_type='text/html', body=(ROOT / 'dist/404.html').read_text(),
    ))
    missing = '/__missing__/several/levels/page?source=test'
    response = page.goto(BASE + missing, wait_until='networkidle')
    assert response.status == 404
    assert_error(404)
    assert page.url == BASE + missing
    assert page.locator('.error-card').evaluate('(el) => getComputedStyle(el).display') == 'grid'
    page.reload(wait_until='networkidle')
    assert_error(404)
    page.keyboard.press('Tab')
    expect(page.get_by_role('link', name='跳至内容')).to_be_focused()
    page.keyboard.press('Enter')
    expect(page.locator('main')).to_be_focused()

    # Returning from an error must reuse the document/header and restore indexability.
    page.evaluate('window.errorProbe = { header: document.querySelector(".header") }')
    page.get_by_role('link', name='返回首页', exact=True).click()
    expect(page.locator('.hero')).to_be_visible()
    expect(page.locator('meta[name="robots"]')).to_have_attribute('content', 'index, follow, max-image-preview:large')
    assert page.evaluate('window.errorProbe.header === document.querySelector(".header")')
    page.go_back()
    assert_error(404)
    assert page.evaluate('window.errorProbe.header === document.querySelector(".header")')
    page.locator('.error-actions a[href="/project"]').click()
    expect(page.locator('.directory-toolbar')).to_be_visible()
    page.go_back()
    assert_error(404)
    page.locator('.error-contact').click()
    page.wait_for_url('**/#contact')
    expect(page.locator('#contact')).to_be_focused()

    # Enter the 403 route through the same handler as ordinary same-origin links.
    page.evaluate('''() => {
        const link = document.createElement('a');
        link.href = '/403'; document.body.append(link); link.click(); link.remove();
    }''')
    assert_error(403)
    page.wait_for_function('document.activeElement === document.querySelector("main")')
    assert page.evaluate('window.errorProbe.header === document.querySelector(".header")')
    page.get_by_role('button', name='返回上一页', exact=True).click()
    page.wait_for_url(BASE + '/#contact')
    expect(page.locator('.hero')).to_be_visible()
    assert page.evaluate('window.errorProbe.header === document.querySelector(".header")')
    page.go_forward()
    assert_error(403)
    page.get_by_role('link', name='实用工具', exact=True).click()
    expect(page.locator('.tool-card').first).to_be_visible()
    page.go_back()
    assert_error(403)
    page.get_by_role('link', name='玩会儿游戏', exact=True).click()
    expect(page.locator('.game-card').first).to_be_visible()

    page.goto(BASE + '/503', wait_until='networkidle')
    page.evaluate('window.beforeErrorReload = true')
    page.evaluate('''() => {
        const root = document.querySelector('.error-page');
        const frames = [];
        root.addEventListener('transitionrun', event => {
            if (event.target !== root || event.propertyName !== 'opacity') return;
            const record = () => {
                frames.push({opacity: Number(getComputedStyle(root).opacity), inert: root.inert});
                sessionStorage.setItem('errorReloadFrames', JSON.stringify(frames));
                requestAnimationFrame(record);
            };
            requestAnimationFrame(record);
        });
    }''')
    with page.expect_navigation(wait_until='networkidle'):
        page.get_by_role('button', name='重新加载').click()
    assert_error(503)
    assert page.evaluate('window.beforeErrorReload === undefined')
    frames = page.evaluate('JSON.parse(sessionStorage.getItem("errorReloadFrames"))')
    assert frames and any(frame['opacity'] < 0.2 for frame in frames), frames
    assert all(frame['inert'] for frame in frames), frames

    # A newer navigation must cancel a pending reload before its bundle arrives.
    pending_routes = []
    page.route('**/assets/ProjectDirectory-*.js', lambda route: pending_routes.append(route))
    page.evaluate('window.cancelReloadProbe = true')
    page.get_by_role('button', name='重新加载').evaluate('(el) => { el.click(); el.click(); }')
    follow('/project')
    page.wait_for_timeout(700)
    assert pending_routes, 'Destination bundle was not delayed'
    assert page.evaluate('window.cancelReloadProbe === true'), 'An obsolete retry interrupted navigation'
    expect(page.locator('.error-page')).not_to_have_attribute('inert', '')
    for pending_route in pending_routes:
        pending_route.continue_()
    page.unroute('**/assets/ProjectDirectory-*.js')
    expect(page.locator('.directory-toolbar')).to_be_visible()
    page.wait_for_timeout(500)
    assert page.evaluate('window.cancelReloadProbe === true'), 'An obsolete retry reloaded the new page'

    # Cover all themes and each layout breakpoint, including both sides of the split.
    for palette in ('fufu-blue', 'hutao-red'):
        for theme in ('dark', 'light'):
            page.evaluate('''({theme, palette}) => {
                localStorage.setItem('homepage-theme', theme);
                localStorage.setItem('homepage-palette', palette);
            }''', {'theme': theme, 'palette': palette})
            page.goto(BASE + '/404', wait_until='networkidle')
            expect(page.locator('html')).to_have_attribute('data-theme', theme)
            expect(page.locator('html')).to_have_attribute('data-palette', palette)
            settle_motion()
            for width in (320, 390, 480, 481, 760, 761, 768, 1024, 1440):
                page.set_viewport_size({'width': width, 'height': 900})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (palette, theme, width)
                assert page.locator('.header .brand').evaluate('(el) => el.scrollWidth <= el.clientWidth'), (palette, theme, width)
                assert page.locator('.error-actions .button, .error-contact, .error-explore a').evaluate_all(
                    'els => els.every(el => el.getBoundingClientRect().height >= 44)')
                if width in (320, 390, 768, 1440):
                    page.screenshot(path=str(OUT / f'error-404-{palette}-{theme}-{width}.png'), full_page=True)

    # Longer copy and labels must also fit on narrow screens.
    page.set_viewport_size({'width': 320, 'height': 900})
    for code in CODES:
        page.goto(f'{BASE}/{code}', wait_until='networkidle')
        assert_error(code)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), code

    page.get_by_role('button', name='选择配色方案').click()
    page.wait_for_function('document.querySelector(".palette-popover") && !document.querySelector(".palette-popover").classList.contains("palette-popover-enter-active")')
    palette_box = page.locator('.palette-popover').bounding_box()
    assert palette_box['x'] >= 0 and palette_box['x'] + palette_box['width'] <= 320, palette_box
    page.keyboard.press('Escape')
    expect(page.get_by_role('button', name='选择配色方案')).to_be_focused()
    page.get_by_role('button', name='打开菜单').click()
    page.get_by_role('navigation', name='移动导航').get_by_role('link', name='工具', exact=True).click()
    expect(page.locator('.tool-card').first).to_be_visible()
    expect(page.get_by_role('button', name='打开菜单')).to_have_attribute('aria-expanded', 'false')

    # Observe the real first-load entrance, including frames before it finishes.
    page.add_init_script('''
        window.errorFrames = [];
        window.problemFrames = [];
        document.addEventListener('animationstart', event => {
            if (event.target.matches('.error-blocks span:nth-child(2) i')) {
                const block = event.target;
                const record = () => {
                    window.problemFrames.push(getComputedStyle(block).transform);
                    if (block.isConnected && block.getAnimations().some(a => a.playState === 'running'))
                        requestAnimationFrame(record);
                };
                requestAnimationFrame(record);
            }
            if (!event.target.matches('.error-card')) return;
            const card = event.target;
            const record = () => {
                const style = getComputedStyle(card);
                window.errorFrames.push({opacity: Number(style.opacity), translate: style.translate});
                if (card.isConnected && card.getAnimations().some(a => a.playState === 'running'))
                    requestAnimationFrame(record);
            };
            requestAnimationFrame(record);
        });
    ''')
    page.set_viewport_size({'width': 1440, 'height': 900})
    page.goto(BASE + '/404', wait_until='networkidle')
    assert_error(404)
    settle_motion()
    frames = page.evaluate('window.errorFrames')
    assert any(frame['opacity'] < 0.95 for frame in frames), frames
    assert any(frame['translate'] not in ('none', '0px', '0px 0px') for frame in frames), frames
    assert len(set(page.evaluate('window.problemFrames'))) > 10, 'Missing block problem motion'
    expect(page.locator('.error-card')).to_have_css('opacity', '1')
    # Keep the second block's original tilt while its independent entry motion runs.
    assert page.locator('.error-blocks span').nth(1).evaluate('(el) => getComputedStyle(el).transform') != 'none'
    page.evaluate('''() => {
        for (const animation of document.querySelector('.error-page').getAnimations({subtree: true})) {
            animation.pause(); animation.currentTime = 200;
        }
    }''')
    page.screenshot(path=str(OUT / 'error-entry-200ms-1440.png'), full_page=True)
    page.evaluate('document.querySelector(".error-page").getAnimations({subtree: true}).forEach(animation => animation.finish())')
    page.evaluate('''() => {
        for (const animation of document.querySelector('.error-page').getAnimations({subtree: true})) {
            animation.pause(); animation.currentTime = 1280;
        }
    }''')
    page.screenshot(path=str(OUT / 'error-block-problem-1280ms-1440.png'), full_page=True)
    page.evaluate('document.querySelector(".error-page").getAnimations({subtree: true}).forEach(animation => animation.finish())')

    page.evaluate('window.motionHeader = document.querySelector(".header")')
    for width in (1440, 390):
        page.set_viewport_size({'width': width, 'height': 900})
        settle_motion()
        page.evaluate('''() => {
            const error = window.leavingError = document.querySelector('.error-page');
            window.exitFrames = [];
            error.addEventListener('transitionrun', event => {
                if (event.target !== error || event.propertyName !== 'opacity') return;
                const record = () => {
                    if (!error.isConnected) return;
                    const style = getComputedStyle(error);
                    window.exitFrames.push({opacity: Number(style.opacity), scale: Number(style.scale), inert: error.inert,
                        block: getComputedStyle(error.querySelector('.error-blocks span')).transform});
                    requestAnimationFrame(record);
                };
                requestAnimationFrame(record);
            });
        }''')
        follow('/403' if page.url.endswith('/404') else '/404')
        page.wait_for_function('!window.leavingError.isConnected')
        frames = page.evaluate('window.exitFrames')
        assert any(frame['opacity'] < 0.9 and frame['scale'] < 1 for frame in frames), frames
        assert all(frame['inert'] for frame in frames), 'Departing page can still receive input'
        assert len({frame['block'] for frame in frames}) > 3, 'Blocks did not move during exit'
        expect(page.locator('.error-page')).to_have_count(1)
        settle_motion()
        page.wait_for_function('document.activeElement === document.querySelector("main")')
        assert page.evaluate('window.motionHeader === document.querySelector(".header")')

    # Interrupt an entrance twice; the final page must remain visible and interactive.
    for path in ('/500', '/404', '/503'):
        follow(path)
        page.wait_for_url(BASE + path)
    assert_error(503)
    settle_motion()
    expect(page.locator('.error-page[inert]')).to_have_count(0)
    expect(page.locator('.error-card')).to_have_css('opacity', '1')

    # A changed system preference must stop an in-flight entrance without hiding content.
    follow('/500')
    page.wait_for_url(BASE + '/500')
    page.emulate_media(reduced_motion='reduce')
    assert_error(500)
    settle_motion()
    expect(page.locator('.error-card')).to_have_css('opacity', '1')
    assert page.locator('.error-card, .error-code, .error-blocks span, .error-blocks i, .error-content > *').evaluate_all(
        'els => els.every(el => getComputedStyle(el).animationName === "none")')

    page.emulate_media(reduced_motion='reduce')
    page.set_viewport_size({'width': 320, 'height': 900})
    page.goto(BASE + '/500', wait_until='networkidle')
    assert_error(500)
    set_theme_mode(page, 'dark')
    expect(page.locator('html')).to_have_attribute('data-theme', 'dark')
    page.screenshot(path=str(OUT / 'error-500-reduced-motion-320.png'), full_page=True)
    with page.expect_navigation(wait_until='networkidle', timeout=3000):
        page.get_by_role('button', name='重新加载').click()
    assert_error(500)
    assert not errors, errors
    assert not failed_assets, failed_assets
    assert not audio_requests, audio_requests

    # Hide Back without a previous entry, including when only forward entries remain.
    # Opening the destination directly avoids Playwright's initial about:blank history entry.
    with page.expect_popup() as new_tab:
        page.evaluate("window.open('/404', '_blank')")
    back_page = new_tab.value
    back_page.emulate_media(reduced_motion='reduce')
    back_page.wait_for_load_state('networkidle')
    assert back_page.evaluate('history.length') == 1
    expect(back_page.get_by_role('button', name='返回上一页', exact=True)).to_have_count(0)
    assert back_page.url == BASE + '/404'
    expect(back_page.get_by_role('link', name='返回首页', exact=True)).to_be_enabled()
    expect(back_page.locator('.error-page')).not_to_have_attribute('inert', '')
    back_page.reload(wait_until='networkidle')
    expect(back_page.get_by_role('button', name='返回上一页', exact=True)).to_have_count(0)
    # Hash changes reuse the same error component, so visibility must update in place.
    back_page.evaluate('''() => {
        window.firstErrorPage = document.querySelector('.error-page');
        const link = document.createElement('a');
        link.href = '/404#main'; document.body.append(link); link.click(); link.remove();
    }''')
    back_page.wait_for_url(BASE + '/404#main')
    expect(back_page.get_by_role('button', name='返回上一页', exact=True)).to_be_visible()
    assert back_page.evaluate('window.firstErrorPage === document.querySelector(".error-page")')
    back_page.get_by_role('button', name='返回上一页', exact=True).click()
    back_page.wait_for_url(BASE + '/404')
    assert back_page.evaluate('history.length') > 1
    expect(back_page.get_by_role('button', name='返回上一页', exact=True)).to_have_count(0)
    back_page.reload(wait_until='networkidle')
    expect(back_page.get_by_role('button', name='返回上一页', exact=True)).to_have_count(0)
    back_page.get_by_role('link', name='返回首页', exact=True).click()
    back_page.wait_for_url(BASE + '/')
    back_page.go_back()
    back_page.wait_for_url(BASE + '/404')
    expect(back_page.get_by_role('button', name='返回上一页', exact=True)).to_have_count(0)

    # An opaque cross-origin entry is uncertain even when the inferred position is positive.
    previous = 'https://previous.example/history?from=error#position'
    back_page.route('https://previous.example/**', lambda route: route.fulfill(
        content_type='text/html', body='<h1>Previous page</h1>',
    ))
    back_page.goto(previous)
    back_page.goto(BASE + '/500', wait_until='networkidle')
    assert back_page.evaluate('history.length > 1 && history.state.position > 0')
    expect(back_page.get_by_role('button', name='返回上一页', exact=True)).to_have_count(0)
    back_page.go_back()
    back_page.wait_for_url(previous)
    expect(back_page.get_by_role('heading', name='Previous page')).to_be_visible()

    # Without Navigation API, require a concrete prior route instead of a numeric guess.
    back_page.add_init_script("Object.defineProperty(window, 'navigation', {value: undefined})")
    back_page.goto(BASE + '/404', wait_until='networkidle')
    assert back_page.evaluate('history.length > 1 && history.state.position > 0')
    expect(back_page.get_by_role('button', name='返回上一页', exact=True)).to_have_count(0)
    back_page.get_by_role('link', name='返回首页', exact=True).click()
    back_page.wait_for_url(BASE + '/')
    back_page.evaluate('''() => {
        const link = document.createElement('a');
        link.href = '/503'; document.body.append(link); link.click(); link.remove();
    }''')
    back_page.wait_for_url(BASE + '/503')
    expect(back_page.get_by_role('button', name='返回上一页', exact=True)).to_be_visible()
    back_page.reload(wait_until='networkidle')
    expect(back_page.get_by_role('button', name='返回上一页', exact=True)).to_be_visible()
    back_page.get_by_role('button', name='返回上一页', exact=True).click()
    back_page.wait_for_url(BASE + '/')
    back_page.close()
    browser.close()

print('Error checks passed: 10 routes, aliases, nested 404 document, recovery, metadata, focus, themes, responsive layouts, entrance/exit motion, rapid switches and reduced motion.')
