"""Development fixtures for computer-first turns and three-card draws."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:5173').rstrip('/')
out = Path('artifacts')
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    page = browser.new_page(viewport={'width':1440, 'height':1000}, reduced_motion='no-preference')
    page.add_init_script('Math.random = () => 0')
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))

    def card_idle():
        expect(page.locator('.solitaire-surface')).to_have_attribute('aria-busy', 'false')

    page.goto(base + '/games/solitaire', wait_until='networkidle')
    page.get_by_label('纸牌难度').select_option('3')
    page.evaluate('''() => {
      const animate=Element.prototype.animate;
      Element.prototype.animate=function(...args) {
        const a=animate.apply(this,args);
        if (this.closest('.waste-stack')) a.pause();
        return a;
      };
    }''')
    stock = page.locator('.stock-card').bounding_box()
    page.locator('.stock-card').click()
    expect(page.locator('.waste-stack .is-card-moving')).to_have_count(3)
    timings = page.locator('.waste-stack .is-card-moving').evaluate_all('els => els.map(el => el.getAnimations()[0].effect.getTiming())')
    assert [t['delay'] for t in timings] == [0, 50, 100]
    assert all(t['duration'] == 340 for t in timings)
    starts = page.locator('.waste-stack .is-card-moving').evaluate_all('els => els.map(el => el.getBoundingClientRect().toJSON())')
    assert all(abs(b[key]-stock[key])<1 for b in starts for key in ['x','y','width','height'])
    expect(page.locator('.stock-card')).to_be_disabled()
    page.get_by_label('纸牌难度').select_option('1')
    card_idle()
    expect(page.locator('.waste-stack .playing-card')).to_have_count(0)
    expect(page.locator('.pile-label').first).to_have_text('牌堆 · 24')
    page.get_by_label('纸牌难度').select_option('3')
    page.locator('.stock-card').click()
    expect(page.locator('.waste-stack .is-card-moving')).to_have_count(3)
    page.emulate_media(reduced_motion='reduce')
    card_idle()
    expect(page.locator('.pile-label').first).to_have_text('牌堆 · 21')
    page.get_by_role('button', name='撤销', exact=True).click()
    card_idle()
    expect(page.locator('.waste-stack .playing-card')).to_have_count(0)
    for remaining in [1, 2]:
        page.get_by_role('button', name='重新开始', exact=True).click()
        page.evaluate('''n => {
          const s=document.querySelector('.solitaire-surface').__vueParentComponent.setupState;
          s.game={...s.game,stock:s.game.stock.slice(0,n),waste:s.game.stock.slice(n).map(c=>({...c,faceUp:true}))};
        }''', remaining)
        page.locator('.stock-card').click()
        card_idle()
        expect(page.locator('.pile-label').first).to_have_text('牌堆 · 0')
        expect(page.locator('.waste-stack .playing-card')).to_have_count(24)
        page.get_by_role('button', name='撤销', exact=True).click()
        card_idle()
        expect(page.locator('.pile-label').first).to_have_text(f'牌堆 · {remaining}')
    page.get_by_role('button', name='重新开始', exact=True).click()
    page.locator('.stock-card').click()
    card_idle()
    for theme in ['dark', 'light']:
        page.evaluate('t=>document.documentElement.dataset.theme=t', theme)
        for width in [320,390,768,1024,1440]:
            page.set_viewport_size({'width':width,'height':1000})
            page.locator('.waste-stack').scroll_into_view_if_needed()
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            assert page.locator('.waste-stack').evaluate('''el => {
              const cards=[...el.querySelectorAll('.playing-card')].map(c=>c.getBoundingClientRect());
              const foundation=document.querySelector('.foundation-card').getBoundingClientRect();
              return cards[0].x<cards[1].x && cards[1].x<cards[2].x && cards[2].right<foundation.left
                && cards.every(c=>Math.abs(c.height-c.width*1.4)<.1);
            }''')
            if width in [390,1440]:
                page.locator('.game-surface').screenshot(path=str(out / f'game-options-three-{theme}-{width}.png'))
    page.set_viewport_size({'width':390,'height':844})
    page.get_by_role('button', name='网页全屏', exact=True).click()
    page.evaluate('''() => {
      const s=document.querySelector('.solitaire-surface').__vueParentComponent.setupState;
      s.game={stock:[0,1,2].map(suit=>({suit,rank:1,faceUp:false})),waste:[],foundations:[[],[],[],[]],tableau:[[],[],[],[],[],[],[]],moves:0};
      s.history=[];
    }''')
    page.locator('.stock-card').click()
    card_idle()
    source = page.locator('.waste-stack button')
    a, b = source.bounding_box(), page.locator('.foundation-card').first.bounding_box()
    page.mouse.move(a['x']+a['width']/2, a['y']+12)
    page.mouse.down()
    page.mouse.move(b['x']+b['width']/2, b['y']+b['height']/2, steps=8)
    expect(page.locator('.solitaire-drag-layer')).to_have_count(1)
    page.mouse.up()
    card_idle()
    expect(page.locator('.game-stats strong').first).to_have_text('1 / 52')
    expect(page.locator('.waste-stack button')).to_have_attribute('data-card-id', '1-1')
    page.get_by_role('button', name='撤销', exact=True).click()
    card_idle()
    expect(page.locator('.waste-stack button')).to_have_attribute('data-card-id', '0-1')
    page.screenshot(path=str(out / 'game-options-three-fullscreen.png'))
    print('Three-card draw: staggered origins, input lock, cancellation, short stock, undo, theme/width matrix and scaled drag passed.', flush=True)

    page.set_viewport_size({'width':1440,'height':1000})
    for game in ['xiangqi', 'gomoku']:
        page.goto(base + '/games/' + game, wait_until='networkidle')
        page.evaluate('''() => {
          window.RealWorker=Worker; window.requests=[];
          window.Worker=class {
            postMessage(data) { this.data=data; requests.push(this); }
            terminate() { this.stopped=true; }
          };
        }''')
        button = page.get_by_role('button', name='机器先手', exact=True)
        button.click()
        expect(page.locator('.strategy-surface')).to_have_attribute('aria-busy', 'true')
        assert page.evaluate('requests[0].data.side') == 1
        cell = page.locator('.board-cell').nth(0)
        cell.scroll_into_view_if_needed()
        box = cell.bounding_box()
        page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
        expect(page.locator('.strategy-cell.is-selected')).to_have_count(0)
        button.click()
        assert page.evaluate('requests[0].stopped')
        button.click()
        page.get_by_role('button', name='重新开始', exact=True).click()
        assert page.evaluate('requests[1].stopped && requests[2].data.side===1')
        page.evaluate('''() => {
          requests[0].onmessage({data:112}); requests[1].onmessageerror();
        }''')
        expect(page.locator('.strategy-error')).to_have_count(0)
        expect(page.locator('.strategy-surface')).to_have_attribute('aria-busy', 'true')
        page.evaluate('requests[2].onerror({preventDefault(){}})')
        expect(page.locator('.strategy-error')).to_be_visible()
        page.evaluate('() => { window.Worker=RealWorker; }')
        page.get_by_role('button', name='重试电脑落子').click()
        expect(page.locator('.strategy-surface')).to_have_attribute('aria-busy', 'false')
        expect(page.locator('.game-stats strong').nth(1)).to_have_text('0')
        for theme in ['dark', 'light']:
            page.evaluate('t=>document.documentElement.dataset.theme=t', theme)
            for width in [320,390,768,1024,1440]:
                page.set_viewport_size({'width':width,'height':1000})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), (game,theme,width)
                if width in [390,1440]:
                    page.locator('.game-surface').screenshot(path=str(out / f'game-options-first-{game}-{theme}-{width}.png'))
        page.set_viewport_size({'width':320,'height':568})
        page.get_by_role('button', name='网页全屏', exact=True).click()
        page.wait_for_function('''() => {
          const r=document.querySelector('.game-surface').getBoundingClientRect();
          return r.x>=-1 && r.y>=-1 && r.right<=innerWidth+1 && r.bottom<=innerHeight+1;
        }''')
        expect(button).to_have_attribute('aria-pressed', 'true')
        page.screenshot(path=str(out / f'game-options-first-{game}-fullscreen.png'))
        page.keyboard.press('Escape')
        page.set_viewport_size({'width':1440,'height':1000})
        for win in [True, False]:
            page.evaluate('''([kind,win]) => {
              const s=document.querySelector('.strategy-surface').__vueParentComponent.setupState;
              s.cancelTurn();
              if (kind==='xiangqi') {
                s.board[win?85:4]=0;
              } else {
                s.board=Array(225).fill(0);
                for (let i=90;i<95;i++) s.board[i]=win?-1:1;
                s.last={from:-1,to:94};
              }
            }''', [game, win])
            expect(page.locator('.strategy-result')).to_contain_text('你赢了' if win else '电脑赢了')
            if win:
                page.get_by_role('button', name='重新开始', exact=True).click()
                expect(page.locator('.strategy-surface')).to_have_attribute('aria-busy', 'false')
        print(f'{game}: computer opening, cancellation, stale messages, retry and player-relative results passed.', flush=True)
    assert not errors, errors
    browser.close()
