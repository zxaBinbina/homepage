"""Dev-only fixtures exercise real special moves, animation cancellation and scoring controls."""
import os
import re
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL','http://127.0.0.1:5173').rstrip('/')
out=Path('artifacts')
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER','/usr/bin/google-chrome'),args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='no-preference')
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    def visit(kind):
        page.goto(base+'/games/'+kind,wait_until='networkidle')
        expect(page.locator('.strategy-surface')).to_be_visible()
    def fixture_chess(fen):
        page.evaluate('''fen=>{ const s=document.querySelector('.chess-surface').__vueParentComponent.setupState;
          s.restart(); s.game={fen,positions:[fen.split(' ').slice(0,4).join(' ')],ply:0,last:null};
        }''',fen)
    def hold():
        page.evaluate('''()=>{
          window.held=[]; const animate=Element.prototype.animate;
          Element.prototype.animate=function(...args) {
            const a=animate.apply(this,args);
            if(this.closest('.strategy-board')) {a.pause();held.push(a)}
            return a;
          };
        }''')
    def move(start,end):
        page.locator(f'[data-square="{start}"]').click()
        page.locator(f'[data-square="{end}"]').click()
    def ready():
        expect(page.locator('.strategy-surface')).to_have_attribute('aria-busy','false',timeout=12000)

    visit('chess')
    hold()
    fixture_chess('r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1')
    page.get_by_role('button',name='网页全屏',exact=True).click()
    page.set_viewport_size({'width':844,'height':390})
    move('e1','g1')
    expect(page.locator('.strategy-surface')).to_have_attribute('aria-busy','true')
    assert page.evaluate('held.length===2 && held.every(a=>a.effect.getTiming().duration===240)')
    assert page.evaluate('held.every(a=>a.effect.getKeyframes()[0].transform!==a.effect.getKeyframes()[1].transform)')
    page.locator('[data-square="a1"]').dispatch_event('click')
    page.locator('[data-square="a2"]').dispatch_event('click')
    expect(page.locator('[data-square="a1"] .chess-piece-art')).to_have_count(1)
    page.get_by_role('button',name='悔棋',exact=True).click()
    ready()
    expect(page.locator('[data-square="e1"]')).to_have_attribute('aria-label','e1：白王')
    expect(page.locator('[data-square="h1"]')).to_have_attribute('aria-label','h1：白车')
    assert page.evaluate('held.every(a=>a.playState==="idle")')
    page.keyboard.press('Escape')
    page.set_viewport_size({'width':1440,'height':1000})
    move('e1','c1')
    page.emulate_media(reduced_motion='reduce')
    ready()
    expect(page.locator('[data-square="c1"]')).to_have_attribute('aria-label','c1：白王')
    expect(page.locator('[data-square="d1"]')).to_have_attribute('aria-label','d1：白车')

    # Underpromotion must remain a choice, work with keyboard, and keep fullscreen fit.
    for piece,name in [('q','后'),('r','车'),('b','象'),('n','马')]:
        fixture_chess('7k/P7/8/8/8/8/8/7K w - - 0 1')
        move('a7','a8')
        expect(page.locator('.chess-promotion')).to_be_visible()
        expect(page.locator('.chess-promotion button').first).to_be_focused()
        expect(page.locator('[data-square="a7"] .chess-piece-art')).to_have_count(1)
        page.get_by_role('button',name='网页全屏',exact=True).click()
        page.set_viewport_size({'width':320,'height':740})
        page.wait_for_function('''()=>{const r=document.querySelector('.chess-promotion').getBoundingClientRect();return r.right<=innerWidth+.5&&r.bottom<=innerHeight+.5}''')
        page.locator('.chess-promotion').screenshot(path=str(out/f'game-chess-promotion-{piece}.png'))
        page.locator('.chess-promotion').get_by_role('button',name=name,exact=True).click()
        ready()
        expect(page.locator('[data-square="a8"]')).to_have_attribute('aria-label',re.compile(f'^a8：白{name}'))
        page.get_by_role('button',name='悔棋',exact=True).click()
        expect(page.locator('[data-square="a7"]')).to_have_attribute('aria-label','a7：白兵')
        page.keyboard.press('Escape')
        page.set_viewport_size({'width':1440,'height':1000})
    fixture_chess('7k/P7/8/8/8/8/8/7K w - - 0 1')
    move('a7','a8')
    page.keyboard.press('Escape')
    expect(page.locator('.chess-promotion')).to_have_count(0)
    expect(page.locator('[data-square="a8"]')).to_be_focused()
    expect(page.locator('[data-square="a7"] .chess-piece-art')).to_have_count(1)
    fixture_chess('7k/5Q2/6K1/8/8/8/8/8 w - - 0 1')
    move('f7','g7')
    expect(page.locator('.game-result')).to_contain_text('你赢了')
    page.get_by_role('button',name='悔棋',exact=True).click()
    expect(page.locator('.game-result')).to_have_count(0)

    visit('go')
    page.emulate_media(reduced_motion='no-preference')
    hold()
    page.evaluate('''()=>{const s=document.querySelector('.go-surface').__vueParentComponent.setupState;
      s.game.board[40]=-1;for(const n of [31,39,41])s.game.board[n]=1;
      s.game.positions=[s.game.board.join(',')];
    }''')
    page.locator('.board-cell').nth(49).click()
    page.get_by_role('button',name='确认落子',exact=True).click()
    expect(page.locator('.go-captured')).to_have_count(1)
    assert page.evaluate('held.length===2 && held.every(a=>a.effect.getTiming().duration===180)')
    page.locator('.board-cell').nth(50).dispatch_event('click')
    expect(page.locator('.is-preview')).to_have_count(0)
    page.get_by_role('button',name='悔棋',exact=True).click()
    ready()
    expect(page.locator('.go-captured')).to_have_count(0)
    expect(page.locator('.board-cell').nth(40)).to_have_attribute('aria-label','第 5 行第 5 列：白棋')
    expect(page.locator('.game-stats strong').nth(1)).to_have_text('0 / 0')
    page.locator('.board-cell').nth(49).click()
    page.get_by_role('button',name='确认落子',exact=True).click()
    page.emulate_media(reduced_motion='reduce')
    ready()
    expect(page.locator('.go-captured')).to_have_count(0)
    expect(page.locator('.game-stats strong').nth(1)).to_contain_text('1 /')
    page.get_by_role('button',name='重新开始',exact=True).click()
    page.evaluate('''()=>{const s=document.querySelector('.go-surface').__vueParentComponent.setupState;
      s.game.board[40]=1;s.game.board[41]=1;s.game.board[0]=-1;
      s.game.positions=[s.game.board.join(',')];
    }''')
    page.get_by_role('button',name='停一手',exact=True).click()
    expect(page.locator('.go-scoring')).to_be_visible(timeout=12000)
    page.locator('.board-cell').nth(40).click()
    expect(page.locator('.is-dead')).to_have_count(2)
    page.locator('.board-cell').nth(41).click()
    expect(page.locator('.is-dead')).to_have_count(0)
    page.locator('.board-cell').nth(40).click()
    page.get_by_role('button',name='网页全屏',exact=True).click()
    for width,height in [(320,740),(844,390)]:
        page.set_viewport_size({'width':width,'height':height})
        page.wait_for_function('''()=>{const r=document.querySelector('.game-surface').getBoundingClientRect();return r.left>=-.5&&r.right<=innerWidth+.5&&r.bottom<=innerHeight+.5}''')
        page.screenshot(path=str(out/f'game-go-scoring-{width}.png'))
    page.get_by_role('button',name='确认数子',exact=True).click()
    expect(page.locator('.game-result')).to_contain_text('白棋胜 87.5 点')
    page.get_by_role('button',name='悔棋',exact=True).click()
    expect(page.locator('.game-result')).to_have_count(0)
    expect(page.locator('.is-dead')).to_have_count(0)

    # Stale worker messages, restart, error and retry, and navigation teardown.
    page.set_viewport_size({'width':1440,'height':1000})
    for kind in ['chess','go']:
        visit(kind)
        page.evaluate('''()=>{window.RealWorker=Worker;window.requests=[];window.Worker=class {
          postMessage(data){this.data=data;requests.push(this)} terminate(){this.stopped=true}
        }}''')
        page.get_by_role('button',name='机器先手',exact=True).click()
        expect(page.locator('.strategy-surface')).to_have_attribute('aria-busy','true')
        page.get_by_role('button',name='重新开始',exact=True).click()
        assert page.evaluate('requests[0].stopped')
        page.evaluate('requests[0].onmessage({data:null});requests[0].onmessageerror()')
        expect(page.locator('.strategy-error')).to_have_count(0)
        page.evaluate('requests[1].onerror({preventDefault(){}})')
        expect(page.locator('.strategy-error')).to_be_visible()
        page.evaluate('()=>{window.Worker=RealWorker}')
        page.get_by_role('button',name='重试电脑落子',exact=True).click()
        ready()
        page.evaluate('''()=>{window.Worker=class{postMessage(data){this.data=data;requests.push(this)}terminate(){this.stopped=true}}}''')
        page.get_by_role('button',name='重新开始',exact=True).click()
        page.locator('.header a[href="/game"]').first.click()
        expect(page.locator('.game-card')).to_have_count(13)
        assert page.evaluate('requests.at(-1).stopped')
    browser.close()
    assert not errors,errors
print('Chess / Go motion passed: scaled castling, input lock, undo/restart, reduced motion, four promotions/focus, capture decoration, dead-group scoring, stale worker/error/retry/navigation.')
