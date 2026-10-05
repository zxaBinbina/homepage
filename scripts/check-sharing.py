"""Check the HTML that a social crawler receives, without executing JavaScript."""
from html.parser import HTMLParser
from pathlib import Path
import sys
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
    '网页工具 · a彬彬a': 'tool',
    'JSON 格式化 · 网页工具 · a彬彬a': 'tools/json',
    'Base64 编解码 · 网页工具 · a彬彬a': 'tools/base64',
    'URL 编解码 · 网页工具 · a彬彬a': 'tools/url',
    '时间戳转换 · 网页工具 · a彬彬a': 'tools/timestamp',
    'UUID 生成 · 网页工具 · a彬彬a': 'tools/uuid',
    '文本整理 · 网页工具 · a彬彬a': 'tools/text',
    '进制转换 · 网页工具 · a彬彬a': 'tools/radix',
    '哈希计算 · 网页工具 · a彬彬a': 'tools/hash',
    'JWT 解析 · 网页工具 · a彬彬a': 'tools/jwt',
    '密码生成 · 网页工具 · a彬彬a': 'tools/password',
    'HTML 实体转换 · 网页工具 · a彬彬a': 'tools/html',
    '颜色转换 · 网页工具 · a彬彬a': 'tools/color',
    '项目目录 · a彬彬a': 'project',
    'a彬彬a · 在代码与方块之间': '',
    'RDP Access Auth · 远程桌面，先认证再连接': 'projects/rdp-access-auth',
    '部署与维护 Wiki · RDP Access Auth': 'projects/rdp-access-auth/wiki',
    '下载发行版 · RDP Access Auth': 'projects/rdp-access-auth/downloads',
}
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
