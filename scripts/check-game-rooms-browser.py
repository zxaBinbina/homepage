"""Real multi-browser gameplay against the local Workers fixture; widget/network are mocked."""
import os
import re
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:8796').rstrip('/')
out = Path('artifacts/rooms')
out.mkdir(parents=True, exist_ok=True)
widget_script = r'''(()=>{let next=0;const widgets=new Map();window.turnstile={render(element,options){const id=String(++next);element.dataset.widgetTheme=options.theme;element.dataset.widgetSize=options.size;const button=document.createElement('button');button.type='button';button.textContent='测试安全验证';button.style.cssText='width:'+ (options.size==='compact'?'150px':'300px')+';height:'+(options.size==='compact'?'140px':'65px')+';max-width:100%;border:1px solid #888;border-radius:4px;background:transparent;color:inherit';button.onclick=()=>{button.textContent='验证成功';options.callback((options.action==='room_join'?'join-':'create-')+Date.now()+'-'+id)};element.replaceChildren(button);widgets.set(id,{element,button,options});return id},remove(id){const value=widgets.get(id);if(value)value.element.replaceChildren();widgets.delete(id)},reset(id){const value=widgets.get(id);if(value){value.button.textContent='测试安全验证';value.options['expired-callback']()}}}})();'''

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    errors = []
    contexts = []

    def client(width=1440):
        context = browser.new_context(viewport={'width': width, 'height': 1100}, reduced_motion='reduce', color_scheme='dark')
        context.route('https://challenges.cloudflare.com/turnstile/v0/api.js*', lambda route: route.fulfill(content_type='application/javascript', body=widget_script))
        contexts.append(context)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        return page

    def visit(page, kind):
        page.goto(base + '/games/' + kind, wait_until='networkidle')
        page.get_by_role('radio', name='朋友联机', exact=True).click()
        expect(page.get_by_role('button', name='测试安全验证')).to_be_visible()

    def create(page, kind, name):
        visit(page, kind)
        page.get_by_label('你的昵称', exact=True).fill(name)
        expect(page.get_by_role('button', name='创建房间', exact=True)).to_be_disabled()
        page.get_by_role('button', name='测试安全验证').click()
        page.get_by_role('button', name='创建房间', exact=True).click()
        expect(page.locator('.room-number')).to_be_visible()
        expect(page.get_by_role('button', name='我准备好了', exact=True)).to_be_visible()
        return re.search(r'\d{6}', page.locator('.room-number').inner_text()).group()

    def join(page, code, name, kind='gomoku'):
        visit(page, kind)
        page.get_by_role('radio', name='加入房间', exact=True).click()
        page.get_by_label('你的昵称', exact=True).fill(name)
        page.get_by_label('6 位数字房间号', exact=True).fill(code)
        expect(page.get_by_role('button', name='加入房间', exact=True)).to_be_disabled()
        page.get_by_role('button', name='测试安全验证').click()
        page.get_by_role('button', name='加入房间', exact=True).click()

    def start(host, guest):
        expect(host.get_by_role('button', name='开始对局', exact=True)).to_be_disabled()
        host.get_by_role('button', name='我准备好了', exact=True).click()
        guest.get_by_role('button', name='我准备好了', exact=True).click()
        host.get_by_role('button', name='开始对局', exact=True).click()
        expect(host.locator('.room-board')).to_be_visible()
        expect(guest.locator('.room-board')).to_be_visible()

    def stone(page, to):
        expect(page.locator('.room-toolbar .strategy-turn')).to_have_text('轮到你了')
        page.locator('.room-board [data-at="' + str(to) + '"]').click()
        page.get_by_role('button', name='确认落子', exact=True).click()

    def move(page, source, target):
        expect(page.locator('.room-toolbar .strategy-turn')).to_have_text('轮到你了')
        page.locator('.room-board [data-at="' + str(source) + '"]').click()
        page.locator('.room-board [data-at="' + str(target) + '"]').click()

    def leave(page):
        page.get_by_role('button', name='离开房间', exact=True).click()
        page.get_by_role('button', name='确认离开', exact=True).click()
        expect(page.get_by_role('radio', name='单机对战', exact=True)).to_have_attribute('aria-checked', 'true')

    def check_leave_position(page):
        page.wait_for_function("getComputedStyle(document.querySelector('.room-leave-popover')).opacity === '1'")
        result = page.evaluate('''() => {
            const panel = document.querySelector('.room-leave-popover');
            const button = document.querySelector('.room-leave-control > button');
            const box = panel.getBoundingClientRect(), anchor = button.getBoundingClientRect();
            const style = getComputedStyle(panel), gap = parseFloat(style.getPropertyValue('--space-sm'));
            const distance = panel.dataset.side === 'below' ? box.top - anchor.bottom : anchor.top - box.bottom;
            const arrow = box.left + parseFloat(style.getPropertyValue('--room-leave-arrow-left'));
            const valid = box.left >= gap - 1 && box.right <= innerWidth - gap + 1
                && box.top >= gap - 1 && box.bottom <= innerHeight - gap + 1
                && Math.abs(distance - gap) < 1
                && Math.abs(arrow - (anchor.left + anchor.width / 2)) < 1;
            return {valid, box:box.toJSON(), anchor:anchor.toJSON(), distance, gap, arrow, side:panel.dataset.side};
        }''')
        assert result['valid'], ('Leave confirmation must remain beside its button, with its arrow pointing at it', result)

    def open_leave(page):
        page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
        before = page.locator('.room-surface').bounding_box()['height']
        page.get_by_role('button', name='离开房间', exact=True).click()
        panel = page.get_by_role('dialog', name='确认离开房间？', exact=True)
        expect(panel).to_be_visible()
        expect(page.get_by_role('button', name='继续留在房间', exact=True)).to_be_focused()
        check_leave_position(page)
        after = page.locator('.room-surface').bounding_box()['height']
        assert abs(after - before) < 1, ('Popover must not resize the room or board', before, after, page.viewport_size)
        return panel

    host, guest, newcomer = client(), client(390), client(320)
    code = create(host, 'gomoku', '房主')
    open_leave(host)
    host.evaluate('window.scrollBy(0, 60)')
    host.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
    check_leave_position(host)
    host.keyboard.press('Escape')
    expect(host.get_by_role('dialog', name='确认离开房间？', exact=True)).not_to_be_visible()
    expect(host.get_by_role('button', name='离开房间', exact=True)).to_be_focused()
    open_leave(host)
    host.get_by_role('button', name='离开房间', exact=True).click()
    expect(host.get_by_role('dialog', name='确认离开房间？', exact=True)).not_to_be_visible()
    open_leave(host)
    host.mouse.click(4, 500)
    expect(host.get_by_role('dialog', name='确认离开房间？', exact=True)).not_to_be_visible()
    host.get_by_role('radio', name='单机对战', exact=True).click()
    expect(host.get_by_role('dialog', name='确认离开房间？', exact=True)).to_be_visible()
    check_leave_position(host)
    host.get_by_role('button', name='继续留在房间', exact=True).click()
    expect(host.locator('.room-number')).to_contain_text(code)
    host.set_viewport_size({'width': 1440, 'height': 400})
    host.get_by_role('button', name='离开房间', exact=True).scroll_into_view_if_needed()
    host.evaluate('''() => {
        const anchor = document.querySelector('.room-leave-control > button').getBoundingClientRect();
        window.scrollBy(0, anchor.bottom - (innerHeight - 20));
    }''')
    open_leave(host)
    expect(host.locator('.room-leave-popover')).to_have_attribute('data-side', 'above')
    host.keyboard.press('Escape')
    host.set_viewport_size({'width': 1440, 'height': 1100})
    # Joining from a different game must route to the room's actual game.
    join(guest, code, '朋友', 'chess')
    expect(guest).to_have_url(base + '/games/gomoku')
    host.locator('.room-surface').screenshot(path=str(out / 'lobby-dark-desktop.png'))
    start(host, guest)
    stone(host, 112); expect(guest.locator('.room-board .strategy-piece')).to_have_count(1)
    stone(guest, 113); expect(host.locator('.room-board .strategy-piece')).to_have_count(2)
    host.get_by_role('button', name='悔棋', exact=True).click()
    guest.get_by_role('button', name='同意', exact=True).click()
    expect(host.locator('.room-board .strategy-piece')).to_have_count(0)
    expect(guest.locator('.room-board .strategy-piece')).to_have_count(0)
    host.get_by_role('button', name='房间聊天', exact=False).click()
    host.get_by_label('聊天消息').fill('<script>只是聊天文字</script>')
    host.get_by_role('button', name='发送消息').click()
    guest.get_by_role('button', name='房间聊天', exact=False).click()
    expect(guest.locator('.room-chat-log')).to_contain_text('<script>只是聊天文字</script>')
    host.reload(wait_until='networkidle')
    expect(host.locator('.room-number')).to_contain_text(code)
    expect(host.locator('.room-board .strategy-piece')).to_have_count(0)
    copied_session = host.evaluate("sessionStorage.getItem('homepage-game-room')")
    duplicate = host.context.new_page()
    duplicate.add_init_script("sessionStorage.setItem('homepage-game-room', " + json.dumps(copied_session) + ")")
    duplicate.goto(base + '/games/gomoku', wait_until='networkidle')
    expect(duplicate.locator('.room-number')).to_contain_text(code)
    expect(host.locator('.room-feedback').filter(has_text='其他标签页')).to_be_visible()
    duplicate.wait_for_timeout(1500)
    expect(duplicate.locator('.room-toolbar .strategy-turn')).to_have_text('轮到你了')
    host.get_by_role('button', name='重新连接', exact=True).click()
    expect(duplicate.locator('.room-feedback').filter(has_text='其他标签页')).to_be_visible()
    duplicate.close()
    host.get_by_role('button', name='网页全屏', exact=True).click()
    expect(host.locator('.game-fullscreen-dialog')).to_be_visible()
    expect(host.locator('.room-number')).to_contain_text(code)
    open_leave(host)
    host.keyboard.press('Escape')
    expect(host.get_by_role('dialog', name='确认离开房间？', exact=True)).not_to_be_visible()
    expect(host.locator('.game-fullscreen-dialog')).to_be_visible()
    host.keyboard.press('Escape')
    expect(host.locator('.game-fullscreen-dialog')).not_to_be_visible()
    join(newcomer, code, '新朋友')
    expect(newcomer.locator('.room-feedback')).to_contain_text('本局正在进行')
    for index, target in enumerate([112, 113, 111, 114, 110, 115, 109, 116, 108]):
        stone(host if index % 2 == 0 else guest, target)
    expect(host.locator('.game-result')).to_contain_text('你赢了')
    expect(guest.get_by_role('button', name='我准备好了', exact=True)).to_be_visible()
    leave(guest)
    newcomer.get_by_role('button', name='测试安全验证').click()
    newcomer.get_by_role('button', name='加入房间', exact=True).click()
    expect(newcomer.locator('.room-number')).to_contain_text(code)
    expect(host.get_by_role('button', name='悔棋', exact=True)).to_have_count(0)
    leave(newcomer); leave(host)

    for kind in ['xiangqi', 'chess', 'go', 'junqi']:
        code = create(host, kind, '房主')
        join(guest, code, '朋友', kind)
        expect(guest.locator('.room-number')).to_contain_text(code)
        if kind == 'junqi':
            host.get_by_label('军旗玩法').select_option('hidden')
        start(host, guest)
        if kind == 'xiangqi':
            move(host, 54, 45); move(guest, 27, 36)
        elif kind == 'chess':
            move(host, 52, 36); move(guest, 12, 28)
        elif kind == 'go':
            stone(host, 40); stone(guest, 41)
            host.get_by_role('button', name='停一手', exact=True).click()
            guest.get_by_role('button', name='停一手', exact=True).click()
            host.get_by_role('button', name='确认数子', exact=True).click()
            guest.get_by_role('button', name='确认数子', exact=True).click()
            expect(host.locator('.game-result')).to_be_visible()
        else:
            expect(host.locator('.junqi-piece.is-hidden').first).to_be_visible()
            expect(guest.locator('.junqi-piece.is-hidden').first).to_be_visible()
            host.get_by_role('button', name='确认布阵', exact=True).click()
            guest.get_by_role('button', name='确认布阵', exact=True).click()
            expect(host.locator('.room-toolbar .strategy-turn')).to_have_text('轮到你了')
            for cell in host.locator('.room-board .board-cell:has(.junqi-piece.is-self)').all():
                cell.click()
                targets = host.locator('.room-board .is-target:not(:has(.junqi-piece))')
                if targets.count():
                    targets.first.click(); break
            expect(guest.locator('.room-toolbar .strategy-turn')).to_have_text('轮到你了')
        guest.locator('.room-surface').screenshot(path=str(out / (kind + '-mobile.png')))
        assert guest.evaluate('document.documentElement.scrollWidth <= innerWidth'), kind + ' overflow'
        leave(guest); leave(host)

    trio = [client(), client(390), client(320)]
    code = create(trio[0], 'doudizhu', '房主')
    for index in [1, 2]:
        join(trio[index], code, '朋友' + str(index), 'doudizhu')
        expect(trio[index].locator('.room-number')).to_contain_text(code)
    for page in trio: page.get_by_role('button', name='我准备好了', exact=True).click()
    trio[0].get_by_role('button', name='开始对局', exact=True).click()
    for page in trio: expect(page.locator('.room-hand .dd-card')).to_have_count(17)
    trio[0].get_by_role('button', name='叫 3 分', exact=True).click()
    expect(trio[0].locator('.room-hand .dd-card')).to_have_count(20)
    trio[0].locator('.room-hand .dd-card').first.click()
    trio[0].get_by_role('button', name='出牌', exact=True).click()
    expect(trio[1].locator('.dd-played .playing-card')).to_have_count(1)
    trio[1].get_by_role('button', name='不出', exact=True).click()
    trio[2].get_by_role('button', name='不出', exact=True).click()
    expect(trio[0].locator('.room-toolbar .strategy-turn')).to_have_text('轮到你了')
    trio[2].locator('.room-surface').screenshot(path=str(out / 'doudizhu-320.png'))
    assert trio[2].evaluate('document.documentElement.scrollWidth <= innerWidth'), '斗地主 overflow'
    for page in trio: leave(page)

    code = create(host, 'gomoku', '气泡验证')
    for width in [320, 390, 768, 1024, 1440]:
        host.set_viewport_size({'width': width, 'height': 844})
        for theme in ['dark', 'light']:
            for palette in ['fufu-blue', 'hutao-red']:
                host.evaluate('([theme,palette])=>{document.documentElement.dataset.theme=theme;document.documentElement.dataset.palette=palette}', [theme, palette])
                open_leave(host)
                if width in [320, 1440]:
                    host.screenshot(path=str(out / f'leave-popover-{theme}-{palette}-{width}.png'))
                host.get_by_role('button', name='继续留在房间', exact=True).click()
        host.get_by_role('button', name='网页全屏', exact=True).click()
        open_leave(host)
        assert host.get_by_role('button', name='确认离开', exact=True).bounding_box()['height'] >= 43, 'Fullscreen popover controls must remain readable and usable'
        host.keyboard.press('Escape')
        expect(host.locator('.game-fullscreen-dialog')).to_be_visible()
        host.keyboard.press('Escape')
        expect(host.locator('.game-fullscreen-dialog')).not_to_be_visible()
    host.emulate_media(reduced_motion='no-preference')
    host.get_by_role('button', name='离开房间', exact=True).click()
    samples = host.locator('.room-leave-popover').evaluate('''async panel => {
        const values = [], start = performance.now();
        while (performance.now() - start < 250) {
            values.push(parseFloat(getComputedStyle(panel).opacity));
            await new Promise(requestAnimationFrame);
        }
        return values;
    }''')
    assert any(0 < value < 1 for value in samples) and samples[-1] == 1, 'Popover should fade in'
    host.keyboard.press('Escape')
    host.locator('.room-leave-popover .game-button').first.focus()
    expect(host.get_by_role('button', name='离开房间', exact=True)).to_be_focused()
    host.emulate_media(reduced_motion='reduce')
    leave(host)

    for width in [320, 390, 768, 1024, 1440]:
        host.set_viewport_size({'width': width, 'height': 1100})
        visit(host, 'gomoku')
        for theme in ['dark', 'light']:
            for palette in ['fufu-blue', 'hutao-red']:
                host.evaluate('([theme,palette])=>{document.documentElement.dataset.theme=theme;document.documentElement.dataset.palette=palette}', [theme, palette])
                expect(host.locator('[data-widget-theme]')).to_have_attribute('data-widget-theme', theme)
                assert host.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, theme, palette)
        if width == 320: host.locator('.room-surface').screenshot(path=str(out / 'entry-light-320.png'))
    assert not errors, errors
    for context in contexts: context.close()
    browser.close()
print('Six multiplayer UIs, cross-game routing, seats, refresh, consent, chat and fullscreen: passed. Leave popover placement, arrow, focus, dismissal, motion and four themes at five widths: passed.')
