"""Verify native Office editing and downloaded files, not just editor availability."""
import io
import json
import os
import re
import subprocess
import zipfile
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:4173').rstrip('/')
out = Path('artifacts/office-editor'); out.mkdir(parents=True, exist_ok=True)
subprocess.run(['node', 'scripts/check-office-editor.mjs'], check=True)
picture = out / 'insert.png'
Image.new('RGB', (120, 80), '#c45834').save(picture)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce', permissions=['clipboard-read', 'clipboard-write'])
    page = context.new_page()
    errors, uploads, external = [], [], []
    allowed = {urlparse(base).netloc, urlparse(base).netloc.replace('127.0.0.1', 'localhost')}
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('request', lambda r: uploads.append(r.url) if r.method not in ['GET', 'HEAD'] else None)
    page.on('request', lambda r: external.append(r.url) if r.url.startswith(('http:', 'https:')) and urlparse(r.url).netloc not in allowed else None)

    def open_tool():
        page.goto(base + '/tools/office-editor')
        expect(page.get_by_role('heading', name='在线 Office 编辑', exact=True)).to_be_visible()

    def native_editor(app):
        expect(page.locator('.office-preview-stage')).to_be_visible(timeout=30000)
        page.locator('.office-preview-stage').scroll_into_view_if_needed()
        expect(page.locator('.office-preview[data-ready="true"]')).to_be_visible(timeout=90000)
        frame = next(f for f in page.frames if f'/{app}/main/index.html' in f.url)
        assert 'mode=view' not in frame.url
        assert frame.evaluate('Asc.editor.isViewMode') is False
        expect(frame.locator('[data-layout-name="toolbar-collaboration"]')).to_be_hidden()
        assert frame.evaluate('(window.DE || window.SSE || window.PE).getController("Main").appOptions.canChangeCoAuthoring') is False
        assert frame.evaluate('localStorage.setItem.toString().includes("values.set")')
        assert frame.evaluate('navigator.serviceWorker.getRegistrations().then(r=>r.length)') == 0
        page.wait_for_timeout(150)
        return frame

    def create(kind, app):
        page.get_by_role('button', name='新建 ' + kind, exact=True).click()
        return native_editor(app)

    def save(name):
        with page.expect_download(timeout=120000) as pending:
            page.get_by_role('button', name='下载编辑后的文件', exact=True).click()
        file = out / name
        pending.value.save_as(file)
        with zipfile.ZipFile(file) as archive:
            assert archive.testzip() is None
        return file

    def protect_refresh_and_close():
        seen = []
        def stay(dialog):
            seen.append(dialog.type)
            dialog.dismiss()
        page.once('dialog', stay)
        reload_session = context.new_cdp_session(page)
        with page.expect_event('dialog'):
            reload_session.send('Page.reload')
        reload_session.detach()
        assert seen == ['beforeunload'], seen
        assert not page.is_closed()
        expect(page.locator('.office-preview iframe')).to_have_count(1)
        page.once('dialog', stay)
        page.close(run_before_unload=True)
        page.wait_for_timeout(100)
        assert seen == ['beforeunload', 'beforeunload'], seen
        assert not page.is_closed()
        expect(page.locator('.office-preview iframe')).to_have_count(1)

    def click_document(frame, x, y):
        point = frame.evaluate('([x,y])=>Asc.editor.WordControl.m_oDrawingDocument.ConvertCoordsToCursorWR(x,y,0)', [x,y])
        assert not point.get('Error')
        if 'presentationeditor' in frame.url:
            offset = frame.evaluate('document.getElementById("id_viewer_overlay").getBoundingClientRect().toJSON()')
            frame.locator('body').dblclick(position={'x': point['X'] + offset['left'], 'y': point['Y'] + offset['top']})
        else:
            frame.locator('body').click(position={'x': point['X'], 'y': point['Y']})

    open_tool()
    expect(page.locator('.office-preview iframe')).to_have_count(0)
    frame = create('Word', 'documenteditor')
    protect_refresh_and_close()
    click_document(frame, 35, 30)
    page.keyboard.insert_text('在线 Word 中文编辑验证')
    frame.locator('body').press('Control+a')
    frame.locator('body').press('Control+b')
    page.get_by_label('下载文件名', exact=True).fill('中文报告.docx')
    word = save('edited.docx')
    with zipfile.ZipFile(word) as z:
        xml = z.read('word/document.xml').decode()
        assert '在线 Word 中文编辑验证' in xml and '<w:b' in xml
    assert frame.evaluate('Asc.editor.isDocumentModified()') is False
    protect_refresh_and_close()
    page.get_by_label('打开 Office 文件', exact=True).set_input_files(word)
    frame = native_editor('documenteditor')
    assert frame.evaluate('Asc.editor.getCountPages()') == 1
    with page.expect_file_chooser() as chooser:
        frame.evaluate('Asc.editor.asc_addImage()')
    chooser.value.set_files(picture)
    page.wait_for_timeout(200)
    image_word = save('with-image.docx')
    with zipfile.ZipFile(image_word) as z:
        images = [z.read(n) for n in z.namelist() if n.startswith('word/media/')]
        decoded = [Image.open(io.BytesIO(data)).convert('RGB') for data in images]
        assert any(image.size == (120,80) and image.getpixel((10,10)) == (196,88,52) for image in decoded), 'Inserted image must survive the actual DOCX export'
    page.get_by_label('打开 Office 文件', exact=True).set_input_files(image_word)
    frame = native_editor('documenteditor')
    assert frame.evaluate('Object.keys(Asc.editor.ImageLoader.map_image_index).length') > 0
    click_document(frame, 40, 30)
    frame.locator('body').press('Control+End')
    page.keyboard.insert_text('退出提示验证')
    frame.wait_for_function('Asc.editor.isDocumentModified() === true')
    page.get_by_role('button', name='关闭文档', exact=True).click()
    expect(page.locator('.office-discard-dialog')).to_be_visible()
    page.get_by_role('button', name='返回编辑', exact=True).click()
    assert not frame.is_detached()
    protect_refresh_and_close()
    page.get_by_role('link', name='全部工具', exact=True).click()
    expect(page.locator('.office-discard-dialog')).to_be_visible()
    page.get_by_role('button', name='返回编辑', exact=True).click()
    assert page.url.endswith('/tools/office-editor')
    click_document(frame, 40, 30)
    with page.expect_download() as pending:
        page.keyboard.press('Control+s')
    pending.value.save_as(out / 'shortcut.docx')
    page.get_by_role('button', name='全屏编辑', exact=True).click()
    page.wait_for_function('document.fullscreenElement?.classList.contains("office-preview")')
    assert not frame.is_detached()
    page.get_by_role('button', name='退出全屏', exact=True).click()
    expect(page.get_by_role('button', name='全屏编辑', exact=True)).to_be_focused()
    page.screenshot(path=str(out / 'word-desktop.png'), full_page=True)

    frame = create('Excel', 'spreadsheeteditor')
    frame.locator('#ce-cell-content').fill('42')
    first_sheet = save('numeric.xlsx')
    frame.locator('#ce-cell-name').fill('B1')
    frame.locator('#ce-cell-name').press('Enter')
    frame.locator('#ce-cell-content').fill('=A1*2')
    workbook = save('formula.xlsx')
    check = subprocess.check_output(['node', '-e', "const X=require('xlsx'),fs=require('fs');const w=X.read(fs.readFileSync(process.argv[1]));console.log(JSON.stringify(w.Sheets[w.SheetNames[0]]))", str(workbook)], text=True)
    sheet = json.loads(check)
    assert sheet['A1']['v'] == 42 and sheet['B1']['f'] == 'A1*2' and sheet['B1']['v'] == 84, sheet
    page.get_by_label('打开 Office 文件', exact=True).set_input_files(workbook)
    frame = native_editor('spreadsheeteditor')
    assert frame.evaluate('Asc.editor.wbModel.getWorksheet(0).getCell3(0,1).getFormula()') == 'A1*2'
    page.screenshot(path=str(out / 'excel-desktop.png'), full_page=True)

    frame = create('PowerPoint', 'presentationeditor')
    click_document(frame, 120, 45)
    page.keyboard.insert_text('PowerPoint 中文编辑验证')
    deck = save('edited.pptx')
    with zipfile.ZipFile(deck) as z:
        assert 'PowerPoint 中文编辑验证' in z.read('ppt/slides/slide1.xml').decode()
    page.get_by_label('打开 Office 文件', exact=True).set_input_files(deck)
    frame = native_editor('presentationeditor')
    assert frame.evaluate('Asc.editor.getCountPages()') == 1
    click_document(frame, 120, 45)
    page.keyboard.insert_text('放弃修改验证')
    assert frame.evaluate('Asc.editor.isDocumentModified()') is True
    page.get_by_role('button', name='关闭文档', exact=True).click()
    expect(page.locator('.office-discard-dialog')).to_be_visible()
    page.get_by_role('button', name='放弃修改', exact=True).click()
    expect(page.locator('.office-preview iframe')).to_have_count(0)

    # Native rendering and responsive containers remain correct in all themes.
    for kind, app in [('Word','documenteditor'), ('Excel','spreadsheeteditor'), ('PowerPoint','presentationeditor')]:
        frame = create(kind, app)
        for theme in ['dark', 'light']:
            while page.locator('.theme-toggle').get_attribute('data-mode') != theme:
                page.locator('.theme-toggle').click()
            frame.wait_for_function('(theme)=>window.uitheme.id===theme', arg='theme-night' if theme=='dark' else 'theme-white')
            for palette in ['fufu-blue','hutao-red']:
                page.evaluate('(palette)=>document.documentElement.dataset.palette=palette', palette)
                for width in [320,390,768,1024,1440]:
                    page.set_viewport_size({'width':width,'height':1000})
                    page.wait_for_function('(width)=>innerWidth===width', arg=width)
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (kind,theme,palette,width)
                page.set_viewport_size({'width':390,'height':1000})
                page.locator('.office-preview-stage').scroll_into_view_if_needed()
                page.screenshot(path=str(out / f'{kind}-{theme}-{palette}.png'), full_page=True)
        page.get_by_role('button', name='关闭文档', exact=True).click()
    # Cancel before the real engine finishes initialising.
    pending = []
    page.route('**/office-viewer/**/x2t.wasm.br', lambda route: pending.append(route))
    with page.expect_request('**/office-viewer/**/x2t.wasm.br'):
        page.get_by_role('button', name='新建 Word', exact=True).click()
    page.get_by_role('button', name='关闭文档', exact=True).click()
    expect(page.locator('.office-preview iframe')).to_have_count(0)
    for route in pending: route.abort()
    page.unroute('**/office-viewer/**/x2t.wasm.br')
    # Explicitly closing the document releases the browser unload protection.
    page.reload()
    expect(page.locator('.office-preview iframe')).to_have_count(0)
    # Read-only previews must keep their permissions after enabling the editor.
    page.goto(base + '/tools/pdf-to-word')
    page.get_by_label('选择 PDF', exact=True).set_input_files('scripts/fixtures/pdf-convert.pdf')
    page.get_by_role('button', name='开始转换', exact=True).click()
    page.locator('.office-preview-stage').scroll_into_view_if_needed()
    expect(page.locator('.office-preview[data-ready="true"]')).to_be_visible(timeout=90000)
    preview = next(f for f in page.frames if '/documenteditor/main/' in f.url)
    assert preview.evaluate('Asc.editor.isViewMode') is True
    assert not errors, errors
    assert not uploads, uploads
    assert not external, external
    (out / 'verification.json').write_text(json.dumps({'checks':['Word formatting and image export','Excel pending edit, formula and recalculation','PowerPoint real text export','reopen all formats','native beforeunload for pristine, edited and downloaded documents', 'discard/cancel and route guard','Ctrl+S and full screen','two palettes and five widths','read-only preview','no uploads or persistent document storage']}, ensure_ascii=False, indent=2))
    context.close(); browser.close()
print('Office browser checks passed: real editing, images, formulas, exports, reopening, cleanup, themes, widths and read-only preview.')
