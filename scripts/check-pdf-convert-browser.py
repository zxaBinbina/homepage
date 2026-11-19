"""Check real PDF conversion downloads, cancellation and all website themes."""
import io
import os
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from PIL import Image, ImageDraw, ImageStat
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:4173').rstrip('/')
out = Path('artifacts/pdf-convert'); out.mkdir(parents=True, exist_ok=True)
fixture = Path('scripts/fixtures/pdf-convert.pdf')
writer = PdfWriter()
for pdf_page in PdfReader(fixture).pages:
    writer.add_page(pdf_page)
writer.encrypt('secret', algorithm='RC4-128')
encrypted = out / 'encrypted.pdf'
with encrypted.open('wb') as stream:
    writer.write(stream)
image = Image.new('RGB', (600, 800), '#f7f0dc')
draw = ImageDraw.Draw(image)
draw.rectangle((40, 80, 560, 480), fill='#bb4a32')
draw.text((60, 50), 'SCANNED PAGE', fill='black')
scan = out / 'scan.pdf'
c = canvas.Canvas(str(scan), pagesize=(600, 800))
c.drawImage(ImageReader(image), 0, 0, width=600, height=800)
c.save()

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce', permissions=['clipboard-read', 'clipboard-write'])
    context.add_init_script('''
      window.__pdfTerminated = 0; window.__delayPdf = false;
      const NativeWorker = Worker;
      window.Worker = class extends NativeWorker {
        constructor(url, options) { super(url, options); this.pdfExport = String(url).includes('convert.worker'); }
        postMessage(message, options) {
          if (this.pdfExport && window.__delayPdf) setTimeout(() => super.postMessage(message, options), 1500);
          else super.postMessage(message, options);
        }
        terminate() { if (this.pdfExport) window.__pdfTerminated++; super.terminate(); }
      };
    ''')
    page = context.new_page()
    errors, external, downloads = [], [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda request: external.append(request.url) if request.url.startswith(('http:', 'https:')) and not request.url.startswith(base) else None)
    page.on('download', lambda download: downloads.append(download.suggested_filename))

    def open_tool(tool):
        page.goto(base + '/tools/pdf-to-' + tool)
        expect(page.locator('.pdfconv-panel')).to_be_visible()

    def start(path=fixture):
        page.get_by_label('选择 PDF', exact=True).set_input_files(path)
        page.get_by_role('button', name='开始转换', exact=True).click()

    def download(extension, label):
        button = page.get_by_role('button', name='下载 .' + extension, exact=True)
        expect(button).to_be_visible(timeout=60000)
        with page.expect_download() as pending:
            button.click()
        output = out / (label + '.' + extension)
        pending.value.save_as(output)
        assert output.stat().st_size > 50
        return output

    def archive(path):
        z = zipfile.ZipFile(path)
        assert z.testzip() is None
        assert '[Content_Types].xml' in z.namelist()
        return z

    open_tool('markdown'); start()
    markdown = download('md', 'converted').read_text()
    assert '# 季度销售报告' in markdown and '| 华东 | 1,200 |' in markdown
    assert '1. 编号列表第一项' in markdown and '<!-- PAGE_BREAK -->' in markdown
    page.get_by_role('button', name='复制 Markdown', exact=True).click()
    expect(page.get_by_role('button', name='已复制', exact=True)).to_be_visible()
    assert page.evaluate('navigator.clipboard.readText()') == markdown
    assert page.locator('.pdfconv-preview').bounding_box()['height'] >= 320
    page.screenshot(path=str(out / 'markdown-desktop.png'), full_page=True)
    page.get_by_label('保留页间分隔').uncheck()
    expect(page.get_by_role('button', name='下载 .md')).to_have_count(0)
    page.get_by_role('button', name='开始转换', exact=True).click()
    assert '<!-- PAGE_BREAK -->' not in download('md', 'no-page-breaks').read_text()

    open_tool('word'); start()
    word = archive(download('docx', 'editable'))
    xml = word.read('word/document.xml').decode()
    assert '季度销售报告' in xml and xml.count('<w:tbl>') == 2
    assert '编号列表第一项' in xml

    open_tool('excel'); start()
    excel = archive(download('xlsx', 'tables'))
    assert len([name for name in excel.namelist() if re.fullmatch(r'xl/worksheets/sheet\d+\.xml', name)]) == 2
    assert '华东' in ''.join(excel.read(name).decode() for name in excel.namelist() if name.endswith('.xml'))
    page.get_by_label('识别普通数字（编号保持为文字）').check()
    page.get_by_label('工作表布局').select_option('single')
    page.get_by_role('button', name='开始转换', exact=True).click()
    numeric = archive(download('xlsx', 'combined-numeric'))
    assert '<v>1200</v>' in numeric.read('xl/worksheets/sheet1.xml').decode()

    open_tool('powerpoint'); start()
    ppt = archive(download('pptx', 'page-images'))
    slides = [name for name in ppt.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml', name)]
    assert len(slides) == 2 and all('<p:pic>' in ppt.read(name).decode() for name in slides)
    media = [name for name in ppt.namelist() if name.startswith('ppt/media/') and name.endswith('.jpeg')]
    if not media:
        media = [name for name in ppt.namelist() if name.startswith('ppt/media/') and name.endswith('.jpg')]
    assert len(media) >= 2
    for name in media:
        im = Image.open(io.BytesIO(ppt.read(name)))
        assert im.width >= 1199 and max(ImageStat.Stat(im).stddev) > 5
    page.get_by_label('转换模式').select_option('text')
    page.get_by_role('button', name='开始转换', exact=True).click()
    text_ppt = archive(download('pptx', 'editable-text'))
    assert '季度销售报告' in text_ppt.read('ppt/slides/slide1.xml').decode()
    assert '<p:pic>' not in text_ppt.read('ppt/slides/slide1.xml').decode()

    # Scan-only documents must fail clearly in text mode and work in image mode.
    open_tool('markdown'); start(scan)
    expect(page.get_by_role('alert')).to_contain_text('没有可提取的文字层', timeout=60000)
    open_tool('word')
    page.get_by_label('转换模式').select_option('image'); start(scan)
    scan_word = archive(download('docx', 'scanned-image'))
    assert any(name.startswith('word/media/') for name in scan_word.namelist())
    open_tool('powerpoint'); start(scan)
    scan_ppt = archive(download('pptx', 'scanned-image'))
    assert '<p:pic>' in scan_ppt.read('ppt/slides/slide1.xml').decode()

    open_tool('markdown'); start(encrypted)
    expect(page.get_by_role('alert')).to_contain_text('打开密码', timeout=60000)
    page.get_by_label('打开密码（仅加密文件需要）').fill('wrong')
    page.get_by_role('button', name='开始转换', exact=True).click()
    expect(page.get_by_role('alert')).to_contain_text('打开密码', timeout=60000)
    page.get_by_label('打开密码（仅加密文件需要）').fill('secret')
    page.get_by_role('button', name='开始转换', exact=True).click()
    assert '季度销售报告' in download('md', 'decrypted').read_text()
    page.get_by_role('button', name='取消并清空', exact=True).click()
    expect(page.get_by_label('打开密码（仅加密文件需要）')).to_have_value('')
    expect(page.get_by_role('button', name='开始转换', exact=True)).to_be_disabled()

    page.get_by_label('选择 PDF', exact=True).set_input_files({'name': 'bad.pdf', 'mimeType': 'application/pdf', 'buffer': b'not a pdf'})
    page.get_by_role('button', name='开始转换', exact=True).click()
    expect(page.get_by_role('alert')).to_contain_text('无法读取', timeout=60000)
    page.get_by_label('选择 PDF', exact=True).set_input_files(fixture)
    page.get_by_label('开始页', exact=True).fill('3')
    page.get_by_role('button', name='开始转换', exact=True).click()
    expect(page.get_by_role('alert')).to_contain_text('共 2 页', timeout=60000)
    page.get_by_label('开始页', exact=True).fill('2')
    page.get_by_label('结束页（留空为末页）').fill('2')
    page.get_by_role('button', name='开始转换', exact=True).click()
    partial = download('md', 'second-page').read_text()
    assert 'Second Page Title' in partial and '季度销售报告' not in partial

    # Hold the real export worker before it receives content; clearing, option
    # changes and route departure must terminate it and suppress stale results.
    for action in ['clear', 'option', 'leave']:
        open_tool('markdown')
        page.evaluate('window.__delayPdf = true')
        start()
        expect(page.locator('.pdfconv-status')).to_contain_text('正在整理内容', timeout=60000)
        count = page.evaluate('window.__pdfTerminated')
        previous_downloads = len(downloads)
        if action == 'clear': page.get_by_role('button', name='取消并清空', exact=True).click()
        elif action == 'option': page.get_by_label('保留页间分隔').uncheck()
        else: page.get_by_role('link', name='全部工具', exact=True).click()
        page.wait_for_timeout(1800)
        assert page.evaluate('window.__pdfTerminated') > count
        assert len(downloads) == previous_downloads
        expect(page.get_by_role('button', name='下载 .md')).to_have_count(0)

    for tool in ['word', 'excel', 'powerpoint', 'markdown']:
        open_tool(tool)
        for theme in ['dark', 'light']:
            for palette in ['fufu-blue', 'hutao-red']:
                page.evaluate('''([theme, palette]) => {
                  document.documentElement.dataset.theme = theme;
                  document.documentElement.dataset.palette = palette;
                }''', [theme, palette])
                for width in [320, 390, 768, 1024, 1440]:
                    page.set_viewport_size({'width': width, 'height': 1000})
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (tool, theme, palette, width)
                page.set_viewport_size({'width': 390, 'height': 1000})
                page.screenshot(path=str(out / f'{tool}-{palette}-{theme}.png'), full_page=True)
    assert not external, external
    assert not errors, errors
    context.close(); browser.close()
print('PDF conversion browser checks passed: DOCX/XLSX/PPTX/Markdown downloads, image and text modes, scans, passwords, page ranges, cancellation, four themes and five widths.')
