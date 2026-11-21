"""Challenge UI: concealment, shared marks, computer beliefs, undo and nested fullscreen dialogs."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from browser_theme import set_theme_mode

base=os.environ.get('HOMEPAGE_TEST_URL','http://127.0.0.1:4173').rstrip('/')
out=Path('artifacts/junqi-challenge');out.mkdir(parents=True,exist_ok=True)
expect.set_options(timeout=10000)

def start_page(context):
 page=context.new_page();page.set_default_timeout(10000)
 page.goto(base+'/games/junqi',wait_until='networkidle')
 expect(page.get_by_role('radio',name='练习 · 明棋',exact=True)).to_have_attribute('aria-checked','true')
 page.get_by_role('radio',name='挑战 · 暗棋',exact=True).click()
 expect(page.locator('.junqi-piece.is-hidden')).to_have_count(25)
 return page

def mark(page,at,rank):
 page.get_by_role('button',name='标记与推测',exact=True).click()
 page.locator(f'[data-at="{at}"]').click()
 expect(page.locator('.junqi-note-dialog')).to_be_visible()
 expect(page.locator('#junqi-note-title')).to_have_text('对方未知棋子')
 page.get_by_label('你认为这枚棋子是').select_option(str(rank))
 expect(page.locator('.junqi-mark-shared')).to_contain_text('已同步给电脑')
 page.get_by_role('button',name='完成',exact=True).click()
 page.get_by_role('button',name='标记与推测',exact=True).click()

def assert_hidden(page):
 assert page.locator('.junqi-piece.is-hidden').evaluate_all('''els=>els.every(el=>{
   const card=el.closest('.junqi-cell');return el.querySelector('small').textContent==='标记'
    || (el.querySelector('b').textContent==='？' && card.getAttribute('aria-label').includes('未知棋子'))
 })'''),'Unknown pieces cannot expose their real rank in faces or accessible labels'

with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER','/usr/bin/google-chrome'),args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':1440,'height':1100},reduced_motion='reduce')
 context.add_init_script('Math.random=()=>0')
 errors=[];context.on('page',lambda page:page.on('pageerror',lambda e:errors.append(str(e))))
 page=start_page(context)
 assert_hidden(page)
 # The seeded computer will move piece 38 from 15 to 21; the guess is deliberately not its real rank.
 mark(page,15,1)
 tracked=page.locator('[data-at="15"] .junqi-piece').get_attribute('data-piece-id')
 assert tracked=='38'
 mark(page,25,7)
 victim=page.locator('[data-at="25"] .junqi-piece').get_attribute('data-piece-id')
 page.get_by_role('button',name='开始对局',exact=True).click()
 page.locator('[data-at="30"]').click()
 expect(page.locator('.junqi-computer-belief')).to_contain_text('尚未确定')
 page.get_by_role('button',name='查看候选军衔',exact=True).click()
 expect(page.locator('.junqi-guess-detail')).to_contain_text('可能有误')
 expect(page.locator('.junqi-candidate-list span')).not_to_have_count(0)
 page.keyboard.press('Escape')
 expect(page.locator('.junqi-note-dialog')).not_to_be_visible()
 page.locator('[data-at="25"]').click()
 expect(page.locator('.junqi-surface')).to_have_attribute('aria-busy','false')
 expect(page.locator(f'[data-piece-id="{victim}"]')).to_have_count(0)
 tracked_card=page.locator(f'[data-piece-id="{tracked}"]')
 assert tracked_card.evaluate('el=>el.closest(".junqi-cell").dataset.at')=='21'
 expect(tracked_card.locator('b')).to_have_text('工兵')
 expect(tracked_card.locator('small')).to_have_text('标记')
 expect(page.locator('.junqi-recent')).to_contain_text('未知棋子')
 assert '团长' not in page.locator('.junqi-recent').inner_text(),'Move records cannot disclose the computer mover'
 assert_hidden(page)
 page.get_by_role('button',name='悔棋',exact=True).click()
 assert page.locator(f'[data-piece-id="{tracked}"]').evaluate('el=>el.closest(".junqi-cell").dataset.at')=='15'
 expect(page.locator(f'[data-piece-id="{victim}"] b')).to_have_text('师长')
 expect(page.locator('.junqi-piece.is-hidden')).to_have_count(25)
 # Clear a shared note; this immediately removes the visible guess too.
 page.get_by_role('button',name='标记与推测',exact=True).click()
 page.locator('[data-at="15"]').click()
 page.get_by_role('button',name='清除标记',exact=True).click()
 expect(page.locator('.junqi-mark-shared')).to_have_text('当前没有标记')
 page.get_by_role('button',name='完成',exact=True).click()
 expect(page.locator('[data-at="15"] b')).to_have_text('？')
 page.get_by_role('button',name='标记与推测',exact=True).click()
 page.get_by_role('button',name='重新开始',exact=True).click()
 expect(page.get_by_role('radio',name='挑战 · 暗棋',exact=True)).to_have_attribute('aria-checked','true')
 expect(page.locator('.junqi-piece.is-hidden')).to_have_count(25)
 assert all(text=='？' for text in page.locator('.junqi-piece.is-hidden b').all_text_contents())
 page.get_by_role('radio',name='练习 · 明棋',exact=True).click()
 expect(page.locator('.junqi-piece.is-hidden')).to_have_count(0)
 expect(page.get_by_role('button',name='标记与推测',exact=True)).to_have_count(0)
 page.get_by_role('radio',name='练习 · 明棋',exact=True).focus();page.keyboard.press('ArrowRight')
 expect(page.get_by_role('radio',name='挑战 · 暗棋',exact=True)).to_have_attribute('aria-checked','true')
 assert not errors,errors
 context.close()
 print('Concealment, shared notes, following a moved piece, removed/restored notes, beliefs, whole-turn undo, mode keyboard and restart passed',flush=True)

 for palette in ['fufu-blue','hutao-red']:
  for theme in ['dark','light']:
   context=browser.new_context(viewport={'width':1440,'height':1100},reduced_motion='reduce')
   context.add_init_script(f"Math.random=()=>0;try {{localStorage.setItem('homepage-theme','{theme}');localStorage.setItem('homepage-palette','{palette}')}} catch {{}}")
   page=start_page(context)
   for width in [1440,390,320]:
    page.set_viewport_size({'width':width,'height':1000});page.wait_for_timeout(60)
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert_hidden(page)
    page.locator('[data-at="0"]').click()
    expect(page.locator('.junqi-note-dialog')).to_be_visible()
    box=page.locator('.junqi-note-dialog').bounding_box()
    assert box['x']>=0 and box['x']+box['width']<=width+1
    page.locator('.junqi-note-dialog').screenshot(path=str(out/f'mark-{palette}-{theme}-{width}.png'))
    page.get_by_role('button',name='完成',exact=True).click()
   page.locator('.junqi-surface').screenshot(path=str(out/f'board-{palette}-{theme}.png'))
   # The note dialog uses the top layer above the existing fullscreen dialog.
   page.get_by_role('button',name='网页全屏',exact=True).click()
   page.set_viewport_size({'width':844,'height':390})
   expect(page.locator('.junqi-board')).to_have_class('junqi-board is-horizontal')
   page.wait_for_timeout(100)
   page.locator('[data-at="0"]').click()
   expect(page.locator('dialog[open]')).to_have_count(2)
   page.get_by_label('你认为这枚棋子是').select_option('11')
   page.keyboard.press('Escape')
   expect(page.locator('dialog[open]')).to_have_count(1)
   assert page.locator('[data-at="0"]').evaluate('el=>el===document.activeElement')
   page.get_by_role('button',name='标记与推测',exact=True).click()
   page.locator('[data-at="30"]').click()
   expect(page.locator('.junqi-guess-detail')).to_be_visible()
   page.locator('.junqi-note-dialog').screenshot(path=str(out/f'belief-fullscreen-{palette}-{theme}.png'))
   page.get_by_role('button',name='完成',exact=True).click()
   page.get_by_role('button',name='退出全屏',exact=True).click()
   context.close()
 print('Four themes, desktop/320px layouts, marking dialogs and nested fullscreen belief dialogs passed',flush=True)

 context=browser.new_context(viewport={'width':390,'height':900},has_touch=True,is_mobile=True,reduced_motion='reduce')
 context.add_init_script('Math.random=()=>0')
 page=start_page(context)
 page.locator('[data-at="0"]').tap()
 expect(page.locator('.junqi-note-dialog')).to_be_visible()
 page.get_by_label('你认为这枚棋子是').select_option('9')
 page.get_by_role('button',name='完成',exact=True).tap()
 expect(page.locator('[data-at="0"] b')).to_have_text('司令')
 context.close()
 print('Touch marking passed',flush=True)

 context=browser.new_context(viewport={'width':1440,'height':1100},reduced_motion='no-preference')
 context.add_init_script('Math.random=()=>0')
 page=start_page(context)
 page.get_by_role('button',name='开始对局',exact=True).click()
 page.evaluate('''()=>{const animate=Element.prototype.animate;Element.prototype.animate=function(...args){
  const a=animate.apply(this,args);if(this.classList.contains('junqi-flight')&&this.classList.contains('is-hidden'))a.pause();return a}}''')
 page.locator('[data-at="30"]').click();page.locator('[data-at="25"]').click()
 expect(page.locator('.junqi-flight.is-hidden')).to_have_count(1)
 expect(page.locator('.junqi-flight.is-hidden b')).to_have_text('？')
 expect(page.locator('.junqi-flight.is-hidden small')).to_have_text('未知')
 page.get_by_role('button',name='悔棋',exact=True).click()
 expect(page.locator('.junqi-flight')).to_have_count(0)
 expect(page.locator('.junqi-piece.is-hidden')).to_have_count(25)
 page.get_by_role('button',name='开始对局',exact=True).count()
 page.locator('[data-at="30"]').click();page.locator('[data-at="25"]').click()
 page.get_by_role('radio',name='练习 · 明棋',exact=True).click()
 page.wait_for_timeout(650)
 expect(page.get_by_role('button',name='开始对局',exact=True)).to_be_enabled()
 expect(page.locator('.junqi-piece.is-hidden')).to_have_count(0)
 page.get_by_role('radio',name='挑战 · 暗棋',exact=True).click()
 page.get_by_role('button',name='开始对局',exact=True).click()
 page.locator('[data-at="30"]').click();page.locator('[data-at="25"]').click()
 page.get_by_role('link',name='全部游戏',exact=True).click()
 expect(page.locator('.junqi-note-dialog')).to_have_count(0)
 expect(page.locator('.junqi-board')).to_have_count(0)
 context.close();browser.close()
 print('Enemy flight masking, canceled animations, mode changes and unmount cleanup passed',flush=True)
