"""Check the HTML that a social crawler receives, without executing JavaScript."""
from html.parser import HTMLParser
from pathlib import Path
import sys
import json
import subprocess
from urllib.parse import urlparse

class Head(HTMLParser):
    def __init__(self):
        super().__init__()
        self.metas = []
        self.links = []
        self.title = ''
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta': self.metas.append(attrs)
        if tag == 'link': self.links.append(attrs)
        if tag == 'title': self.in_title = True

    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False

    def handle_data(self, data):
        if self.in_title: self.title += data

pages = {
    '小游戏 · a彬彬a': 'game',
    '2048 · 小游戏 · a彬彬a': 'games/2048',
    '扫雷 · 小游戏 · a彬彬a': 'games/minesweeper',
    '纸牌接龙 · 小游戏 · a彬彬a': 'games/solitaire',
    '俄罗斯方块 · 小游戏 · a彬彬a': 'games/tetris',
    '数独经典版 · 小游戏 · a彬彬a': 'games/sudoku',
    '中国象棋单机版 · 小游戏 · a彬彬a': 'games/xiangqi',
    '五子棋单机版 · 小游戏 · a彬彬a': 'games/gomoku',
    '国际象棋单机版 · 小游戏 · a彬彬a': 'games/chess',
    '围棋 · 小游戏 · a彬彬a': 'games/go',
    '贪吃蛇 · 小游戏 · a彬彬a': 'games/snake',
    '消灭星星经典版 · 小游戏 · a彬彬a': 'games/popstar',
    '华容道 · 小游戏 · a彬彬a': 'games/huarongdao',
    '跳一跳 · 小游戏 · a彬彬a': 'games/jump',
    '网页工具 · a彬彬a': 'tool',
    '项目目录 · a彬彬a': 'project',
    'a彬彬a · 在代码与方块之间': '',
    'RDP Access Auth · 远程桌面，先认证再连接': 'projects/rdp-access-auth',
    '部署与维护 Wiki · RDP Access Auth': 'projects/rdp-access-auth/wiki',
    '下载发行版 · RDP Access Auth': 'projects/rdp-access-auth/downloads',
    '400 · 这个请求有点不对劲 · a彬彬a': '400',
    '401 · 先确认一下你的身份 · a彬彬a': '401',
    '403 · 这片区域暂未开放 · a彬彬a': '403',
    '404 · 这块世界，还没有生成 · a彬彬a': '404',
    '408 · 这次等待有点久 · a彬彬a': '408',
    '429 · 慢一点，风景还在 · a彬彬a': '429',
    '500 · 方块之间，出了点小差错 · a彬彬a': '500',
    '502 · 通往这里的桥暂时断了 · a彬彬a': '502',
    '503 · 世界正在稍作休息 · a彬彬a': '503',
    '504 · 远方的回应，还没到达 · a彬彬a': '504',
}
pages.update({t['name'] + ' · 网页工具 · a彬彬a': t['path'].lstrip('/')
              for t in json.loads(subprocess.check_output(['node', 'scripts/list-tools.mjs']))})

paths = [Path(sys.argv[1])] if len(sys.argv) > 1 else [Path('dist') / (f'{route}.html' if route else 'index.html') for route in pages.values()]
for path in paths:
    html = path.read_text()
    assert '<%=' not in html and '%BASE_URL%' not in html, 'Unrendered template token'
    head = Head()
    head.feed(html)

    def meta(key, value):
        matches = [tag for tag in head.metas if tag.get(key) == value]
        assert len(matches) == 1, f'Expected exactly one {key}={value}'
        assert matches[0].get('content'), f'Empty {value}'
        return matches[0]['content']

    title = head.title.strip()
    assert title in pages, title
    assert meta('name', 'robots') == ('noindex' if pages[title].isdigit() else 'index, follow, max-image-preview:large')
    assert meta('property', 'og:title') == meta('itemprop', 'name') == title
    description = meta('name', 'description')
    assert meta('property', 'og:description') == meta('itemprop', 'description') == description
    image = meta('property', 'og:image')
    assert image == meta('itemprop', 'image') == meta('property', 'og:image:secure_url')
    project = pages[title].startswith('projects/rdp-access-auth')
    image_path = 'images/rdp-access-auth.png' if project else 'images/share-avatar.jpg'
    assert image == 'https://zxabinbina.cc.cd/' + image_path
    assert urlparse(image).scheme == 'https' and urlparse(image).netloc
    assert meta('property', 'og:image:type') == ('image/png' if project else 'image/jpeg')
    assert meta('property', 'og:image:width') == ('512' if project else '256')
    assert meta('property', 'og:image:height') == ('394' if project else '256')
    assert meta('property', 'og:image:alt') == ('RDP Access Auth 软件 Logo' if project else 'a彬彬a 的头像')
    canonical = 'https://zxabinbina.cc.cd/' + pages[title]
    assert meta('property', 'og:url') == canonical
    assert [link['href'] for link in head.links if link.get('rel') == 'canonical'] == [canonical]
    assert (Path('dist') / image_path).is_file()
    print(f'{path}: title/description reuse, absolute image URL, Open Graph, QQ tags and template rendering passed.')
