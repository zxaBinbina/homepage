"""Check real PDF conversion downloads, cancellation and all website themes."""
import io
import os
import re
import zipfile
from pathlib import Path
from urllib.parse import urlparse
import json
from xml.etree import ElementTree as ET
from PIL import Image, ImageDraw, ImageStat
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from playwright.sync_api import sync_playwright, expect
from browser_theme import set_theme_mode

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

def text_pdf(lines):
    escape = lambda text: text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
    stream = ('BT /F1 12 Tf 40 740 Td 22 TL ' + ' T* '.join(f'({escape(line)}) Tj' for line in lines) + ' ET').encode()
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>', b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
      b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>',
      b'<< /Length ' + str(len(stream)).encode() + b' >>\nstream\n' + stream + b'\nendstream',
      b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>']
    data = b'%PDF-1.4\n'; offsets = []
    for index, obj in enumerate(objects, 1):
        offsets.append(len(data)); data += f'{index} 0 obj\n'.encode() + obj + b'\nendobj\n'
    start = len(data)
    data += b'xref\n0 6\n0000000000 65535 f \n' + b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets)
    return data + f'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{start}\n%%EOF'.encode()

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce', permissions=['clipboard-read', 'clipboard-write'])
    context.add_init_script('''
      window.__pdfTerminated = 0; window.__delayPdf = false;
      window.__fastOfficeTimeout = false;
      const originalTimeout = window.setTimeout;
      window.setTimeout = (fn, ms, ...args) => originalTimeout(fn, window.__fastOfficeTimeout && [90000,180000].includes(ms) ? 500 : ms, ...args);
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
    errors, external, downloads, uploads = [], [], [], []
    allowed_origins = {urlparse(base).netloc, urlparse(base).netloc.replace("127.0.0.1", "localhost").replace("localhost", "127.0.0.1") if "localhost" in base else urlparse(base).netloc.replace("127.0.0.1", "localhost")}
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda request: external.append(request.url) if request.url.startswith(('http:', 'https:')) and urlparse(request.url).netloc not in allowed_origins else None)
    page.on('request', lambda request: uploads.append(request.url) if request.method not in ('GET', 'HEAD') else None)
    page.on('download', lambda download: downloads.append(download.suggested_filename))

    def viewport(width):
        page.set_viewport_size({'width': width, 'height': 1000})
        page.wait_for_function('(width) => innerWidth === width', arg=width)
        if page.locator('.office-preview-stage').count(): page.locator('.office-preview-stage').scroll_into_view_if_needed()
        page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')

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

    def office(app):
        page.locator('.office-preview-stage').scroll_into_view_if_needed()
        expect(page.locator('.office-preview[data-ready="true"]')).to_be_visible(timeout=90000)
        native = next(frame for frame in page.frames if urlparse(frame.url).path.removesuffix('index.html').endswith(f'/apps/{app}/main/'))
        assert 'mode=view' in native.url and 'lang=zh' in native.url
        assert native.evaluate('!!window.Asc.editor')
        assert native.locator('canvas').count() > 0
        native.wait_for_function('innerWidth === document.getElementById("viewport").getBoundingClientRect().width')
        native.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
        # Storage adapters are memory-only; there are no service workers in the viewer origin.
        assert native.evaluate('localStorage.setItem.toString().includes("values.set")')
        assert native.evaluate('navigator.serviceWorker.getRegistrations().then(r => r.length)') == 0
        return native

    open_tool('markdown'); start()
    markdown = download('md', 'converted').read_text()
    assert '# 季度销售报告' in markdown and '| 华东 | 1,200 |' in markdown
    assert '1. 编号列表第一项' in markdown and '<!-- PAGE_BREAK -->' in markdown
    page.get_by_role('button', name='复制 Markdown', exact=True).click()
    expect(page.get_by_role('button', name='已复制', exact=True)).to_be_visible()
    assert page.evaluate('navigator.clipboard.readText()') == markdown
    expect(page.locator('.pdfconv-reading')).to_contain_text('季度销售报告')
    expect(page.locator('.pdfconv-reading table')).to_have_count(2)
    page.get_by_label('Markdown 显示方式').select_option('source')
    assert page.locator('.pdfconv-preview').bounding_box()['height'] >= 320
    expect(page.locator('.pdfconv-preview')).to_have_value(markdown)
    page.get_by_label('Markdown 显示方式').select_option('reading')
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
    native = office('documenteditor')
    assert native.evaluate('Asc.editor.getCountPages()') == 2
    native.evaluate('Asc.editor.goToPage(1)')
    page.wait_for_timeout(150)
    assert native.evaluate('Asc.editor.getCurrentPage()') == 1
    native.evaluate('Asc.editor.goToPage(0)')
    page.locator('.office-preview').scroll_into_view_if_needed()
    page.screenshot(path=str(out / 'preview-word-desktop.png'), full_page=True)
    page.get_by_role('button', name='全屏预览', exact=True).click()
    page.wait_for_function('document.fullscreenElement?.classList.contains("office-preview")')
    assert native.evaluate('Asc.editor.getCountPages()') == 2
    page.get_by_role('button', name='退出全屏', exact=True).click()
    page.wait_for_function('!document.fullscreenElement')
    expect(page.get_by_role('button', name='全屏预览', exact=True)).to_be_focused()

    open_tool('excel'); start()
    excel = archive(download('xlsx', 'tables'))
    assert len([name for name in excel.namelist() if re.fullmatch(r'xl/worksheets/sheet\d+\.xml', name)]) == 2
    assert '华东' in ''.join(excel.read(name).decode() for name in excel.namelist() if name.endswith('.xml'))
    native = office('spreadsheeteditor')
    assert native.evaluate('Asc.editor.asc_getWorksheetsCount()') == 2
    assert native.evaluate('Asc.editor.asc_getCellInfo().asc_getText()') == '区域'
    font = native.evaluate('Asc.editor.wb.model.getWorksheet(0).getCell3(0,0).getFont().fn')
    assert font == 'Microsoft YaHei', font
    native.evaluate('Asc.editor.asc_showWorksheet(1)')
    assert native.evaluate('Asc.editor.asc_getActiveWorksheetIndex()') == 1
    assert native.evaluate('Asc.editor.asc_getWorksheetName(1)') == '第2页'
    page.get_by_label('识别普通数字（编号保持为文字）').check()
    page.get_by_label('工作表布局').select_option('single')
    page.get_by_role('button', name='开始转换', exact=True).click()
    numeric = archive(download('xlsx', 'combined-numeric'))
    assert '<v>1200</v>' in numeric.read('xl/worksheets/sheet1.xml').decode()
    native = office('spreadsheeteditor')
    assert native.evaluate('Asc.editor.asc_getWorksheetsCount()') == 1
    assert native.evaluate('Asc.editor.wb.model.getWorksheet(0).getCell3(2,1).getValue()') == '1200'
    page.locator('.office-preview').scroll_into_view_if_needed()
    native.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
    page.screenshot(path=str(out / 'preview-excel-desktop.png'), full_page=True)

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
    native = office('presentationeditor')
    assert native.evaluate('Asc.editor.getCountPages()') == 2
    native.evaluate('Asc.editor.goToPage(1)')
    assert native.evaluate('Asc.editor.getCurrentPage()') == 1
    page.get_by_label('转换模式').select_option('text')
    page.get_by_role('button', name='开始转换', exact=True).click()
    text_ppt = archive(download('pptx', 'editable-text'))
    assert '季度销售报告' in text_ppt.read('ppt/slides/slide1.xml').decode()
    assert '<p:pic>' not in text_ppt.read('ppt/slides/slide1.xml').decode()
    native = office('presentationeditor')
    assert native.evaluate('Asc.editor.getCountPages()') == 2
    native.evaluate('Asc.editor.goToPage(1)')
    assert native.evaluate('Asc.editor.getCurrentPage()') == 1
    native.evaluate('Asc.editor.goToPage(0)')
    page.screenshot(path=str(out / 'preview-powerpoint-text-desktop.png'), full_page=True)

    # Scan-only documents must fail clearly in text mode and work in image mode.
    open_tool('markdown'); start(scan)
    expect(page.get_by_role('alert')).to_contain_text('没有可提取的文字层', timeout=60000)
    open_tool('word')
    page.get_by_label('转换模式').select_option('image'); start(scan)
    scan_word = archive(download('docx', 'scanned-image'))
    assert any(name.startswith('word/media/') for name in scan_word.namelist())
    assert office('documenteditor').evaluate('Asc.editor.getCountPages()') == 1
    open_tool('powerpoint'); start(scan)
    scan_ppt = archive(download('pptx', 'scanned-image'))
    assert '<p:pic>' in scan_ppt.read('ppt/slides/slide1.xml').decode()
    assert office('presentationeditor').evaluate('Asc.editor.getCountPages()') == 1

    open_tool('markdown'); start(encrypted)
    expect(page.get_by_role('alert')).to_contain_text('打开密码', timeout=60000)
    page.get_by_label(re.compile(r'^(文件)?打开密码（仅加密文件需要）$')).fill('wrong')
    page.get_by_role('button', name='开始转换', exact=True).click()
    expect(page.get_by_role('alert')).to_contain_text('打开密码', timeout=60000)
    page.get_by_label(re.compile(r'^(文件)?打开密码（仅加密文件需要）$')).fill('secret')
    page.get_by_role('button', name='开始转换', exact=True).click()
    assert '季度销售报告' in download('md', 'decrypted').read_text()
    page.get_by_role('button', name='取消并清空', exact=True).click()
    expect(page.get_by_label(re.compile(r'^(文件)?打开密码（仅加密文件需要）$'))).to_have_value('')
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

    # Treat file text as data in every preview; Markdown cannot create active
    # HTML, links or remote image requests, while source/download stays intact.
    open_tool('markdown')
    malicious = text_pdf(['<script>window.__previewAttack=1</script>',
      '<img src="https://example.invalid/pdf-preview.png">',
      '<iframe src="https://example.invalid/frame"></iframe>',
      '![image](https://example.invalid/image.png)',
      '[link](https://example.invalid/open)'])
    page.get_by_label('选择 PDF', exact=True).set_input_files({'name':'markup.pdf','mimeType':'application/pdf','buffer':malicious})
    page.get_by_role('button', name='开始转换', exact=True).click()
    literal = download('md', 'literal-markup').read_text()
    assert 'window.__previewAttack' in literal and 'example.invalid' in literal
    expect(page.locator('.pdfconv-reading')).to_be_visible()
    expect(page.locator('.pdfconv-reading script, .pdfconv-reading iframe, .pdfconv-reading img, .pdfconv-reading a')).to_have_count(0)
    assert page.evaluate('window.__previewAttack === undefined')
    page.get_by_label('Markdown 显示方式').select_option('source')
    expect(page.locator('.pdfconv-preview')).to_have_value(literal)

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
        expect(page.locator('.pdfconv-visual-preview')).to_have_count(0)

    # Interrupt the actual Office WASM load. No frame or delayed result may survive
    # input changes, clearing or a route departure, including before SDK ready.
    for action in ['clear', 'option', 'leave', 'timeout']:
        open_tool('word')
        pending = []
        def hold_engine(route): pending.append(route)
        page.route('**/office-viewer/**/x2t.wasm.br', hold_engine)
        if action == 'timeout': page.evaluate('window.__fastOfficeTimeout = true')
        with page.expect_request('**/office-viewer/**/x2t.wasm.br'):
            start()
        expect(page.locator('.office-preview iframe')).to_have_count(1)
        if action == 'clear': page.get_by_role('button', name='取消并清空', exact=True).click()
        elif action == 'option': page.get_by_label('转换模式').select_option('image')
        elif action == 'leave': page.get_by_role('link', name='全部工具', exact=True).click()
        else:
            expect(page.get_by_role('button', name='重新加载预览')).to_be_visible(timeout=5000)
            expect(page.get_by_role('button', name='下载 .docx')).to_be_visible()
            page.evaluate('window.__fastOfficeTimeout = false')
        expect(page.locator('.office-preview iframe')).to_have_count(0)
        for route in pending: route.abort()
        page.unroute('**/office-viewer/**/x2t.wasm.br', hold_engine)
        if action == 'timeout':
            page.get_by_role('button', name='重新加载预览').click()
            assert office('documenteditor').evaluate('Asc.editor.getCountPages()') == 2
        else: expect(page.locator('.office-preview')).to_have_count(0)

    for tool in ['word', 'excel', 'powerpoint', 'markdown']:
        open_tool(tool)
        start()
        expect(page.locator('.pdfconv-visual-preview')).to_be_visible(timeout=60000)
        if tool != 'markdown': office({'word':'documenteditor', 'excel':'spreadsheeteditor', 'powerpoint':'presentationeditor'}[tool])
        for theme in ['dark', 'light']:
            set_theme_mode(page, theme)
            if tool != 'markdown':
                native = next(f for f in page.frames if urlparse(f.url).path.removesuffix('index.html').endswith('/main/'))
                native.wait_for_function('(id) => window.uitheme.id === id', arg='theme-night' if theme == 'dark' else 'theme-white')
                assert not native.evaluate('window.uitheme.iscontentdark')
            for palette in ['fufu-blue', 'hutao-red']:
                page.evaluate('''([theme, palette]) => {
                  document.documentElement.dataset.theme = theme;
                  document.documentElement.dataset.palette = palette;
                }''', [theme, palette])
                for width in [320, 390, 768, 1024, 1440]:
                    viewport(width)
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (tool, theme, palette, width)
                    if tool != 'markdown':
                        size = round(page.locator('.office-preview-frame').bounding_box()['width'])
                        native.wait_for_function('(size) => Math.abs(innerWidth - size) <= 1', arg=size)
                viewport(390)
                if tool != 'markdown': native.wait_for_function('(size) => Math.abs(innerWidth - size) <= 1', arg=round(page.locator('.office-preview-frame').bounding_box()['width']))
                page.screenshot(path=str(out / f'{tool}-{palette}-{theme}.png'), full_page=True)
    assert not uploads, uploads
    assert not external, external
    assert not errors, errors
    (out / 'office-verification.json').write_text(json.dumps({'viewer':'office-wasm-viewer 0.2.0', 'engine':'ONLYOFFICE 9.3.2', 'checks':['real DOCX/XLSX/PPTX canvases', 'Chinese font', 'page and sheet switching', 'fullscreen and focus', 'timeout and retry', 'cancel before ready', 'no uploads', 'memory preferences', 'four site themes', 'five widths']}, ensure_ascii=False, indent=2))
    context.close(); browser.close()
print('PDF conversion browser checks passed: DOCX/XLSX/PPTX/Markdown downloads, image and text modes, scans, passwords, page ranges, cancellation, native Office canvases, full screen, four themes and five widths.')
