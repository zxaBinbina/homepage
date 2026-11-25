"""Smoke-test real Turnstile and multiplayer against a deployed Worker."""
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'https://zxabinbina.cc.cd').rstrip('/')
out = Path('artifacts/rooms/live')
out.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    native = None
    profile = None
    if os.environ.get('HOMEPAGE_NATIVE_BROWSER') == '1':
        profile = tempfile.mkdtemp(prefix='homepage-live-browser-')
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            port = listener.getsockname()[1]
        endpoint = 'http://127.0.0.1:' + str(port)
        native = subprocess.Popen([
            os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'),
            '--no-sandbox', '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=' + str(port),
            '--user-data-dir=' + profile, '--no-first-run', '--no-default-browser-check', 'about:blank',
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            try:
                with urllib.request.urlopen(endpoint + '/json/version', timeout=1): break
            except Exception: time.sleep(.2)
        browser = p.chromium.connect_over_cdp(endpoint)
    else:
        browser = p.chromium.launch(
            executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'),
            headless=os.environ.get('HOMEPAGE_HEADLESS', '1') != '0', args=['--no-sandbox'],
        )
    contexts = []
    pages = []
    errors = []

    def client(width):
        context = browser.new_context(viewport={'width': width, 'height': 1100}, reduced_motion='reduce', color_scheme='dark')
        contexts.append(context)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        pages.append(page)
        return page

    def visit(page):
        page.bring_to_front()
        page.goto(base + '/games/gomoku', wait_until='networkidle')
        page.get_by_role('radio', name='朋友联机', exact=True).click()

    def verify(page, operation):
        button = page.get_by_role('button', name=operation, exact=True)
        end = time.monotonic() + 90
        clicked = set()
        last_widget_click = time.monotonic()
        while time.monotonic() < end:
            if button.is_enabled(): return
            retry = page.get_by_role('button', name='重试验证', exact=True)
            if retry.count() and retry.is_visible():
                retry.click()
                last_widget_click = time.monotonic()
            for frame in page.frames:
                if 'challenges.cloudflare.com' not in frame.url or frame.url in clicked: continue
                checkbox = frame.get_by_role('checkbox')
                if checkbox.count() and checkbox.first.is_visible():
                    checkbox.first.click(timeout=2000)
                    clicked.add(frame.url)
                    last_widget_click = time.monotonic()
            # Managed widgets can place their iframe in a closed shadow root.
            # Click the visible checkbox using the widget's on-screen bounds.
            target = page.locator('.room-turnstile > div').first
            box = target.bounding_box()
            if box and box['height'] >= 60 and time.monotonic() - last_widget_click > 10:
                target.scroll_into_view_if_needed()
                box = target.bounding_box()
                page.mouse.click(box['x'] + 22, box['y'] + 32)
                last_widget_click = time.monotonic()
            page.wait_for_timeout(1000)
        page.screenshot(path=str(out / 'turnstile-pending.png'), full_page=True)
        raise AssertionError('Real Turnstile did not finish: ' + page.locator('.room-turnstile').inner_text())

    def leave(page):
        if page.get_by_role('button', name='离开房间', exact=True).count():
            page.get_by_role('button', name='离开房间', exact=True).click()
            expect(page.get_by_role('dialog', name='确认离开房间？', exact=True)).to_be_visible()
            expect(page.locator('.room-leave-popover')).to_be_visible()
            page.get_by_role('button', name='确认离开', exact=True).click()
            expect(page.get_by_role('radio', name='单机对战', exact=True)).to_have_attribute('aria-checked', 'true')

    try:
        host, guest = client(1440), client(390)
        visit(host)
        host.get_by_label('你的昵称', exact=True).fill('上线验证甲')
        verify(host, '创建房间')
        host.get_by_role('button', name='创建房间', exact=True).click()
        expect(host.locator('.room-number')).to_be_visible(timeout=30000)
        code = re.search(r'\d{6}', host.locator('.room-number').inner_text()).group()
        print('Real Turnstile and server-side create: passed.', flush=True)

        visit(guest)
        guest.get_by_role('radio', name='加入房间', exact=True).click()
        guest.get_by_label('你的昵称', exact=True).fill('上线验证乙')
        guest.get_by_label('6 位数字房间号', exact=True).fill(code)
        verify(guest, '加入房间')
        guest.get_by_role('button', name='加入房间', exact=True).click()
        expect(guest.locator('.room-number')).to_contain_text(code, timeout=30000)
        host.get_by_role('button', name='我准备好了', exact=True).click()
        guest.get_by_role('button', name='我准备好了', exact=True).click()
        host.get_by_role('button', name='开始对局', exact=True).click()
        expect(guest.locator('.room-board')).to_be_visible()
        host.locator('.room-board [data-at="112"]').click()
        host.get_by_role('button', name='确认落子', exact=True).click()
        expect(guest.locator('.room-board .strategy-piece')).to_have_count(1)
        guest.locator('.room-board [data-at="113"]').click()
        guest.get_by_role('button', name='确认落子', exact=True).click()
        expect(host.locator('.room-board .strategy-piece')).to_have_count(2)
        host.get_by_role('button', name='悔棋', exact=True).click()
        guest.get_by_role('button', name='同意', exact=True).click()
        expect(host.locator('.room-board .strategy-piece')).to_have_count(0)
        for page in (host, guest): page.get_by_role('button', name='房间聊天', exact=False).click()
        host.get_by_label('聊天消息').fill('线上联机验证')
        host.get_by_role('button', name='发送消息').click()
        expect(guest.locator('.room-chat-log')).to_contain_text('线上联机验证')
        host.reload(wait_until='networkidle')
        expect(host.locator('.room-number')).to_contain_text(code)
        expect(host.locator('.room-toolbar .strategy-turn')).to_have_text('轮到你了', timeout=30000)
        host.locator('.room-surface').screenshot(path=str(out / 'game-desktop.png'))
        guest.locator('.room-surface').screenshot(path=str(out / 'game-mobile.png'))
        leave(host)
        expect(guest.locator('.game-result')).to_be_visible()
        leave(guest)
        assert not errors, errors
        print('Real join, readiness, two independent players, moves, undo consent, chat, refresh reconnection and leave: passed.', flush=True)
    finally:
        for page in pages:
            try: leave(page)
            except Exception: pass
        for context in contexts: context.close()
        browser.close()
        if native:
            native.terminate()
            native.wait(timeout=10)
        if profile: shutil.rmtree(profile, ignore_errors=True)
