"""Validate crawler metadata and sitemap coverage in the production output."""
import json
import os
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
import xml.etree.ElementTree as ET


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.canonical = []
        self.robots = []
        self.structured = []
        self.in_structured = False
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonical.append(attrs['href'])
        if tag == 'meta' and attrs.get('name') == 'robots':
            self.robots.append(attrs['content'])
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.in_structured = True

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_structured = False

    def handle_data(self, data):
        if self.in_structured:
            self.structured.append(json.loads(data))


root = Path('dist')
base = os.environ.get('SITE_URL', 'https://zxabinbina.cc.cd/').rstrip('/') + '/'
sitemap = ET.parse(root / 'sitemap.xml')
urls = [node.text for node in sitemap.findall('{*}url/{*}loc')]
assert len(urls) == len(set(urls)), 'Duplicate sitemap URLs'
canonical_urls = []
for file in root.rglob('*.html'):
    if file.name == '404.html':
        assert Document(file.read_text()).robots == ['noindex']
        continue
    doc = Document(file.read_text())
    route = file.relative_to(root).as_posix().removesuffix('.html')
    expected = urljoin(base, '' if route == 'index' else route)
    assert doc.canonical == [expected], (file, doc.canonical)
    assert doc.robots == ['index, follow, max-image-preview:large'], file
    assert len(doc.structured) == 1, file
    data = doc.structured[0]
    assert data['@context'] == 'https://schema.org'
    website, page = data['@graph']
    assert website['url'] == base
    assert page['url'] == expected and page['name'] and page['description']
    assert page['isPartOf']['@id'] == website['@id']
    canonical_urls.append(expected)
assert len(canonical_urls) == 22, canonical_urls
assert set(urls) == set(canonical_urls), 'Sitemap must contain all canonical pages only'
robots = (root / 'robots.txt').read_text()
assert 'User-agent: *\nAllow: /' in robots
assert f'Sitemap: {urljoin(base, "sitemap.xml")}' in robots
assert (root / '404.html').is_file()
print(f'SEO checks passed: {len(urls)} canonical pages, JSON-LD, robots, sitemap and noindex 404.')
