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
    '项目目录 · a彬彬a': 'project/',
    'a彬彬a · 在代码与方块之间': '',
    'RDP Access Auth · 远程桌面，先认证再连接': 'projects/rdp-access-auth/',
    '部署与维护 Wiki · RDP Access Auth': 'projects/rdp-access-auth/wiki/',
}
paths = [Path(sys.argv[1])] if len(sys.argv) > 1 else [Path('dist') / route / 'index.html' for route in pages.values()]
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
    assert image == 'https://zxabinbina.cc.cd/images/share-cover.jpg'
    assert urlparse(image).scheme == 'https' and urlparse(image).netloc
    assert meta('property', 'og:image:type') == 'image/jpeg'
    assert meta('property', 'og:image:width') == '1200'
    assert meta('property', 'og:image:height') == '630'
    canonical = 'https://zxabinbina.cc.cd/' + pages[title]
    assert meta('property', 'og:url') == canonical
    assert [link['href'] for link in head.links if link.get('rel') == 'canonical'] == [canonical]
    assert Path('dist/images/share-cover.jpg').is_file()
    print(f'{path}: title/description reuse, absolute image URL, Open Graph, QQ tags and template rendering passed.')
