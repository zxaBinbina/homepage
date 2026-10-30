"""Exercise imported Web Tools with real files, downloads, cancellation and theme/motion checks."""
import io
import json
import os
import re
import zipfile
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:5173').rstrip('/')
out = Path('artifacts/jaytools'); out.mkdir(parents=True, exist_ok=True)
manifest = json.loads(Path('third_party/jaywcjlove-tools/upstream.json').read_text())
added = [item['id'] for item in manifest['tools'] if item['status'] == 'added']

def pdf_fixture():
    # Two distinct pages, built without an external PDF generator.
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>', b'<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>']
    for content in [5, 6]:
        objects.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 240 180] /Resources << >> /Contents {content} 0 R >>'.encode())
    for content in [b'0.2 0.6 0.9 rg 20 20 160 120 re f', b'0.8 0.2 0.2 rg 40 40 120 80 re f']:
        objects.append(b'<< /Length ' + str(len(content)).encode() + b' >>\nstream\n' + content + b'\nendstream')
    data = b'%PDF-1.4\n'; offsets = []
    for index, obj in enumerate(objects, 1):
        offsets.append(len(data)); data += f'{index} 0 obj\n'.encode() + obj + b'\nendobj\n'
    start = len(data)
    data += b'xref\n0 7\n0000000000 65535 f \n'
    data += b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets)
    return data + f'trailer\n<< /Size 7 /Root 1 0 R >>\nstartxref\n{start}\n%%EOF'.encode()

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    context = browser.new_context(viewport={'width':1440,'height':1000}, reduced_motion='reduce', permissions=['clipboard-read','clipboard-write'])
    page = context.new_page()
    errors, remote = [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('request', lambda request: remote.append(request.url) if request.url.startswith(('http:', 'https:')) and not request.url.startswith(base) else None)
    def open_tool(id):
        page.goto(base + '/tools/' + id)
        expect(page.locator('.tool-page')).to_be_visible()
    def download(button):
        with page.expect_download() as event: button.click()
        target = out / event.value.suggested_filename
        event.value.save_as(target)
        return target
    def no_overflow():
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), page.url

    open_tool('json-xml')
    page.get_by_role('button', name='示例', exact=True).click()
    expect(page.locator('textarea[readonly]')).to_have_value(re.compile('name="悠哉世界"'))
    page.get_by_role('radio', name='XML → JSON').click()
    expect(page.locator('textarea[readonly]')).to_have_value('')
    page.get_by_role('button', name='示例', exact=True).click()
    expect(page.locator('textarea[readonly]')).to_have_value(re.compile('"@_name"'))
    page.locator('textarea:not([readonly])').fill('<root><broken></root>')
    expect(page.locator('[role="alert"]')).to_be_visible()

    open_tool('svg-optimizer')
    page.get_by_role('button', name='示例', exact=True).click()
    expect(page.locator('textarea[readonly]')).to_have_value(re.compile('viewBox'), timeout=15000)
    svg = download(page.get_by_role('button', name='下载', exact=True))
    assert '<svg' in svg.read_text() and '<!--' not in svg.read_text()

    open_tool('js-obfuscator')
    page.get_by_role('button', name='示例', exact=True).click()
    page.get_by_role('button', name='开始混淆', exact=True).click()
    expect(page.locator('textarea[readonly]').first).not_to_have_value('', timeout=20000)
    assert download(page.get_by_role('button', name='下载', exact=True)).stat().st_size > 40
    page.locator('textarea:not([readonly])').fill('function invalid (')
    expect(page.locator('textarea[readonly]').first).to_have_value('')
    page.get_by_role('button', name='开始混淆', exact=True).click()
    expect(page.locator('[role="alert"]')).to_be_visible(timeout=20000)
    page.get_by_role('button', name='示例', exact=True).click()
    page.get_by_role('button', name='开始混淆', exact=True).click()
    page.get_by_role('button', name='取消', exact=True).click()
    expect(page.locator('textarea[readonly]').first).to_have_value('')

    open_tool('standard-chinese-characters')
    expect(page.locator('.jay-characters button')).to_have_count(120)
    page.get_by_label('查找汉字或拼音').fill('中')
    expect(page.locator('.jay-characters button')).to_have_count(1)
    page.locator('.jay-characters button').click()
    assert page.evaluate('navigator.clipboard.readText()') == '中'
    page.get_by_label('查找汉字或拼音').fill('')
    page.get_by_label('字表级别').select_option('3')
    expect(page.locator('.jay-characters small').first).to_have_text('6501')

    open_tool('chinese-pinyin-conversion')
    page.get_by_role('button', name='示例', exact=True).click()
    expect(page.locator('.jay-ruby ruby').first).to_have_text('天tiān')
    page.get_by_role('radio', name='首字母').click()
    expect(page.locator('.jay-ruby ruby').first).to_have_text('天t')

    open_tool('generate-github-badges')
    page.get_by_label('项目来源').select_option('docker')
    page.get_by_label('镜像名').fill('team/image')
    expect(page.locator('textarea[readonly]')).to_have_value(re.compile('/team/image'))
    page.get_by_role('radio', name='自定义徽章').click()
    page.get_by_label('左侧文字').fill('中文-a')
    expect(page.locator('textarea[readonly]')).to_have_value(re.compile('%E4%B8%AD'))

    open_tool('exif-viewer')
    exif = Image.Exif(); exif[271] = 'Toolbox Camera'; exif[272] = 'Local Test'
    img = Image.new('RGB', (120,80), (60,140,200)); buffer = io.BytesIO(); img.save(buffer, format='JPEG', exif=exif)
    page.get_by_label('选择图片').set_input_files({'name':'metadata.jpg','mimeType':'image/jpeg','buffer':buffer.getvalue()})
    expect(page.locator('.jay-metadata')).to_contain_text('Toolbox Camera')
    assert 'Toolbox Camera' in download(page.get_by_role('button', name='下载', exact=True)).read_text()
    page.get_by_label('选择图片').set_input_files({'name':'broken.jpg','mimeType':'image/jpeg','buffer':b'not an image'})
    expect(page.locator('[role="alert"]')).to_be_visible()
    expect(page.locator('.jay-metadata')).to_have_count(0)

    open_tool('code-to-image')
    page.get_by_role('button', name='示例', exact=True).click()
    expect(page.locator('.jay-code-body code')).to_contain_text('你好')
    for type in ['png','jpeg','svg']:
        page.get_by_label('导出格式').select_option(type)
        path = download(page.get_by_role('button',name='下载图片',exact=True))
        if type == 'svg': assert '<svg' in path.read_text()
        else:
            image = Image.open(path)
            assert image.width == 1440 and image.height > 100
            assert len(image.convert('RGB').getcolors(image.width*image.height)) > 30, 'Export is blank'
    page.locator('textarea').fill('<img src="https://privacy.invalid/" onerror="window.injected=true">')
    assert not page.evaluate('window.injected || false')

    open_tool('pdf-to-img')
    page.get_by_label('选择 PDF').set_input_files({'name':'two-pages.pdf','mimeType':'application/pdf','buffer':pdf_fixture()})
    expect(page.locator('.jay-pdf-preview img')).to_be_visible(timeout=20000)
    first = download(page.get_by_role('button',name='下载当前页',exact=True))
    assert Image.open(first).size == (360,270)
    page.get_by_role('button',name='下一页',exact=True).click()
    expect(page.locator('.jay-pdf-preview figcaption')).to_contain_text('第 2 页')
    second = download(page.get_by_role('button',name='下载当前页',exact=True))
    assert first.read_bytes() != second.read_bytes()
    archive = download(page.get_by_role('button',name='打包全部页面',exact=True))
    with zipfile.ZipFile(archive) as zipped:
        assert sorted(zipped.namelist()) == ['two-pages-1.png','two-pages-2.png']
        assert zipped.read('two-pages-2.png') == second.read_bytes(), 'Last PDF page was omitted or wrong'
    page.get_by_label('图片格式').select_option('jpeg')
    expect(page.get_by_role('button',name='下载当前页',exact=True)).to_be_enabled()
    assert Image.open(download(page.get_by_role('button',name='下载当前页',exact=True))).format == 'JPEG'
    page.get_by_role('button',name='打包全部页面',exact=True).click()
    page.get_by_role('button',name='取消打包',exact=True).click()
    expect(page.get_by_role('button',name='打包全部页面',exact=True)).to_be_enabled()
    page.get_by_label('选择 PDF').set_input_files({'name':'bad.pdf','mimeType':'application/pdf','buffer':b'bad'})
    expect(page.locator('[role="alert"]')).to_be_visible()
    expect(page.locator('.jay-pdf-preview')).to_have_count(0)

    open_tool('css-easing-animation')
    page.get_by_label('缓动预设').select_option('easeOutBack')
    expect(page.locator('textarea[readonly]')).to_have_value(re.compile('0.34, 1.56, 0.64, 1'))
    handle = page.get_by_role('button',name='控制点 1，方向键微调')
    handle.focus(); page.keyboard.press('ArrowRight')
    expect(page.get_by_label('x1',exact=True)).to_have_value('0.35')
    handle.evaluate("el => el.scrollIntoView({block:'center'})")
    box = handle.bounding_box()
    page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2); page.mouse.down(); page.mouse.move(box['x']+50,box['y']+50); page.mouse.up()
    assert page.get_by_label('x1',exact=True).input_value() != '0.35'
    page.get_by_role('button',name='播放预览',exact=True).click()
    assert page.locator('.jay-easing-block').evaluate('el => getComputedStyle(el).transitionDuration') in ['0s','1e-05s','0.00001s']

    for id in added:
        open_tool(id)
        sample = page.get_by_role('button',name='示例',exact=True)
        if sample.count():
            sample.first.click()
            if id == 'js-obfuscator': page.get_by_role('button',name='开始混淆',exact=True).click()
            if page.locator('textarea[readonly]').count(): expect(page.locator('textarea[readonly]').first).not_to_have_value('',timeout=20000)
        if id == 'exif-viewer':
            page.get_by_label('选择图片').set_input_files({'name':'metadata.jpg','mimeType':'image/jpeg','buffer':buffer.getvalue()})
            expect(page.locator('.jay-metadata')).to_be_visible()
        if id == 'pdf-to-img':
            page.get_by_label('选择 PDF').set_input_files({'name':'two-pages.pdf','mimeType':'application/pdf','buffer':pdf_fixture()})
            expect(page.locator('.jay-pdf-preview')).to_be_visible(timeout=20000)
        for palette in ['fufu-blue','hutao-red']:
            for theme in ['dark','light']:
                page.evaluate('([p,t]) => {document.documentElement.dataset.palette=p;document.documentElement.dataset.theme=t}',[palette,theme])
                assert page.locator('html').evaluate("el => getComputedStyle(el).getPropertyValue('--blue').trim()") == ({'dark':'#ed8871','light':'#a83d33'}[theme] if palette == 'hutao-red' else {'dark':'#4ea4ef','light':'#2468b1'}[theme])
                for width in [320,390,768,1024,1440]:
                    page.set_viewport_size({'width':width,'height':1000}); no_overflow()
                    if width in [390,1440] and id in ['code-to-image','css-easing-animation','pdf-to-img','chinese-pinyin-conversion']:
                        page.screenshot(path=str(out/f'{id}-{palette}-{theme}-{width}.png'),full_page=True)
        print('PASS themes/widths', id, flush=True)

    page.set_viewport_size({'width':1440,'height':1000})
    page.emulate_media(reduced_motion='no-preference')
    open_tool('generate-github-badges')
    page.get_by_role('radio',name='自定义徽章').click()
    leaving = page.locator('.jay-panel-leave-active')
    assert leaving.count() and leaving.evaluate_all('els => els.every(el => el.inert)')
    expect(page.get_by_label('左侧文字')).to_be_visible()
    page.get_by_role('link',name='全部工具',exact=True).click()
    expect(page.locator('.tool-card')).to_have_count(56)
    page.get_by_role('searchbox',name='搜索工具').fill('CSS 缓动')
    expect(page.locator('.tool-card:not(.tool-list-leave-active)')).to_have_count(1)
    page.locator('.tool-card:not(.tool-list-leave-active)').click()
    expect(page.locator('.tool-heading h1')).to_have_text('CSS 缓动曲线')
    assert page.locator('.tool-heading').evaluate('el => getComputedStyle(el).animationName') == 'tool-workbench-in'
    assert not errors, errors
    assert not remote, remote
    browser.close()
print('15 new tools: real files, PDF final page/ZIP/cancel, image exports, conversion, copy, workers, 5 widths, 4 themes, motion and local-only processing passed.')
