"""Slow first paint and fullscreen transitions must never expose a wrong-theme canvas."""
import asyncio
import os
import re
from pathlib import Path
from playwright.async_api import async_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:4173').rstrip('/')
out = Path('artifacts')
out.mkdir(exist_ok=True)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
        errors = []
        for theme in ['light', 'dark']:
            for game in ['2048', 'minesweeper', 'solitaire']:
                context = await browser.new_context(viewport={'width':1440,'height':1000}, color_scheme='dark' if theme == 'light' else 'light', reduced_motion='no-preference')
                await context.add_init_script(f'localStorage.setItem("homepage-theme", "{theme}"); Math.random=()=>0')
                page = await context.new_page()
                page.on('pageerror', lambda error: errors.append(str(error)))
                ready = asyncio.Event()
                async def slow_script(route):
                    await ready.wait()
                    await route.continue_()
                await page.route(re.compile(r'/assets/.*\.js(?:\?.*)?$'), slow_script)
                await page.goto(base + '/games/' + game, wait_until='commit')
                await page.wait_for_function('getComputedStyle(document.documentElement).getPropertyValue("--bg").trim() !== ""')
                await expect(page.locator('html')).to_have_attribute('data-theme', theme)
                await page.screenshot(path=str(out / f'game-paint-loading-{game}-{theme}.png'))
                canvas = await page.evaluate('''() => ({
                  root: getComputedStyle(document.documentElement).backgroundColor,
                  body: getComputedStyle(document.body).backgroundColor,
                  height: document.body.getBoundingClientRect().height,
                  viewport: innerHeight,
                })''')
                expected = 'rgb(244, 246, 250)' if theme == 'light' else 'rgb(20, 21, 33)'
                assert canvas['root'] == expected and canvas['body'] == expected, (game, theme, 'wrong loading background', canvas)
                assert canvas['height'] >= canvas['viewport'], (game, theme, 'short loading body', canvas)
                ready.set()
                await expect(page.locator('.game-surface')).to_be_visible()
                await page.wait_for_load_state('networkidle')
                await page.get_by_role('button', name='网页全屏', exact=True).scroll_into_view_if_needed()
                before = await page.evaluate('''() => ({
                  height:document.body.getBoundingClientRect().height,
                  footer:document.querySelector('footer').getBoundingClientRect().top + scrollY,
                  scroll:scrollY,
                })''')
                await page.get_by_role('button', name='网页全屏', exact=True).click()
                await page.locator('dialog[open]').evaluate('el => el.getAnimations().forEach(a => {a.pause(); a.currentTime=60})')
                during = await page.evaluate('''() => ({
                  height:document.body.getBoundingClientRect().height,
                  footer:document.querySelector('footer').getBoundingClientRect().top + scrollY,
                  scroll:scrollY,
                })''')
                assert abs(before['height']-during['height']) <= 1 and abs(before['footer']-during['footer']) <= 1, (game, theme, 'page collapsed under fullscreen fade', before, during)
                await page.screenshot(path=str(out / f'game-paint-enter-{game}-{theme}.png'))
                await page.locator('dialog[open]').evaluate('el => el.getAnimations().forEach(a => a.finish())')
                await page.get_by_role('button', name='退出全屏', exact=True).click()
                await page.locator('dialog[open]').evaluate('el => el.getAnimations().forEach(a => {a.pause(); a.currentTime=70})')
                await page.screenshot(path=str(out / f'game-paint-exit-{game}-{theme}.png'))
                await page.locator('dialog[open]').evaluate('el => el.getAnimations().forEach(a => a.finish())')
                await expect(page.locator('dialog[open]')).to_have_count(0)
                assert abs(await page.evaluate('scrollY') - before['scroll']) <= 1
                await context.close()
        assert not errors, errors
        await browser.close()
    print('Game first paint and fullscreen fades: both themes, delayed scripts, stable page/footer height and restored scrolling passed.')

asyncio.run(main())
