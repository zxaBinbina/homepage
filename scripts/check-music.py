"""Verify production player UI with a temporary Vite lyrics server and real audio."""
import io
import json
import math
import mimetypes
import os
from pathlib import Path
import signal
import struct
import subprocess
import time
from urllib.parse import urlparse
from urllib.request import urlopen
import wave
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'artifacts'
OUT.mkdir(exist_ok=True)
MUSIC = json.loads((ROOT / 'src/data/music.json').read_text())
DEFAULT_INDEX = next(i for i,t in enumerate(MUSIC['tracks']) if t['id'] == MUSIC['defaultTrackId'])
NEXT_TRACK = MUSIC['tracks'][DEFAULT_INDEX + 1]
PORT = 5187
buffer = io.BytesIO()
with wave.open(buffer,'wb') as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(8000)
    wav.writeframes(b''.join(struct.pack('<h', int(400 * math.sin(2 * math.pi * 220 * i / 8000))) for i in range(8000 * 8)))

log = (OUT / 'music-vite.log').open('w')
server = subprocess.Popen(['npm','run','dev','--','--port',str(PORT),'--strictPort'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
try:
    for attempt in range(60):
        try:
            urlopen(f'http://127.0.0.1:{PORT}',timeout=1).close()
            break
        except Exception:
            if server.poll() is not None: raise RuntimeError('Vite exited; see artifacts/music-vite.log')
            time.sleep(.25)
    else: raise RuntimeError('Vite startup timed out')
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER','/usr/bin/google-chrome'),headless=True,args=['--no-sandbox'])
        context = browser.new_context(viewport={'width':1440,'height':1000})
        def site(route):
            parsed = urlparse(route.request.url)
            if parsed.path == '/api/music/lyrics':
                response = route.fetch(url=f'http://127.0.0.1:{PORT}{parsed.path}?{parsed.query}')
                route.fulfill(response=response)
                return
            relative = parsed.path.lstrip('/') or 'index.html'
            path = (ROOT/'dist'/relative).resolve()
            assert path.is_relative_to(ROOT/'dist')
            route.fulfill(path=path,content_type=mimetypes.guess_type(path)[0] or 'application/octet-stream')
        context.route('https://homepage.test/**',site)
        page = context.new_page()
        errors=[]
        requests=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.on('request',lambda request:requests.append(request.url))
        page.goto('https://homepage.test/',wait_until='networkidle')
        assert page.locator('.music-card').count()==0
        assert not any('/song/media/' in url or '/api/music/lyrics' in url for url in requests)
        assert page.locator('.theme-toggle').evaluate('(e)=>e.nextElementSibling.classList.contains("music-toggle")')
        assert page.locator('.theme-toggle').get_attribute('title')=='切换浅色主题'
        assert page.locator('.header-actions a.icon-button').get_attribute('title')=='GitHub'
        assert page.locator('.music-toggle').get_attribute('title')=='网易云音乐'
        page.get_by_role('button',name='打开网易云音乐播放器',exact=True).click()
        assert page.locator('.music-popover').evaluate('(e)=>e.matches(":popover-open")')
        assert page.locator('.music-info h3').inner_text()=='飞鼠进行曲 The Parade of Flying Squirrels'
        assert page.locator('.music-title-row .music-vip').count()==0
        page.get_by_text('纯音乐，请欣赏',exact=True).wait_for(timeout=20000)
        player_height=page.locator('.music-popover').bounding_box()['height']
        lyrics_height=page.locator('.music-lyrics').bounding_box()['height']
        page.get_by_role('button',name='展开或收起歌单',exact=True).click()
        assert page.locator('.music-track').count()==MUSIC['total']
        assert page.locator('.music-list-heading button').count()==0
        page.wait_for_timeout(250)
        left=page.locator('.music-player-body').bounding_box()
        right=page.locator('.music-playlist').bounding_box()
        assert right['x'] >= left['x'] + left['width'] - 1
        assert abs(right['y'] - left['y']) < 2
        page.screenshot(path=str(OUT/'music-sidebar.png'),animations='disabled')
        names=page.locator('.music-track-name>span:first-child').all_text_contents()
        assert names==[track['title'] for track in MUSIC['tracks']]
        assert page.locator('.music-track[aria-pressed=true] .music-track-name').inner_text().startswith('飞鼠')
        assert page.locator('.music-track').first.locator('.music-vip').inner_text()=='VIP'
        page.get_by_role('button',name='展开或收起歌单',exact=True).click()
        page.wait_for_timeout(250)
        assert page.locator('.music-popover').evaluate('(e)=>e.getBoundingClientRect().width<=380')
        assert page.evaluate('document.body.style.overflow')!='hidden'
        page.screenshot(path=str(OUT/'music-desktop.png'),animations='disabled')
        page.get_by_role('button',name='播放音乐',exact=True).click()
        page.wait_for_function('document.querySelector("audio").currentTime>.4&&!document.querySelector("audio").paused',timeout=45000)
        assert page.locator('audio').evaluate('(audio)=>audio.duration')>60
        assert page.locator('.music-toggle').evaluate('(e)=>e.classList.contains("is-playing")')
        track=MUSIC['tracks'][DEFAULT_INDEX]
        assert page.locator('.music-toggle').get_attribute('title')==f"正在播放：{track['title']} - {track['artist']}"
        old_time=page.locator('audio').evaluate('(e)=>e.currentTime')
        page.get_by_role('button',name='关闭音乐播放器',exact=True).click()
        page.wait_for_timeout(500)
        assert page.locator('audio').evaluate('(e)=>!e.paused&&e.currentTime')>old_time
        assert page.evaluate('document.body.style.overflow')!='hidden'
        assert page.locator('.music-toggle').evaluate('(e)=>e===document.activeElement')
        page.get_by_role('button',name='打开网易云音乐播放器',exact=True).click()
        page.get_by_role('button',name='暂停音乐',exact=True).click()
        assert page.locator('.music-toggle').get_attribute('title')=='网易云音乐'
        page.get_by_role('slider',name='播放进度').fill('30')
        assert page.locator('audio').evaluate('(e)=>Math.abs(e.currentTime-30)<2')
        print('LIVE: default HTTPS audio, pure-music lyrics, original playlist order, VIP badges, and playback across dialog close/reopen passed.',flush=True)

        page.route('**/song/media/outer/url?*',lambda route:route.fulfill(status=200,content_type='audio/wav',body=buffer.getvalue()))
        page.route('**/api/music/lyrics?*',lambda route:route.fulfill(json={'instrumental':False,'lyric':'[00:00.00]测试第一句\n[00:01.00]测试第二句\n[00:04.00]测试第三句','translation':''}))
        page.get_by_role('button',name='下一首',exact=True).click()
        page.wait_for_function('document.querySelector("audio").currentTime>1.2')
        assert page.locator('.music-info h3').inner_text()==NEXT_TRACK['title']
        assert page.locator('.music-toggle').get_attribute('title')==f"正在播放：{NEXT_TRACK['title']} - {NEXT_TRACK['artist']}"
        assert abs(page.locator('.music-popover').bounding_box()['height']-player_height)<1
        page.wait_for_function('document.querySelector(".lyric-line[data-active=true]")?.textContent.trim() === "测试第二句"',timeout=3000)
        page.get_by_role('button',name='暂停音乐',exact=True).click()
        page.locator('.lyric-line').first.click()
        assert page.locator('audio').evaluate('(e)=>e.currentTime')<.1
        page.wait_for_function('document.querySelector(".lyric-line[data-active=true]")?.textContent.trim() === "测试第一句"',timeout=3000)
        page.get_by_role('button',name='播放音乐',exact=True).click()
        expected=MUSIC['tracks'][DEFAULT_INDEX+2]['title']
        page.wait_for_function('(name)=>document.querySelector(".music-info h3").textContent.trim()===name',arg=expected,timeout=12000)
        page.get_by_role('button',name='暂停音乐',exact=True).click()
        page.get_by_role('button',name='展开或收起歌单',exact=True).click()
        page.get_by_role('searchbox',name='搜索歌单').fill('Whistle')
        page.locator('.music-track').first.click()
        page.wait_for_function('document.querySelector("audio").currentTime>.1')
        assert page.locator('.music-title-row .music-vip').inner_text()=='VIP'
        page.get_by_role('slider',name='音量',exact=True).fill('0.3')
        assert abs(page.locator('audio').evaluate('(e)=>e.volume')-.3)<.01
        page.get_by_role('button',name='静音',exact=True).click()
        assert page.locator('audio').evaluate('(e)=>e.muted')
        page.get_by_role('button',name='取消静音',exact=True).click()
        page.get_by_role('button',name='暂停音乐',exact=True).click()
        page.screenshot(path=str(OUT/'music-lyrics.png'))
        page.get_by_role('button',name='展开或收起歌单',exact=True).click()
        print('Mocked audio/lyrics: original-order next/ended, timed highlighting, lyric seeking, search, VIP current title, volume and mute passed.',flush=True)

        page.unroute('**/song/media/outer/url?*')
        page.route('**/song/media/outer/url?*',lambda route:route.abort('failed'))
        page.unroute('**/api/music/lyrics?*')
        page.route('**/api/music/lyrics?*',lambda route:route.fulfill(status=503,json={'error':'unavailable'}))
        page.get_by_role('button',name='下一首',exact=True).click()
        page.locator('.music-error').wait_for()
        page.get_by_role('button',name='重试',exact=True).wait_for()
        assert abs(page.locator('.music-lyrics').bounding_box()['height']-lyrics_height)<1
        page.unroute('**/api/music/lyrics?*')
        page.route('**/api/music/lyrics?*',lambda route:route.fulfill(json={'instrumental':False,'lyric':'','translation':''}))
        page.get_by_role('button',name='重试',exact=True).click()
        page.get_by_text('暂无歌词，让旋律继续。',exact=True).wait_for()
        assert abs(page.locator('.music-lyrics').bounding_box()['height']-lyrics_height)<1
        page.keyboard.press('Escape')
        assert not page.locator('.music-popover').evaluate('(e)=>e.matches(":popover-open")')
        print('Playback failure, lyric failure/retry/empty state and Escape passed.',flush=True)

        for width in [320,390,768,1024,1440]:
            page.set_viewport_size({'width':width,'height':844})
            assert page.locator('.music-toggle').is_visible()
            page.get_by_role('button',name='打开网易云音乐播放器',exact=True).click()
            page.wait_for_timeout(300)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),f'page overflow at {width}'
            assert page.locator('.music-popover').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1'),f'dialog overflow at {width}'
            assert page.locator('.music-popover').evaluate('(e)=>e.getBoundingClientRect().width<=innerWidth')
            page.get_by_role('button',name='展开或收起歌单',exact=True).click()
            page.wait_for_timeout(250)
            assert page.locator('.music-popover').evaluate('(e)=>e.getBoundingClientRect().right<=innerWidth')
            assert page.locator('.music-popover').evaluate('(e)=>e.getBoundingClientRect().left>=0')
            if width<720:
                assert page.locator('.music-player-body').evaluate('(e)=>e.inert')
                page.screenshot(path=str(OUT/f'music-sidebar-{width}.png'),animations='disabled')
            if width<720:
                page.locator('.playlist-scrim').click(position={'x':8,'y':40})
            else:
                page.get_by_role('button',name='展开或收起歌单',exact=True).click()
            page.keyboard.press('Escape')
        page.set_viewport_size({'width':390,'height':844})
        page.get_by_role('button',name='打开网易云音乐播放器',exact=True).click()
        page.screenshot(path=str(OUT/'music-mobile.png'), animations='disabled')
        page.keyboard.press('Escape')
        dark_fill=page.locator('.music-toggle svg').evaluate('(e)=>getComputedStyle(e).fill')
        page.get_by_role('button',name='切换浅色主题',exact=True).click()
        assert page.locator('.theme-toggle').get_attribute('title')=='切换深色主题'
        assert page.locator('.music-toggle svg').evaluate('(e)=>getComputedStyle(e).fill')!=dark_fill
        page.get_by_role('button',name='打开网易云音乐播放器',exact=True).click()
        page.screenshot(path=str(OUT/'music-mobile-light.png'), animations='disabled')
        page.get_by_role('button',name='打开网易云音乐播放器',exact=True).click()
        assert not page.locator('.music-popover').evaluate('(e)=>e.matches(":popover-open")')
        page.get_by_role('button',name='打开网易云音乐播放器',exact=True).click()
        page.mouse.click(3,800)
        assert not page.locator('.music-popover').evaluate('(e)=>e.matches(":popover-open")')
        assert not errors,errors
        print('320–1440px dialog/navigation layouts, light theme, and no JavaScript errors passed.',flush=True)
        browser.close()
finally:
    if server.poll() is None: os.killpg(server.pid,signal.SIGTERM)
    server.wait(timeout=10)
    log.close()
