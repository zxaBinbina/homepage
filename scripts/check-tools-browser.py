"""Verify the complete imported toolbox on a dev or built preview server."""
import json
import os
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:5173').rstrip('/')
tools = json.loads(subprocess.check_output(['node', 'scripts/list-tools.mjs']))
out = Path('artifacts'); out.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce', timezone_id='Asia/Shanghai', permissions=['clipboard-read', 'clipboard-write'])
    page = context.new_page()
    errors, external = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    blocked = []
    page.on('requestfailed', lambda r: blocked.append(r.url) if r.failure and 'csp' in r.failure.lower() else None)
    page.on('request', lambda r: external.append(r.url) if r.url.startswith(('http:', 'https:')) and not r.url.startswith(base) else None)

    def open_tool(id):
        page.goto(base + '/tools/' + id)
        expect(page.locator('.tool-page')).to_be_visible()

    def no_overflow():
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), page.url

    def resize_editor(editor, delta):
        editor.scroll_into_view_if_needed()
        box = editor.bounding_box()
        x, y = box['x'] + box['width'] - 5, box['y'] + box['height'] - 5
        page.mouse.move(x, y)
        page.mouse.down()
        page.mouse.move(x, y + delta, steps=10)
        page.mouse.up()
        page.evaluate('new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
        assert editor.bounding_box()['height'] >= box['height'] + delta - 2

    def editor_fills_pane(pane):
        editor = pane.locator('textarea')
        editor.scroll_into_view_if_needed()
        assert pane.evaluate('''el => {
          const editor = el.querySelector('textarea')
          const field = editor.getBoundingClientRect()
          const area = el.querySelector('.pane__editor').getBoundingClientRect()
          return Math.abs(field.top - area.top) < 1 && Math.abs(field.bottom - area.bottom) < 1
            && document.elementFromPoint(field.left + 24, field.bottom - 16) === editor
        }'''), f'Unusable space in editor: {page.url}'

    # Alternating native resizes must grow the real textareas, including one already resized.
    page.set_viewport_size({'width': 1440, 'height': 1400})
    for tool_id in ['text-diff', 'json-formatter']:
        open_tool(tool_id)
        panes = page.locator('.pane')
        expect(panes).to_have_count(2)
        for index, delta in [(0, 140), (1, 100), (0, 70)]:
            resize_editor(panes.nth(index).locator('textarea'), delta)
            for pane in panes.all():
                editor_fills_pane(pane)
        if tool_id == 'text-diff':
            for pane in panes.all():
                editor = pane.locator('textarea')
                box = editor.bounding_box()
                page.mouse.click(box['x'] + 24, box['y'] + box['height'] - 16)
                page.keyboard.insert_text('在扩大后的区域输入')
                expect(editor).to_have_value('在扩大后的区域输入')
        panes.first.get_by_role('button', name='全屏编辑', exact=True).click()
        expect(page.locator('.pane--max')).to_be_visible()
        editor_fills_pane(page.locator('.pane--max'))
        page.keyboard.press('Escape')
        expect(page.locator('.pane--max')).to_have_count(0)
        for pane in panes.all():
            editor_fills_pane(pane)
    page.set_viewport_size({'width': 1440, 'height': 1000})

    page.goto(base + '/tool')
    expect(page.locator('.tool-card')).to_have_count(41)
    expect(page.locator('.desktop-nav [aria-current="page"]')).to_have_text('工具')
    page.get_by_role('button', name='格式整理', exact=True).click()
    expect(page.locator('.tool-card')).to_have_count(7)
    page.get_by_role('button', name='全部', exact=True).click()
    page.get_by_role('searchbox', name='搜索工具').fill('二维码')
    expect(page.locator('.tool-card')).to_have_count(1)
    page.get_by_role('searchbox', name='搜索工具').fill('no-such-tool')
    expect(page.locator('.directory-empty')).to_be_visible()
    page.get_by_role('button', name='查看全部工具').click()
    expect(page.locator('.tool-card')).to_have_count(41)

    # Every source tool renders, responds to its sample, has metadata and fits all required widths.
    for tool in (tools if not os.environ.get('HOMEPAGE_TOOLS_FOCUS') else []):
        open_tool(tool['id'])
        expect(page).to_have_title(tool['name'] + ' · 网页工具 · a彬彬a')
        expect(page.locator('main h1')).to_have_text(tool['name'])
        sample = page.get_by_role('button', name='示例', exact=True)
        if sample.count():
            sample.first.click()
            page.wait_for_timeout(250)
            outputs = page.locator('textarea[readonly]')
            if outputs.count():
                expect(outputs.first).not_to_have_value('')
        assert not page.locator('[role="alert"]').count(), (tool['id'], page.locator('[role="alert"]').all_text_contents())
        for width in [320, 390, 768, 1024, 1440]:
            page.set_viewport_size({'width': width, 'height': 1000})
            no_overflow()
        # Raw HTML is useful to crawlers without client JavaScript.
        html = context.request.get(base + tool['path']).text()
        assert tool['name'] + ' · 网页工具 · a彬彬a' in html
        assert f'href="https://zxabinbina.cc.cd{tool["path"]}"' in html
        print('PASS', tool['id'], flush=True)

    open_tool('json-formatter')
    source = page.locator('.pane textarea:not([readonly])')
    result = page.locator('.pane textarea[readonly]')
    source.fill('{"name":"中文🌍","ok":true}')
    expect(result).to_have_value('{\n  "name": "中文🌍",\n  "ok": true\n}')
    page.get_by_role('button', name='复制', exact=True).click()
    assert page.evaluate('navigator.clipboard.readText()') == result.input_value()
    with page.expect_download() as download:
        page.get_by_role('button', name='下载', exact=True).click()
    assert Path(download.value.path()).read_text() == result.input_value()
    source.fill('{bad}')
    expect(result).to_have_value('')
    expect(page.get_by_role('alert')).to_contain_text('处理失败')
    expect(page.get_by_role('button', name='复制', exact=True)).to_be_disabled()
    source.fill('{"secret":"not-stored"}')
    expect(result).not_to_have_value('')
    page.reload(); expect(page.locator('.tool-page')).to_be_visible()
    expect(source).to_have_value('')
    assert page.evaluate('Object.keys(localStorage).concat(Object.keys(sessionStorage)).every(k => !k.startsWith("freemium:"))')

    # Real editor state survives expansion; Escape restores focus and background interactivity.
    source.fill('{"modal":true}')
    page.get_by_role('button', name='全屏编辑', exact=True).first.click()
    expect(page.locator('.pane--max')).to_be_visible()
    assert page.locator('#app').evaluate('el => el.inert')
    expect(page.locator('.pane--max textarea')).to_have_value('{"modal":true}')
    page.keyboard.press('Escape')
    expect(page.locator('.pane--max')).to_have_count(0)
    assert not page.locator('#app').evaluate('el => el.inert')
    expect(page.get_by_role('button', name='全屏编辑', exact=True).first).to_be_focused()

    page.evaluate('Object.defineProperty(navigator, "clipboard", { configurable:true, value: { writeText: () => Promise.reject(new Error("blocked")) } })')
    page.get_by_role('button', name='复制', exact=True).click()
    expect(page.get_by_role('status')).to_contain_text('复制失败')
    expect(result).to_be_focused()
    assert result.evaluate('el => el.selectionEnd - el.selectionStart') == len(result.input_value())

    # Files, images, QR decoding, workbook sheets and non-text tools.
    open_tool('excel-to-json')
    page.locator('input[type="file"]').set_input_files('public/tools/freemium-sample.xlsx')
    expect(page.locator('textarea[readonly]')).not_to_have_value('')
    json.loads(page.locator('textarea[readonly]').input_value())
    open_tool('image-base64')
    page.locator('input[type="file"]').set_input_files('public/favicon.svg')
    expect(page.locator('textarea[readonly]')).to_have_value(__import__('re').compile(r'^data:image/svg\+xml;base64,'))
    open_tool('qr-code')
    page.locator('textarea').first.fill('https://example.com/中文')
    page.wait_for_timeout(200)
    with page.expect_download() as download:
        page.get_by_role('button', name='下载 PNG', exact=True).click()
    qr_file = download.value.path()
    page.get_by_role('radio', name='识别', exact=True).click()
    page.locator('input[type="file"]').set_input_files({'name':'qr-code.png', 'mimeType':'image/png', 'buffer':Path(qr_file).read_bytes()})
    expect(page.locator('textarea[readonly]')).to_have_value('https://example.com/中文')
    open_tool('hash-generator')
    page.locator('textarea').fill('abc')
    expect(page.locator('.results')).to_contain_text('ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
    page.locator('textarea').fill('')
    expect(page.locator('.results')).to_contain_text('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
    open_tool('jwt-debugger')
    page.get_by_role('button', name='示例', exact=True).click()
    page.get_by_placeholder('your-256-bit-secret (the sample’s secret)').fill('your-256-bit-secret')
    expect(page.locator('.tool-page')).to_contain_text('签名校验通过')
    open_tool('certificate-decoder')
    pem = __import__('re').search(r'-----BEGIN CERTIFICATE-----[\s\S]*?-----END CERTIFICATE-----', Path('src/tools/freemium/tools/data/cacert.pem').read_text()).group()
    page.get_by_role('textbox', name='证书（PEM）', exact=True).fill(pem)
    expect(page.locator('.cert')).to_have_count(1)
    expect(page.locator('.cert')).to_contain_text('SHA-256')

    open_tool('html-preview')
    page.locator('textarea').fill('<h1>本地预览</h1><script>parent.previewEscaped=true</script><img src="https://tool-privacy.invalid/image">')
    expect(page.frame_locator('iframe').locator('h1')).to_have_text('本地预览')
    assert page.evaluate('window.previewEscaped === undefined')
    assert page.locator('iframe').get_attribute('sandbox') == ''
    open_tool('markdown-preview')
    page.locator('textarea').fill('# 标题\n\n<script>window.previewEscaped=true</script>\n\n![x](https://tool-privacy.invalid/image)')
    expect(page.locator('.prose h1')).to_have_text('标题')
    expect(page.locator('.prose script')).to_have_count(0)
    expect(page.locator('.prose img')).to_have_count(0)
    assert not [url for url in external if url not in blocked], (external, blocked)

    # Theme and palette surfaces, with current screenshots rather than old artifacts.
    for palette in ['fufu-blue', 'hutao-red']:
        for theme in ['light', 'dark']:
            for width in [390, 1440]:
                page.set_viewport_size({'width': width, 'height': 1000})
                page.goto(base + '/tool')
                page.evaluate('([p,t]) => {document.documentElement.dataset.palette=p;document.documentElement.dataset.theme=t}', [palette,theme])
                expect(page.locator('.tool-card')).to_have_count(41)
                no_overflow()
                page.screenshot(path=str(out / f'tools-{palette}-{theme}-{width}.png'), full_page=False)
                page.locator('.tool-card').first.click()
                expect(page.locator('.tool-page')).to_be_visible()
                page.get_by_role('button', name='示例', exact=True).click()
                expect(page.locator('textarea[readonly]')).not_to_have_value('')
                no_overflow()
                page.screenshot(path=str(out / f'tool-editor-{palette}-{theme}-{width}.png'), full_page=True)

    page.set_viewport_size({'width': 1440, 'height': 1000})
    page.emulate_media(reduced_motion='no-preference')
    page.goto(base + '/tool'); expect(page.locator('.tool-card')).to_have_count(41)
    page.wait_for_timeout(700)
    page.get_by_role('button', name='内容生成', exact=True).click()
    leaving = page.locator('.tool-list-leave-active')
    assert leaving.count() > 0
    assert leaving.evaluate_all('els => els.every(el => el.inert)')
    page.get_by_role('button', name='格式转换', exact=True).click()
    page.get_by_role('button', name='全部', exact=True).click()
    page.wait_for_timeout(650)
    expect(page.locator('.tool-card')).to_have_count(41)
    assert page.locator('.tool-card').evaluate_all('els => els.every(el => !el.inert && Number(getComputedStyle(el).opacity) === 1)')
    page.locator('.tool-card').first.click()
    expect(page.locator('.tool-page')).to_be_visible()
    assert page.locator('.tool-heading').evaluate('el => getComputedStyle(el).animationDuration') == '0.42s'
    page.get_by_role('link', name='全部工具', exact=True).click()
    assert page.locator('.page-swap-leave-active').evaluate_all('els => els.every(el => el.inert)')
    page.emulate_media(reduced_motion='reduce')
    page.locator('.tool-card').first.click()
    expect(page.locator('.tool-page')).to_be_visible()
    assert page.locator('.tool-heading').evaluate('el => getComputedStyle(el).animationName') == 'none'
    assert not errors, errors
    browser.close()
print('All 41 tools, 5 widths, themes/palettes, files, QR, copy/download, privacy, editor focus and motion checks passed.')
