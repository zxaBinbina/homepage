"""Check tools against a running build preview; no external APIs are needed."""
import os
import re
import hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:5173').rstrip('/')
out = Path('artifacts')
out.mkdir(exist_ok=True)
text_tools = ['json', 'base64', 'url', 'text', 'radix', 'hash', 'jwt', 'html']
routes = ['tool'] + ['tools/' + tool for tool in text_tools + ['timestamp', 'uuid', 'password', 'color']]

def check_resized_editors(page, capture=False):
    # Native resizing writes an inline height. Exercise either side independently,
    # including shrinking it again; the status row must remain at the panel bottom.
    editors = page.locator('.tool-editor-grid .tool-editor')
    for heights in [[640, 360], [360, 720], [300, 280]]:
        editors.locator('textarea').evaluate_all('(elements, heights) => elements.forEach((el, i) => el.style.height = `${heights[i]}px`)', heights)
        page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
        panels = editors.evaluate_all('''elements => elements.map(el => ({
            bottom: el.getBoundingClientRect().bottom,
            statusBottom: el.querySelector('.tool-editor-meta').getBoundingClientRect().bottom,
            textareaHeight: el.querySelector('textarea').getBoundingClientRect().height,
            minimum: parseFloat(getComputedStyle(el.querySelector('textarea')).minHeight)
        }))''')
        for index, panel in enumerate(panels):
            assert abs(panel['bottom'] - panel['statusBottom'] - 1) < 1, ('Blank area below editor status', heights, panels)
            assert abs(panel['textareaHeight'] - max(heights[index], panel['minimum'])) < 1, ('Resizing affected the other editor', heights, panels)
        if capture and heights == [640, 360]:
            page.screenshot(path=str(out / 'tools-editor-resize.png'), full_page=True)
    editors.locator('textarea').evaluate_all('elements => elements.forEach(el => el.style.removeProperty("height"))')

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce', timezone_id='Asia/Shanghai', permissions=['clipboard-read', 'clipboard-write'])
    page = context.new_page()
    errors, data_requests, media = [], [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('request', lambda request: data_requests.append(request.url) if request.resource_type in ['fetch', 'xhr'] else None)
    page.on('request', lambda request: media.append(request.url) if request.resource_type == 'media' else None)
    page.goto(base + '/', wait_until='networkidle')
    page.evaluate('window.toolProbe = {header: document.querySelector(".header")}')
    page.get_by_role('navigation', name='主导航', exact=True).get_by_role('link', name='工具', exact=True).click()
    expect(page).to_have_url(base + '/tool')
    expect(page.locator('.tool-card')).to_have_count(12)
    assert page.evaluate('toolProbe.header === document.querySelector(".header")')
    expect(page.locator('.desktop-nav [aria-current="page"]')).to_have_text('工具')
    page.get_by_role('button', name='编码', exact=True).click()
    expect(page.locator('.tool-card')).to_have_count(3)
    page.get_by_role('button', name='设计', exact=True).click()
    expect(page.locator('.tool-card')).to_have_count(1)
    expect(page.locator('.tool-card')).to_contain_text('颜色转换')
    page.get_by_role('searchbox', name='搜索工具').fill('not-a-tool')
    expect(page.locator('.directory-empty')).to_be_visible()
    page.get_by_role('button', name='查看全部工具').click()
    page.get_by_role('searchbox', name='搜索工具').fill('JSON')
    expect(page.locator('.tool-card')).to_have_count(1)
    page.locator('.tool-card').click()
    expect(page).to_have_title('JSON 格式化 · 网页工具 · a彬彬a')
    expect(page.locator('.tool-main')).to_be_focused()
    expect(page.locator('main')).to_have_count(1)
    assert page.evaluate('toolProbe.header === document.querySelector(".header")')
    input_box = page.locator('#tool-input')
    output = page.locator('#tool-output')
    check_resized_editors(page, capture=True)
    page.get_by_role('button', name='格式化 / 校验', exact=True).click()
    expect(page.get_by_role('alert')).to_contain_text('请先输入')
    page.get_by_role('button', name='示例', exact=True).click()
    page.get_by_role('button', name='格式化 / 校验', exact=True).click()
    assert '1234567890123456789' in output.input_value()
    assert '\n' in output.input_value()
    page.get_by_role('button', name='复制', exact=True).click()
    assert page.evaluate('navigator.clipboard.readText()') == output.input_value()
    with page.expect_download() as info:
        page.get_by_role('button', name='下载', exact=True).click()
    assert info.value.suggested_filename == 'formatted.json'
    assert Path(info.value.path()).read_text() == output.input_value()
    page.get_by_role('button', name='压缩 JSON', exact=True).click()
    assert '\n' not in output.input_value()
    input_box.fill('{"broken":}')
    expect(output).to_have_value('')
    expect(page.get_by_role('button', name='复制', exact=True)).to_be_disabled()
    page.get_by_role('button', name='格式化 / 校验', exact=True).click()
    expect(page.get_by_role('alert')).to_contain_text('JSON 语法有误')
    input_box.fill('{"safe":"<script>alert(1)</script>"}')
    page.get_by_role('button', name='格式化 / 校验', exact=True).click()
    assert '<script>' in output.input_value()
    page.evaluate('Object.defineProperty(navigator,"clipboard",{value:{writeText:()=>Promise.reject(new Error("blocked"))},configurable:true})')
    page.get_by_role('button', name='复制', exact=True).click()
    expect(page.locator('.tool-output [role="status"]')).to_contain_text('请手动复制')
    expect(output).to_be_focused()
    assert output.evaluate('(el)=>el.selectionEnd - el.selectionStart') == len(output.input_value())
    page.get_by_role('button', name='清空', exact=True).click()
    expect(input_box).to_have_value('')
    expect(output).to_have_value('')
    page.go_back()
    expect(page).to_have_url(base + '/tool')
    page.go_forward()
    expect(page).to_have_url(base + '/tools/json')

    for route in ['base64', 'url']:
        page.goto(base + '/tools/' + route, wait_until='networkidle')
        source = '你好 🌍 &/?=+ hello'
        input_box.fill(source)
        page.get_by_role('button', name='编码', exact=True).click()
        assert output.input_value() != source
        page.get_by_role('button', name='将结果用作输入').click()
        page.get_by_role('button', name='解码', exact=True).click()
        expect(output).to_have_value(source)
        input_box.fill('%%bad')
        page.get_by_role('button', name='解码', exact=True).click()
        expect(page.get_by_role('alert')).to_be_visible()
        expect(output).to_have_value('')
    page.get_by_label('解码时将 + 视为空格').check()
    input_box.fill('hello+world%2B')
    page.get_by_role('button', name='解码', exact=True).click()
    expect(output).to_have_value('hello world+')

    page.goto(base + '/tools/timestamp', wait_until='networkidle')
    page.get_by_label('Unix 时间戳', exact=True).fill('0')
    page.get_by_role('button', name='转为日期', exact=True).click()
    assert '1970-01-01T00:00:00.000Z' in output.input_value()
    assert '1970-01-01 08:00:00.000' in output.input_value()
    page.get_by_label('时间单位', exact=True).select_option('milliseconds')
    page.get_by_label('Unix 时间戳', exact=True).fill('-1')
    page.get_by_role('button', name='转为日期', exact=True).click()
    assert '1969-12-31T23:59:59.999Z' in output.input_value()
    page.get_by_label('日期时区', exact=True).select_option('utc')
    page.get_by_label('日期与时间', exact=True).fill('2024-01-01T00:00:00.123')
    page.get_by_role('button', name='转为时间戳', exact=True).click()
    assert '1704067200123' in output.input_value()
    page.get_by_label('Unix 时间戳', exact=True).fill('abc')
    page.get_by_role('button', name='转为日期', exact=True).click()
    expect(page.get_by_role('alert')).to_contain_text('整数时间戳')
    page.get_by_role('button', name='使用当前时间').click()
    expect(page.get_by_role('alert')).to_have_count(0)
    assert 'UTC' in output.input_value()

    page.goto(base + '/tools/uuid', wait_until='networkidle')
    page.get_by_label('数量', exact=True).fill('100')
    page.get_by_role('button', name='生成 UUID').click()
    ids = output.input_value().splitlines()
    assert len(ids) == len(set(ids)) == 100
    assert all(re.fullmatch(r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}', value) for value in ids)
    page.get_by_label('大写字母').check()
    page.get_by_label('保留连字符').uncheck()
    page.get_by_role('button', name='生成 UUID').click()
    assert all(re.fullmatch(r'[0-9A-F]{32}', value) for value in output.input_value().splitlines())
    page.get_by_label('数量', exact=True).fill('101')
    page.get_by_role('button', name='生成 UUID').click()
    expect(output).to_have_value('')

    page.goto(base + '/tools/text', wait_until='networkidle')
    input_box.fill('apple\napple\n  \nBanana')
    page.get_by_role('button', name='按行去重').click()
    expect(output).to_have_value('apple\n  \nBanana')
    page.get_by_role('button', name='将结果用作输入').click()
    page.get_by_role('button', name='移除空行').click()
    expect(output).to_have_value('apple\nBanana')
    input_box.fill('  \n\t')
    page.get_by_role('button', name='移除空行').click()
    expect(page.locator('.tool-output [role="status"]')).to_contain_text('结果为空文本')
    expect(page.get_by_role('button', name='复制', exact=True)).to_be_enabled()

    page.goto(base + '/tools/radix', wait_until='networkidle')
    input_box.fill('123456789012345678901234567890')
    page.get_by_role('button', name='转换进制').click()
    expect(output).to_have_value(format(123456789012345678901234567890, 'X'))
    page.get_by_label('输入进制', exact=True).select_option('16')
    expect(output).to_have_value('')
    input_box.fill('-0xFF')
    page.get_by_label('输出进制', exact=True).select_option('10')
    page.get_by_role('button', name='转换进制').click()
    expect(output).to_have_value('-255')
    input_box.fill('XYZ')
    page.get_by_role('button', name='转换进制').click()
    expect(page.get_by_role('alert')).to_be_visible()

    page.goto(base + '/tools/hash', wait_until='networkidle')
    page.get_by_role('button', name='计算哈希').click()
    expect(output).to_have_value(hashlib.sha256(b'').hexdigest())
    input_box.fill('你好 🌍')
    page.get_by_label('哈希算法').select_option('SHA-512')
    page.get_by_label('输出大写').check()
    page.get_by_role('button', name='计算哈希').click()
    expect(output).to_have_value(hashlib.sha512('你好 🌍'.encode()).hexdigest().upper())
    # Hold the digest promise, then edit input or options before it resolves.
    page.evaluate('''() => {
        const digest = crypto.subtle.digest.bind(crypto.subtle);
        crypto.subtle.digest = (...args) => new Promise((resolve, reject) => {
            window.finishDigest = () => digest(...args).then(resolve, reject);
        });
    }''')
    for change in ['input', 'algorithm']:
        page.get_by_role('button', name='计算哈希').click()
        expect(page.get_by_role('button', name='计算中…')).to_be_disabled()
        if change == 'input':
            input_box.fill('changed')
        else:
            page.get_by_label('哈希算法').select_option('SHA-256')
        page.evaluate('async () => { await window.finishDigest(); await new Promise(requestAnimationFrame); }')
        expect(output).to_have_value('')
        expect(page.get_by_role('button', name='复制', exact=True)).to_be_disabled()

    page.goto(base + '/tools/jwt', wait_until='networkidle')
    page.get_by_role('button', name='示例', exact=True).click()
    page.get_by_role('button', name='解析 JWT').click()
    assert 'a彬彬a' in output.input_value()
    assert '签名：未验证' in output.input_value()
    assert '2030-01-01T00:00:00.000Z' in output.input_value()
    input_box.fill('bad.token')
    page.get_by_role('button', name='解析 JWT').click()
    expect(page.get_by_role('alert')).to_be_visible()
    expect(output).to_have_value('')

    page.goto(base + '/tools/html', wait_until='networkidle')
    source = '<p title="中文">a & b</p>'
    input_box.fill(source)
    page.get_by_role('button', name='转义', exact=True).click()
    expect(output).to_have_value('&lt;p title=&quot;中文&quot;&gt;a &amp; b&lt;/p&gt;')
    page.get_by_role('button', name='将结果用作输入').click()
    page.get_by_role('button', name='还原', exact=True).click()
    expect(output).to_have_value(source)
    input_box.fill('&copy; &#65; &#x1F30D; &amp;lt; &unknown;')
    page.get_by_role('button', name='还原', exact=True).click()
    expect(output).to_have_value('© A 🌍 &lt; &unknown;')
    source = '</textarea><img src="/tool-html-probe" onerror="window.htmlExecuted=true">&lt;script&gt;'
    probe_requests = []
    page.on('request', lambda request: probe_requests.append(request.url) if '/tool-html-probe' in request.url else None)
    input_box.fill(source)
    page.get_by_role('button', name='还原', exact=True).click()
    expect(output).to_have_value(source.replace('&lt;script&gt;', '<script>'))
    assert page.evaluate('window.htmlExecuted === undefined')
    assert not probe_requests

    page.goto(base + '/tools/password', wait_until='networkidle')
    page.get_by_label('密码长度', exact=True).fill('24')
    page.get_by_label('生成数量', exact=True).fill('10')
    page.get_by_role('button', name='生成密码').click()
    passwords = output.input_value().splitlines()
    assert len(passwords) == 10
    assert all(len(value) == 24 and not re.search(r'[0Oo1Il|]', value) for value in passwords)
    page.get_by_role('button', name='复制', exact=True).click()
    assert page.evaluate('navigator.clipboard.readText()') == output.input_value()
    with page.expect_download() as info:
        page.get_by_role('button', name='下载', exact=True).click()
    assert info.value.suggested_filename == 'passwords.txt'
    assert Path(info.value.path()).read_text() == output.input_value()
    for label in ['小写字母', '大写字母', '数字', '符号']:
        page.get_by_label(label, exact=True).uncheck()
    expect(output).to_have_value('')
    page.get_by_role('button', name='生成密码').click()
    expect(page.get_by_role('alert')).to_contain_text('至少选择')
    page.get_by_label('数字', exact=True).check()
    page.get_by_role('button', name='生成密码').click()
    assert all(re.fullmatch(r'[2-9]{24}', value) for value in output.input_value().splitlines())
    page.get_by_label('密码长度', exact=True).fill('7')
    page.get_by_role('button', name='生成密码').click()
    expect(output).to_have_value('')

    page.goto(base + '/tools/color', wait_until='networkidle')
    page.get_by_label('输入颜色', exact=True).fill('hsl(120, 100%, 50%)')
    page.get_by_role('button', name='转换颜色').click()
    assert '#00FF00' in output.input_value()
    expect(page.get_by_role('img', name='颜色预览：#00FF00')).to_have_css('background-color', 'rgb(0, 255, 0)')
    page.get_by_label('取色器').fill('#ff0000')
    assert '#FF0000' in output.input_value()
    expect(page.get_by_label('输入颜色', exact=True)).to_have_value('#ff0000')
    page.get_by_label('输入颜色', exact=True).fill('rgb(256, 0, 0)')
    expect(output).to_have_value('')
    page.get_by_role('button', name='转换颜色').click()
    expect(page.get_by_role('alert')).to_be_visible()

    # Every address loads its own metadata directly and after refresh.
    for route in routes:
        response = context.request.get(base + '/' + route)
        assert response.status == 200
        assert f'href="https://zxabinbina.cc.cd/{route}"' in response.text()
        assert 'href="/favicon.svg"' in response.text()
        for suffix in ['/', '.html', '/index.html']:
            response = context.request.get(base + '/' + route + suffix + '?from=test', max_redirects=0)
            assert response.status == 301
            assert response.headers['location'] == '/' + route + '?from=test'
        page.goto(base + '/' + route, wait_until='networkidle')
        page.reload(wait_until='networkidle')
        expect(page.locator('main h1')).to_be_visible()
        expect(page.locator('.desktop-nav [aria-current="page"]')).to_have_text('工具')
        expect(page.locator('link[rel="canonical"]')).to_have_attribute('href', 'https://zxabinbina.cc.cd/' + route)
        if page.locator('#tool-input').count():
            input_box.fill('x' * 2000)
        for theme in ['dark', 'light']:
            page.get_by_role('button', name='切换' + ('浅色' if theme == 'light' else '深色') + '主题').click() if page.locator('html').get_attribute('data-theme') != theme else None
            for width in [320, 390, 480, 481, 760, 761, 768, 1024, 1050, 1051, 1440]:
                page.set_viewport_size({'width': width, 'height': 1000})
                page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (route, theme, width)
                if route in ['tools/' + tool for tool in text_tools] and width in [390, 768, 1440]:
                    check_resized_editors(page)
                assert page.locator('.tool-workspace button').evaluate_all('buttons => buttons.every(button => button.getBoundingClientRect().height >= 44)'), ('small touch target', route, width)
                assert page.locator('.header').evaluate('el => [...el.querySelectorAll("a,button")].filter(e => e.getBoundingClientRect().width).every(e => e.getBoundingClientRect().right <= el.getBoundingClientRect().right + 1)'), ('header overflow', route, theme, width, page.locator('.header').evaluate('el => ({header:el.getBoundingClientRect().toJSON(), children:[...el.querySelectorAll("a,button")].filter(e=>e.getBoundingClientRect().width).map(e=>({text:e.textContent, label:e.getAttribute("aria-label"),rect:e.getBoundingClientRect().toJSON()}))})'))
                if route in ['tool', 'tools/json', 'tools/timestamp', 'tools/password', 'tools/color'] and width in [390, 1440]:
                    if route == 'tools/json':
                        page.get_by_role('button', name='示例', exact=True).click()
                        page.get_by_role('button', name='格式化 / 校验', exact=True).click()
                    elif route == 'tools/password':
                        page.get_by_role('button', name='生成密码').click()
                    elif route == 'tools/color':
                        page.get_by_role('button', name='示例', exact=True).click()
                    page.evaluate('scrollTo({top:0,behavior:"instant"})')
                    page.screenshot(path=str(out / f'{route.replace("/", "-")}-{theme}-{width}.png'), full_page=True)
        page.set_viewport_size({'width': 1440, 'height': 1000})

    page.set_viewport_size({'width': 320, 'height': 844})
    page.get_by_role('button', name='打开菜单').click()
    expect(page.locator('#mobile-nav [aria-current="page"]')).to_have_text('工具')
    page.locator('#mobile-nav').get_by_role('link', name='工具', exact=True).click()
    expect(page).to_have_url(base + '/tool')
    expect(page.locator('#mobile-nav')).to_have_count(0)
    page.get_by_role('button', name='打开菜单').click()
    page.keyboard.press('Escape')
    expect(page.locator('#mobile-nav')).to_have_count(0)
    page.emulate_media(reduced_motion='no-preference')
    page.locator('.tool-card').first.click()
    expect(page.locator('.tool-main h1')).to_have_text('JSON 格式化')
    expect(page.locator('.tool-main')).to_be_focused()
    page.locator('#tool-input').focus()
    assert page.locator('#tool-input').evaluate('el => getComputedStyle(el).outlineStyle') != 'none'
    page.reload(wait_until='networkidle')
    expect(page.locator('html')).to_have_attribute('data-theme', 'light')
    assert not errors, errors
    assert not data_requests, data_requests
    assert not media, media
    browser.close()
print('Tools UI: all 12 tools, errors, stale async results, clipboard/download, local processing, navigation, direct URLs, themes, independent editor resizing, keyboard and 11 responsive widths passed. Fresh screenshots saved in artifacts/.')
