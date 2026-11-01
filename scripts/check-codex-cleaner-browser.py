"""Verify Codex JSONL cleaning, real downloads, cancellation and responsive UI."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:4173').rstrip('/')
out = Path('artifacts/codex-cleaner')
out.mkdir(parents=True, exist_ok=True)
records = [
    {'type': 'message', 'content': '你好，中文 🌍'},
    {'type': 'reasoning', 'content': '内部轨迹'},
    {'type': 'response_item', 'payload': {'type': 'Reasoning', 'encrypted_content': 'secret'}},
    {'type': 'message', 'payload': {'encrypted_content': 'secret', 'text': '保留'}},
    {'type': 'turn_context', 'reasoning_effort': 'high', 'usage': {'reasoning_output_tokens': 42}},
    {'type': 'message', 'content': '普通正文中的 reasoning'},
    {'type': 'message', 'reasoning': '移除键', 'content': [None, {'type': 'reasoning'}, {'text': '保留'}]},
]
source = '\r\n'.join(json.dumps(r, ensure_ascii=False) for r in records) + '\r\n'

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'),
        args=['--no-sandbox'],
    )
    context = browser.new_context(viewport={'width': 1440, 'height': 1100}, reduced_motion='reduce')
    page = context.new_page()
    errors, external = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda r: external.append(r.url)
            if r.url.startswith(('http:', 'https:')) and not r.url.startswith(base) else None)
    page.goto(base + '/tool')
    page.get_by_role('searchbox', name='搜索工具').fill('Codex JSONL')
    expect(page.locator('.tool-card')).to_have_count(1)
    page.locator('.tool-card').click()
    expect(page.locator('.codex-cleaner')).to_be_visible()
    expect(page).to_have_title('Codex 对话加密字段清理 · 网页工具 · a彬彬a')
    expect(page.locator('.desktop-nav [aria-current="page"]')).to_have_text('工具')
    editor = page.get_by_role('textbox', name='原始 JSONL', exact=True)
    mode = page.get_by_role('combobox', name='清理模式', exact=True)
    run = page.get_by_role('button', name='开始清理', exact=True)
    download = page.get_by_role('link', name='下载 .jsonl', exact=True)
    preview = page.get_by_role('textbox', name='清理后 JSONL 预览', exact=True)
    expect(mode).to_have_value('precise')
    expect(run).to_be_disabled()

    # Import help is opt-in, keyboard operable and preserves the current input.
    guide = page.get_by_role('region', name='如何找到并导入对话文件', exact=True)
    guide_button = page.locator('button[aria-controls="codex-import-guide"]')
    expect(guide).to_have_count(0)
    expect(guide_button).to_have_attribute('aria-expanded', 'false')
    editor.fill('{"type":"message"}')
    guide_button.click()
    expect(guide).to_be_visible()
    expect(guide_button).to_have_attribute('aria-expanded', 'true')
    guide.get_by_role('radio', name='Windows', exact=True).click()
    expect(guide.locator('.codex-import-platform code')).to_have_text('%USERPROFILE%\\.codex\\sessions')
    guide.get_by_role('radio', name='macOS', exact=True).click()
    expect(guide.locator('.codex-import-platform')).to_contain_text('Finder')
    page.keyboard.press('ArrowRight')
    expect(guide.get_by_role('radio', name='Linux', exact=True)).to_be_checked()
    expect(guide.locator('.codex-import-platform')).to_contain_text('Ctrl + L')
    guide_button.focus()
    page.keyboard.press('Enter')
    expect(guide).to_have_count(0)
    expect(guide_button).to_be_focused()
    expect(editor).to_have_value('{"type":"message"}')
    guide_button.click()
    expect(guide.get_by_role('radio', name='Linux', exact=True)).to_be_checked()
    guide_button.click()
    editor.fill('')

    def clean():
        run.click()
        expect(page.locator('.codex-cleaner-success')).to_contain_text('校验通过')

    def downloaded(expected_name=None):
        with page.expect_download() as event:
            download.click()
        file = event.value
        if expected_name:
            assert file.suggested_filename == expected_name, file.suggested_filename
        data = Path(file.path()).read_bytes()
        assert b'\r' not in data
        if data:
            assert data.endswith(b'\n')
        return [json.loads(line) for line in data.decode('utf-8').splitlines()]

    def stats(before, after, removed):
        expect(page.locator('.codex-cleaner-stats dd')).to_have_text(
            [f'{before} 行', f'{after} 行', f'{removed} 行'])

    # Import a real UTF-8 BOM/CRLF file and download the full result in every mode.
    page.get_by_label('选择 JSONL 文件', exact=True).set_input_files({
        'name': '我的 Codex 会话.jsonl', 'mimeType': 'application/x-ndjson',
        'buffer': ('\ufeff' + source).encode('utf-8'),
    })
    expect(page.locator('#codex-input-help')).to_contain_text('我的 Codex 会话.jsonl')
    clean()
    stats(7, 3, 4)
    assert downloaded('我的 Codex 会话.cleaned.jsonl') == [records[0], records[4], records[5]]

    mode.select_option('broad')
    expect(download).to_have_count(0)
    expect(preview).to_have_count(0)
    clean()
    stats(7, 1, 6)
    assert downloaded() == [records[0]]

    mode.select_option('fields')
    clean()
    stats(7, 7, 0)
    expected_fields = [records[0], {}, {'type': 'response_item'},
                       {'type': 'message', 'payload': {'text': '保留'}}, records[4], records[5],
                       {'type': 'message', 'content': [None, {'text': '保留'}]}]
    assert downloaded() == expected_fields

    # Invalid lines cannot be hidden by a filter or become a partial download.
    for choice in ['precise', 'broad', 'fields']:
        mode.select_option(choice)
        editor.fill('{}\n{"encrypted_content":broken}\n\nnull\n{}\n')
        run.click()
        alert = page.get_by_role('alert')
        expect(alert).to_contain_text('3 行无效')
        for line in [2, 3, 4]:
            expect(alert).to_contain_text(f'第 {line} 行')
        expect(download).to_have_count(0)
        expect(preview).to_have_count(0)
        expect(editor).to_have_attribute('aria-invalid', 'true')
        expect(page.locator('.codex-cleaner-stats dd')).to_have_text(['5 行', '未生成', '未生成'])

    editor.fill('{"type":"reasoning","encrypted_content":"secret"}\n')
    mode.select_option('precise')
    clean()
    stats(1, 0, 1)
    assert downloaded('codex-conversation.cleaned.jsonl') == []
    mode.select_option('fields')
    clean()
    assert downloaded() == [{}]

    many = [{'type': 'message', 'content': f'第 {n} 行'} for n in range(120)]
    editor.fill('\n'.join(json.dumps(r, ensure_ascii=False) for r in many))
    clean()
    for count in [10, 30, 100]:
        page.get_by_role('combobox', name='结果预览').select_option(str(count))
        assert len(preview.input_value().splitlines()) == count
    page.get_by_role('combobox', name='结果预览').select_option('0')
    expect(preview).to_have_count(0)
    assert downloaded() == many
    page.get_by_role('button', name='清空', exact=True).click()
    expect(editor).to_have_value('')
    expect(download).to_have_count(0)
    expect(run).to_be_disabled()

    # Required widths, both palettes and themes, with freshly rendered screenshots.
    page.get_by_role('button', name='载入示例', exact=True).click()
    mode.select_option('precise')
    clean()
    page.get_by_role('combobox', name='结果预览').select_option('10')
    guide_button.click()
    expect(guide).to_be_visible()
    for palette in ['fufu-blue', 'hutao-red']:
        for theme in ['light', 'dark']:
            page.evaluate('([p,t]) => {document.documentElement.dataset.palette=p;document.documentElement.dataset.theme=t}', [palette, theme])
            for width in [320, 390, 479, 481, 768, 1024, 1440]:
                page.set_viewport_size({'width': width, 'height': 1100})
                page.evaluate('new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                for system in ['Linux', 'macOS', 'Windows']:
                    guide.get_by_role('radio', name=system, exact=True).click()
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (palette, theme, width, system)
                expect(download).to_be_visible()
                if width in [390, 1440]:
                    page.screenshot(path=str(out / f'{palette}-{theme}-{width}.png'), full_page=True)
    page.get_by_label('选择 JSONL 文件', exact=True).focus()
    assert page.locator('.codex-cleaner-file .btn').evaluate('e => getComputedStyle(e).outlineStyle') == 'solid'
    mode.focus()
    page.keyboard.press('ArrowDown')
    expect(mode).to_have_value('broad')
    expect(download).to_have_count(0)

    # Use a delayed worker only for deterministic cancellation/race checks. The
    # conversion and downloads above use the real bundled worker.
    page.evaluate('''() => {
      window.realWorker = window.Worker;
      window.testWorkers = [];
      window.Worker = class {
        constructor() { window.testWorkers.push(this); }
        addEventListener() {}
        postMessage() {}
        terminate() { this.terminated = true; }
      };
    }''')
    run.click()
    page.get_by_role('button', name='取消', exact=True).click()
    expect(page.locator('.codex-cleaner [role="status"]')).to_contain_text('已取消')
    assert page.evaluate('testWorkers[0].terminated')
    run.click()
    editor.fill('{}')
    assert page.evaluate('testWorkers[1].terminated')
    page.evaluate('''() => {
      for (const w of testWorkers) w.onmessage({data: {result: {
        inputLines: 1, outputLines: 1, removedLines: 0, invalidLines: 0,
        modifiedLines: 0, issues: [], output: '{"stale":true}\\n'
      }}});
    }''')
    expect(download).to_have_count(0)
    run.click()
    page.get_by_role('link', name='全部工具', exact=True).click()
    expect(page.locator('.tools-directory')).to_be_visible()
    assert page.evaluate('testWorkers[2].terminated')
    page.evaluate('() => { window.Worker = window.realWorker }')
    page.goto(base + '/tools/codex-jsonl-cleaner')
    expect(editor).to_have_value('')
    expect(guide).to_have_count(0)
    assert page.evaluate('!JSON.stringify([localStorage, sessionStorage]).includes("stale")')

    # The tool also works with normal motion and after a failed worker start.
    page.emulate_media(reduced_motion='no-preference')
    page.get_by_role('button', name='载入示例', exact=True).click()
    clean()
    page.evaluate('() => { window.realWorker = window.Worker; window.Worker = class { constructor() { throw new Error("test") } } }')
    run.click()
    expect(page.get_by_role('alert')).to_contain_text('未能启动')
    expect(download).to_have_count(0)
    page.evaluate('() => { window.Worker = window.realWorker }')
    clean()
    html = context.request.get(base + '/tools/codex-jsonl-cleaner').text()
    assert 'Codex 对话加密字段清理 · 网页工具 · a彬彬a' in html
    assert 'https://zxabinbina.cc.cd/tools/codex-jsonl-cleaner' in html
    assert not external, external

    # Browser identities include mobile devices that mimic desktop platforms.
    # Detection only sets the initial choice; every case remains switchable.
    identities = [
        ({'hint': 'Windows', 'agent': 'Mozilla/5.0 (X11; Linux x86_64)', 'platform': 'Linux x86_64'}, 'Windows'),
        ({'agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'platform': 'Win32'}, 'Windows'),
        ({'agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', 'platform': 'MacIntel'}, 'macOS'),
        ({'hint': 'macOS', 'agent': 'Mozilla/5.0'}, 'macOS'),
        ({'agent': 'Mozilla/5.0 (X11; Linux x86_64)', 'platform': 'Linux x86_64'}, 'Linux'),
        ({'hint': 'Linux'}, 'Linux'),
        ({'agent': 'Unknown browser', 'platform': ''}, 'Windows'),
        ({'hint': 'Android', 'agent': 'Mozilla/5.0 (Linux; Android 14)', 'platform': 'Linux armv8l', 'touch': 5}, 'Windows'),
        ({'agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)', 'platform': 'iPhone'}, 'Windows'),
        ({'agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15)', 'platform': 'MacIntel', 'touch': 5}, 'Windows'),
        ({'hint': 'Chrome OS', 'agent': 'Mozilla/5.0 (X11; CrOS x86_64)', 'platform': 'Linux x86_64'}, 'Windows'),
        ({'hint': 'Linux', 'mobile': True}, 'Windows'),
    ]
    for device, expected in identities:
        probe = context.new_page()
        probe.on('pageerror', lambda e: errors.append(str(e)))
        probe.add_init_script('''(device => {
          Object.defineProperties(navigator, {
            userAgent: { configurable: true, get: () => device.agent || '' },
            platform: { configurable: true, get: () => device.platform || '' },
            maxTouchPoints: { configurable: true, get: () => device.touch || 0 },
            userAgentData: { configurable: true, get: () => device.hint ? {
              platform: device.hint, mobile: device.mobile || false
            } : undefined }
          })
        })(%s)''' % json.dumps(device))
        probe.goto(base + '/tools/codex-jsonl-cleaner')
        probe.get_by_role('button', name='导入教程', exact=True).click()
        system_choices = probe.get_by_role('radiogroup', name='教程适用系统', exact=True)
        expect(system_choices.get_by_role('radio', name=expected, exact=True)).to_be_checked()
        expect(probe.locator('.codex-import-platform h4')).to_have_text(expected)
        other = 'Linux' if expected != 'Linux' else 'Windows'
        system_choices.get_by_role('radio', name=other, exact=True).click()
        expect(probe.locator('.codex-import-platform h4')).to_have_text(other)
        probe.close()
    assert not errors, errors
    browser.close()
print('Codex cleaner: import guide/device detection, modes, UTF-8 files, downloads, validation, preview, cancellation, stale results, 7 widths, 4 themes and local-only processing passed.')
