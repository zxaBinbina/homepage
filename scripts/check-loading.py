"""Exercise real delayed/failed bundles on a production preview, without timing mocks."""
import asyncio
import os
import re
from pathlib import Path
from playwright.async_api import async_playwright, expect

BASE = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:4173').rstrip('/')
OUT = Path('artifacts/loading')
OUT.mkdir(parents=True, exist_ok=True)


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'),
            args=['--no-sandbox'],
        )
        errors = []

        async def context_for(theme='dark', palette='fufu-blue', motion='no-preference', failures=False):
            context = await browser.new_context(
                viewport={'width': 1440, 'height': 900},
                color_scheme='light' if theme == 'dark' else 'dark', reduced_motion=motion,
            )
            await context.add_init_script(
                f'localStorage.setItem("homepage-theme", "{theme}");'
                f'localStorage.setItem("homepage-palette", "{palette}")'
            )
            page = await context.new_page()
            if not failures:
                page.on('pageerror', lambda error: errors.append(str(error)))
            return context, page

        async def navigate(page, path):
            # Uses the real document click handler, with no direct router/state access.
            await page.evaluate('''path => {
                const link = document.createElement('a');
                link.href = path; document.body.append(link); link.click(); link.remove();
            }''', path)

        async def delay(page, pattern):
            release, requested = asyncio.Event(), asyncio.Event()

            async def handle(route):
                requested.set()
                await release.wait()
                await route.continue_()

            await page.route(re.compile(pattern), handle)
            return release, requested

        async def hidden(page):
            await expect(page.locator('#site-loading')).to_be_hidden()

        async def shown(page, mode):
            await expect(page.locator('#site-loading')).to_have_attribute('data-mode', mode)
            await expect(page.locator('#site-loading')).to_have_attribute('data-visible', 'true')
            await expect(page.locator('.site-loading-title')).to_be_visible()

        async def retry_keeps_layout(page):
            retry = page.locator('.site-loading-retry')
            await expect(retry).to_be_hidden()
            assert await retry.evaluate('el => el.inert && el.getAttribute("aria-hidden") === "true"')
            before = {}
            content_before = {}
            for width in [320, 390, 768, 1024, 1440]:
                await page.set_viewport_size({'width': width, 'height': 844})
                before[width] = await page.locator('.site-loading-card').bounding_box()
                content_before[width] = await page.locator('.site-loading-content').bounding_box()
                card, content = before[width], content_before[width]
                assert abs(card['y'] + card['height'] / 2 - content['y'] - content['height'] / 2) <= 4, (width, card, content)
            await expect(retry).to_be_visible(timeout=12000)
            await page.wait_for_function('getComputedStyle(document.querySelector(".site-loading-retry")).opacity === "1"')
            await page.wait_for_function('!document.querySelector(".site-loading-content").getAnimations().length')
            transition = await retry.evaluate('el => getComputedStyle(el).transitionDuration')
            assert '0.22s' in transition, transition
            assert await page.locator('.site-loading-content').evaluate('el => getComputedStyle(el).transitionDuration') == '0.32s'
            initial = await page.locator('#site-loading').get_attribute('data-mode') == 'initial'
            offset = 32 if initial else 0
            for width, box in before.items():
                await page.set_viewport_size({'width': width, 'height': 844})
                after = await page.locator('.site-loading-card').bounding_box()
                assert all(abs(box[key] - after[key]) <= 1 for key in ['x', 'y', 'width', 'height']), (width, box, after)
                content_after = await page.locator('.site-loading-content').bounding_box()
                assert abs(content_before[width]['y'] - content_after['y'] - offset) <= 1, (width, content_before[width], content_after)
                if not initial:
                    button = await retry.bounding_box()
                    assert button['x'] >= content_after['x'] + content_after['width'] + 11, (width, content_after, button)
                    assert abs(button['y'] + button['height'] / 2 - after['y'] - after['height'] / 2) <= 1, (width, after, button)
                    assert button['height'] >= 44 and after['height'] <= 132, (width, after, button)
                    assert button['x'] + button['width'] <= after['x'] + after['width'] - 15
            assert not await retry.evaluate('el => el.inert')

        async def check_navigation_themes(page):
            for palette in ['fufu-blue', 'hutao-red']:
                for theme in ['dark', 'light']:
                    await page.evaluate('''([palette, theme]) => {
                        document.documentElement.dataset.palette = palette;
                        document.documentElement.dataset.theme = theme;
                    }''', [palette, theme])
                    for width in [320, 390, 480, 481, 768, 1024, 1440]:
                        await page.set_viewport_size({'width': width, 'height': 844})
                        assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                        assert await page.locator('.site-loading-title').evaluate('el => el.getBoundingClientRect().height <= parseFloat(getComputedStyle(el).lineHeight) + 1')
                        assert await page.locator('.site-loading-description').evaluate('el => el.scrollHeight <= 2 * parseFloat(getComputedStyle(el).lineHeight) + 1')
                        button = await page.locator('.site-loading-retry').bounding_box()
                        content = await page.locator('.site-loading-content').bounding_box()
                        assert button['x'] > content['x'] + content['width']
                        if width in [320, 1440]:
                            await page.screenshot(path=str(OUT / f'navigation-retry-{palette}-{theme}-{width}.png'))

        # Blocking both external CSS and JS must still leave a readable, themed first paint.
        for palette in ['fufu-blue', 'hutao-red']:
            for theme in ['dark', 'light']:
                context, page = await context_for(theme, palette)
                release, requested = await delay(page, r'/assets/.*\.(?:js|css)(?:\?.*)?$')
                await page.goto(BASE + '/', wait_until='commit')
                await requested.wait()
                await shown(page, 'initial')
                expected = {
                    ('fufu-blue', 'dark'): 'rgb(20, 21, 33)',
                    ('fufu-blue', 'light'): 'rgb(244, 246, 250)',
                    ('hutao-red', 'dark'): 'rgb(58, 27, 25)',
                    ('hutao-red', 'light'): 'rgb(252, 240, 225)',
                }[palette, theme]
                assert await page.locator('#site-loading').evaluate(
                    'el => getComputedStyle(el).backgroundColor') == expected
                for width in [320, 390, 768, 1024, 1440]:
                    await page.set_viewport_size({'width': width, 'height': 844})
                    assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                    box = await page.locator('.site-loading-card').bounding_box()
                    assert box['x'] >= 0 and box['x'] + box['width'] <= width, box
                    if width in [320, 1440]:
                        await page.screenshot(path=str(OUT / f'initial-{palette}-{theme}-{width}.png'))
                if palette == 'fufu-blue' and theme == 'dark':
                    await retry_keeps_layout(page)
                    await page.screenshot(path=str(OUT / 'initial-retry.png'))
                release.set()
                await page.wait_for_load_state('networkidle')
                await expect(page.locator('.hero')).to_be_visible()
                await hidden(page)
                await context.close()
        print('Initial paint: delayed JS and CSS, four themes and five widths passed.', flush=True)

        # CSS alone can stall after JS/router are ready; Vue must await styled content.
        context, page = await context_for()
        release, requested = await delay(page, r'/assets/index-.*\.css$')
        await page.goto(BASE, wait_until='commit')
        await requested.wait()
        await shown(page, 'initial')
        await expect(page.locator('#app')).to_be_empty()
        release.set()
        await expect(page.locator('.hero')).to_be_visible()
        await hidden(page)
        await context.close()

        # Test delay threshold, actual lazy route loading, cancellation and stale completion.
        context, page = await context_for()
        await page.goto(BASE, wait_until='networkidle')
        await hidden(page)
        await page.evaluate('''() => {
            window.loadingFlashes = 0;
            new MutationObserver(records => {
                for (const r of records)
                    if (r.attributeName === 'data-visible' && r.target.dataset.visible === 'true')
                        window.loadingFlashes++;
            }).observe(document.querySelector('#site-loading'), {attributes: true});
            window.originalHeader = document.querySelector('.header');
        }''')
        release, requested = await delay(page, r'/assets/ProjectDirectory-.*\.js$')
        await navigate(page, '/project')
        await requested.wait()
        await page.wait_for_timeout(180)
        await hidden(page)
        await shown(page, 'navigation')
        assert await page.evaluate('window.originalHeader === document.querySelector(".header")')
        await page.get_by_role('button', name='切换浅色主题').click()
        await expect(page.locator('html')).to_have_attribute('data-theme', 'light')
        for width in [320, 390, 768, 1024, 1440]:
            await page.set_viewport_size({'width': width, 'height': 844})
            box = await page.locator('.site-loading-card').bounding_box()
            assert box['x'] >= 0 and box['x'] + box['width'] <= width, box
        await page.screenshot(path=str(OUT / 'navigation-light.png'))
        await retry_keeps_layout(page)
        await page.screenshot(path=str(OUT / 'navigation-retry.png'))
        await check_navigation_themes(page)
        # Clicking the current home page cancels a pending different route.
        await navigate(page, '/')
        await hidden(page)
        await navigate(page, '/project')
        await shown(page, 'navigation')
        await navigate(page, '/#about')
        await hidden(page)
        await page.wait_for_function('document.activeElement?.id === "about"')
        release.set()
        await page.wait_for_timeout(600)
        assert page.url.split('#')[0].rstrip('/') == BASE
        await hidden(page)
        await navigate(page, '/project')
        await expect(page.locator('.directory-toolbar')).to_be_visible()
        await hidden(page)
        await page.evaluate('window.loadingFlashes = 0')
        await navigate(page, '/')
        await expect(page.locator('.hero')).to_be_visible()
        await navigate(page, '/project')
        await expect(page.locator('.directory-toolbar')).to_be_visible()
        await page.wait_for_timeout(700)
        assert await page.evaluate('window.loadingFlashes') == 0, 'Cached navigation flashed the loader'
        await navigate(page, '/#contact')
        await page.wait_for_function('document.activeElement?.id === "contact"')
        await hidden(page)
        await context.close()
        print('Navigation: delay threshold, live theme, cancellation, cached routes and anchor focus passed.', flush=True)

        # Nested async content needs feedback even after the route shell is mounted.
        for path, chunk, ready in [
            ('/tools/json-formatter', 'JsonFormatter', '.freemium-workbench textarea'),
            ('/games/2048', 'NumberGame', '.game-surface'),
        ]:
            context, page = await context_for('dark', 'hutao-red', 'reduce')
            await page.goto(BASE, wait_until='networkidle')
            release, requested = await delay(page, rf'/assets/{chunk}-.*\.js$')
            await navigate(page, path)
            await requested.wait()
            await shown(page, 'navigation')
            assert await page.locator('#site-loading').evaluate(
                'el => el.getAnimations({subtree:true}).length') == 0
            # Use real elapsed time for the long-wait state.
            await expect(page.locator('.site-loading-retry')).to_be_visible(timeout=12000)
            await page.locator('.site-loading-retry').focus()
            assert await page.locator('.site-loading-retry').evaluate('el => el.href') == BASE + path
            await page.screenshot(path=str(OUT / f'slow-{chunk}.png'))
            release.set()
            await expect(page.locator(ready).first).to_be_visible()
            await hidden(page)
            await page.wait_for_function('document.activeElement === document.querySelector("main")')
            await context.close()
        print('Nested tools/games: long waits, retry target, reduced motion and focus recovery passed.', flush=True)

        # Entry failure and route failure must offer explicit retry, without reload loops.
        for failure_kind in ['entry', 'stylesheet', 'route']:
            entry = failure_kind != 'route'
            context, page = await context_for(failures=True)
            documents = []
            page.on('request', lambda request: documents.append(request.url) if request.resource_type == 'document' else None)
            pattern = re.compile({
                'entry': r'/assets/.*\.js$',
                'stylesheet': r'/assets/index-.*\.css$',
                'route': r'/assets/ProjectDirectory-.*\.js$',
            }[failure_kind])

            async def fail(route):
                await route.abort()

            if not entry:
                await page.goto(BASE, wait_until='networkidle')
            await page.route(pattern, fail)
            if entry:
                await page.goto(BASE, wait_until='commit')
            else:
                await navigate(page, '/project')
            await expect(page.locator('#site-loading')).to_have_attribute('data-state', 'error')
            await expect(page.locator('.site-loading-retry')).to_be_visible()
            assert len(documents) == 1, documents
            await page.screenshot(path=str(OUT / f'failure-{failure_kind}.png'))
            await page.unroute(pattern, fail)
            await page.locator('.site-loading-retry').click()
            await expect(page.locator('.hero' if entry else '.directory-toolbar')).to_be_visible()
            await hidden(page)
            await context.close()
        assert not errors, errors
        await browser.close()
        print('Entry/route failures and full-page retries passed. Screenshots: artifacts/loading/', flush=True)


asyncio.run(main())
