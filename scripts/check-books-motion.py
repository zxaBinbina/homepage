"""Reader fullscreen ownership, control discovery, motion and nested table of contents."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
base=os.environ.get('HOMEPAGE_TEST_URL','http://127.0.0.1:4173').rstrip('/')
out=Path('artifacts/books');out.mkdir(parents=True,exist_ok=True)
books=json.loads(Path('src/books/library.json').read_text())
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER','/usr/bin/google-chrome'),args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':1440,'height':900},reduced_motion='no-preference')
 page=context.new_page();errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 def ready():
  expect(page.locator('.reader-text-layout')).to_be_visible()
  page.wait_for_timeout(300)
 def panel_closed():expect(page.locator('.reader-panel')).not_to_be_visible()
 page.goto(base+'/tool',wait_until='networkidle')
 style_fields=['borderRadius','padding','borderTopWidth','backgroundColor']
 style=page.locator('.tool-filters').evaluate('(e,keys)=>Object.fromEntries(keys.map(k=>[k,getComputedStyle(e)[k]]))',style_fields)
 page.goto(base+'/books/hidden-professor',wait_until='networkidle');ready()
 page.get_by_role('button',name='阅读设置',exact=True).click()
 page.wait_for_timeout(260)
 for group in page.locator('.reader-settings .seg').all():
  actual=group.evaluate('(e,keys)=>Object.fromEntries(keys.map(k=>[k,getComputedStyle(e)[k]]))',style_fields)
  assert actual==style,(actual,style)
 page.screenshot(path=str(out/'settings-shared-style.png'))
 # A closing dialog stays modal during the intermediate frame, then restores focus.
 page.get_by_role('button',name='关闭阅读面板').click()
 page.wait_for_timeout(45)
 assert page.locator('dialog').evaluate('(e)=>e.open && e.getAnimations().length>0')
 panel_closed()
 expect(page.get_by_role('button',name='阅读设置',exact=True)).to_be_focused()
 # Real Fullscreen API, not just a CSS-only expanded view.
 page.get_by_role('button',name='专注阅读',exact=True).click()
 page.wait_for_function('document.fullscreenElement === document.documentElement')
 expect(page.get_by_role('button',name='退出专注',exact=True)).to_be_focused()
 page.mouse.move(300,400);page.wait_for_timeout(2200)
 assert page.locator('.reader-focus-exit').evaluate('(e)=>getComputedStyle(e).opacity')=='0'
 page.mouse.wheel(0,1000);page.wait_for_timeout(300)
 assert page.evaluate('scrollY')>500,'Fullscreen broke native scrolling'
 page.mouse.move(1390,30);page.wait_for_timeout(250)
 assert page.locator('.reader-focus-exit').evaluate('(e)=>getComputedStyle(e).opacity')=='1'
 page.screenshot(path=str(out/'focus-fullscreen.png'))
 # Browser-native exit must leave focus mode too.
 page.evaluate('document.exitFullscreen()')
 expect(page.locator('.reader-root')).not_to_have_class('reader-root is-focused')
 expect(page.get_by_role('button',name='专注阅读',exact=True)).to_be_focused()
 page.get_by_role('button',name='专注阅读',exact=True).focus();page.keyboard.press('Enter')
 page.wait_for_function('!!document.fullscreenElement')
 page.keyboard.press('Tab');page.keyboard.press('Shift+Tab')
 page.keyboard.press('Escape')
 page.wait_for_function('!document.fullscreenElement')
 # Fullscreen is released on SPA departure as well.
 page.get_by_role('button',name='专注阅读',exact=True).click()
 page.wait_for_function('!!document.fullscreenElement')
 page.locator('.reader-back').evaluate('(e)=>e.click()')
 expect(page.locator('.book-card')).to_have_count(7)
 page.wait_for_function('!document.fullscreenElement')
 expect(page.locator('.book-card h2')).not_to_contain_text(['盗墓笔记之秦王帝陵'])
 # Chapter-attached skits are collapsed, unnumbered and do not shift the next chapter.
 page.goto(base+'/books/angel-at-hogwarts?chapter=85',wait_until='networkidle');ready()
 page.get_by_role('button',name='章节目录',exact=True).click()
 expect(page.get_by_role('radiogroup',name='章节分组')).to_have_count(0)
 expect(page.locator('.reader-toc-tree > li')).to_have_count(129)
 expect(page.locator('.reader-toc').get_by_role('link',name='阅读',exact=True)).to_have_count(0)
 toggle=page.locator('.reader-toc-toggle[aria-label*="第85章 事后"]')
 expect(toggle).to_have_attribute('aria-expanded','false')
 target=page.locator('#'+toggle.get_attribute('aria-controls'))
 toggle.click()
 expect(toggle).to_have_attribute('aria-expanded','true')
 page.wait_for_timeout(70)
 height=target.bounding_box()['height'];full=target.locator('ul').bounding_box()['height']
 assert 0<height<full,(height,full)
 expect(target.locator('a')).to_be_visible()
 expect(target.locator('.reader-toc-number')).to_have_count(0)
 assert page.url.endswith('chapter=85')
 page.wait_for_timeout(350)
 target.locator('a').focus()
 toggle.evaluate('(e)=>e.click()')
 assert target.evaluate('(e)=>e.inert')
 expect(toggle).to_be_focused()
 page.wait_for_timeout(350)
 expect(target.locator('a')).not_to_be_visible()
 for _ in range(3):toggle.click();page.wait_for_timeout(40)
 expect(toggle).to_have_attribute('aria-expanded','true')
 page.wait_for_timeout(350)
 target.locator('a').click();ready()
 expect(page.locator('h1')).to_have_text('小剧场')
 expect(page.locator('.reader-parent-chapter')).to_contain_text('第85章 事后')
 page.get_by_role('button',name='下一章',exact=True).click();ready()
 expect(page.locator('h1')).to_have_text('第86章 霍格沃茨恶霸')
 page.get_by_role('button',name='章节目录',exact=True).click()
 page.locator('.reader-toc-main[href$="?chapter=85"]').click();ready()
 expect(page.locator('h1')).to_have_text('第85章 事后')
 page.get_by_role('button',name='章节目录',exact=True).click()
 page.locator('#reader-jump').fill('86')
 page.get_by_role('button',name='跳转',exact=True).click();ready()
 expect(page.locator('h1')).to_have_text('第86章 霍格沃茨恶霸')
 assert page.url.endswith('chapter=87')
 page.get_by_role('button',name='章节目录',exact=True).click()
 page.get_by_role('searchbox',name='搜索章节').fill('吃醋的格林德沃')
 expect(page.locator('.reader-toc-tree > li')).to_have_count(1)
 expect(page.locator('.reader-toc-child')).to_have_text('小剧场——吃醋的格林德沃')
 expect(page.locator('.reader-toc-toggle')).to_have_attribute('aria-expanded','true')
 page.locator('.reader-toc-child').click();ready()
 expect(page.locator('h1')).to_have_text('小剧场——吃醋的格林德沃')
 # Final bonus stories have one separate branch, in original order, outside the last chapter.
 for book_id,main_count,extra_count in [('hidden-professor',643,12),('tom-at-hogwarts',363,30),('angel-at-hogwarts',128,20)]:
  page.goto(base+'/books/'+book_id+'?chapter=1',wait_until='networkidle');ready()
  page.get_by_role('button',name='章节目录',exact=True).click()
  expect(page.locator('.reader-toc-tree > li')).to_have_count(main_count+1)
  ending=page.locator('.reader-toc-tree > li').last
  expect(ending.locator('.reader-toc-number')).to_have_count(0)
  expect(ending.locator('.reader-toc-toggle')).to_have_attribute('aria-expanded','false')
  ending.locator('.reader-toc-toggle').click()
  children=ending.locator('.reader-toc-child')
  expect(children).to_have_count(extra_count)
  book=next(b for b in books if b['id']==book_id)
  data=json.loads(Path(f'public/books/{book_id}/{book["revision"]}-index.json').read_text())
  expected=[c['name'] for c in data['chapters'] if c['appendix']]
  assert children.all_text_contents()==expected
  page.get_by_role('button',name='正序',exact=True).click()
  expect(page.locator('.reader-toc-tree > li').first.locator('.reader-toc-name')).to_contain_text('番外')
  assert page.locator('.reader-toc-tree > li').first.locator('.reader-toc-child').all_text_contents()==expected
  page.get_by_role('button',name='倒序',exact=True).click()
  children.first.click();ready()
  expect(page.locator('h1')).to_have_text(expected[0])
  page.get_by_role('button',name='下一章',exact=True).click();ready()
  expect(page.locator('h1')).to_have_text(expected[1])
 # Searching the last bonus story exposes its branch without numbering it as a chapter.
 page.goto(base+'/books/tom-at-hogwarts?chapter=1',wait_until='networkidle');ready()
 page.get_by_role('button',name='章节目录',exact=True).click()
 page.get_by_role('searchbox',name='搜索章节').fill('埃及之旅 4')
 expect(page.locator('.reader-toc-child')).to_have_count(1)
 page.locator('.reader-toc-child').click();ready()
 expect(page.locator('h1')).to_have_text('番外之埃及之旅 4')
 # Returning progress/bookmarks migrate from the old raw chapter and paragraph.
 book=next(b for b in books if b['id']=='tom-at-hogwarts')
 index=json.loads(Path(f'public/books/{book["id"]}/{book["revision"]}-index.json').read_text())
 old_revision=next(rev for rev,items in index['migrations'].items() if len(items)==363)
 saved={'version':1,'revision':old_revision,'chapter':362,'title':'第364章 大结局（二合一）','paragraph':2000,'offset':.1,'fraction':.95,'updatedAt':1}
 page.locator('.reader-back').click()
 expect(page.locator('.book-card')).to_have_count(7)
 page.evaluate('(v)=>{localStorage.setItem("homepage-reading:tom-at-hogwarts",JSON.stringify(v));localStorage.setItem("homepage-bookmarks:tom-at-hogwarts",JSON.stringify([{...v,id:"old",excerpt:"原书签"}]))}',saved)
 page.goto(base+'/books/tom-at-hogwarts',wait_until='networkidle');ready()
 expect(page.locator('h1')).to_have_text('番外之埃及之旅 4')
 assert page.evaluate('JSON.parse(localStorage.getItem("homepage-reading:tom-at-hogwarts")).paragraph')==38
 page.get_by_role('button',name='我的书签',exact=True).click()
 expect(page.locator('.reader-bookmark strong')).to_have_text('番外之埃及之旅 4')
 page.keyboard.press('Escape');panel_closed()
 # Saved progress and bookmarks from the grouped edition return to the same paragraph.
 grouped_revision=next(rev for rev,items in index['migrations'].items()
  if len(items)==395 and json.loads(Path(f'public/books/{book["id"]}/{rev}-index.json').read_text())['chapters'][363]['number']==1)
 saved={'version':1,'revision':grouped_revision,'chapter':363,'title':'番外 1 · 假如斯内普同意了邀请','paragraph':8,'offset':.2,'fraction':.1,'updatedAt':1}
 page.locator('.reader-back').click()
 expect(page.locator('.book-card')).to_have_count(7)
 page.evaluate('(v)=>{localStorage.setItem("homepage-reading:tom-at-hogwarts",JSON.stringify(v));localStorage.setItem("homepage-bookmarks:tom-at-hogwarts",JSON.stringify([{...v,id:"grouped",excerpt:"分组版书签"}]))}',saved)
 page.goto(base+'/books/tom-at-hogwarts',wait_until='networkidle');ready()
 expect(page.locator('h1')).to_have_text('番外之假如斯内普同意了邀请')
 progress=page.evaluate('JSON.parse(localStorage.getItem("homepage-reading:tom-at-hogwarts"))')
 assert progress['chapter']==267 and progress['paragraph']==8,progress
 page.get_by_role('button',name='我的书签',exact=True).click()
 expect(page.locator('.reader-bookmark strong')).to_have_text('第267章附篇 · 番外之假如斯内普同意了邀请')
 mark=page.evaluate('JSON.parse(localStorage.getItem("homepage-bookmarks:tom-at-hogwarts"))[0]')
 assert mark['chapter']==267 and mark['paragraph']==8 and mark['offset']==.2,mark
 page.keyboard.press('Escape');panel_closed()
 page.reload(wait_until='networkidle');ready()
 assert page.evaluate('JSON.parse(localStorage.getItem("homepage-reading:tom-at-hogwarts")).paragraph')==8
 # Reduced-motion dialogs open/close directly. Tooltips remain available on icon buttons.
 page.emulate_media(reduced_motion='reduce')
 page.get_by_role('button',name='阅读设置',exact=True).click()
 assert page.locator('.reader-panel').evaluate('(e)=>e.getAnimations().length')==0
 for button in page.locator('.reader-panel button[aria-label]').all():
  if button.is_visible():assert button.get_attribute('title'),button.get_attribute('aria-label')
 page.keyboard.press('Escape');panel_closed()
 # Current nested entries are expanded and centered at all target widths and themes.
 for theme in ['dark','light']:
  page.evaluate('(theme)=>localStorage.setItem("homepage-theme",theme)',theme)
  page.goto(base+'/books/tom-at-hogwarts?chapter=268',wait_until='networkidle');ready()
  for width in [320,390,768,1024,1440]:
   page.set_viewport_size({'width':width,'height':844})
   page.get_by_role('button',name='阅读工具' if width<=760 else '章节目录',exact=True).click()
   expect(page.locator('.reader-toc-tree > li')).to_have_count(364)
   expect(page.get_by_role('radiogroup',name='章节分组')).to_have_count(0)
   expect(page.locator('.reader-toc a[aria-current]')).to_contain_text('番外之假如斯内普同意了邀请')
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   box=page.locator('.reader-panel').bounding_box()
   assert box['x']>=0 and box['x']+box['width']<=width
   listbox=page.locator('.reader-toc').bounding_box()
   assert listbox['height']>180,listbox
   current=page.locator('.reader-toc a[aria-current]').bounding_box()
   assert current['y']>=listbox['y'] and current['y']+current['height']<=listbox['y']+listbox['height'],current
   if width in [320,1440]:page.screenshot(path=str(out/f'branch-directory-{theme}-{width}.png'))
   page.keyboard.press('Escape');panel_closed()
 # Rejected fullscreen requests still allow reading and an accessible exit.
 fallback=browser.new_context(viewport={'width':390,'height':844},has_touch=True,reduced_motion='reduce')
 fallback.add_init_script('Element.prototype.requestFullscreen=function(){return Promise.reject(new Error("denied"))}')
 phone=fallback.new_page();phone.goto(base+'/books/hidden-professor',wait_until='networkidle')
 expect(phone.locator('.reader-text-layout')).to_be_visible();phone.wait_for_timeout(300)
 phone.get_by_role('button',name='专注阅读',exact=True).tap()
 expect(phone.locator('.reader-notice')).to_contain_text('未能进入全屏')
 phone.wait_for_timeout(2200)
 phone.locator('.reader-paragraph').first.tap()
 expect(phone.get_by_role('button',name='退出专注',exact=True)).to_have_css('opacity','1')
 phone.get_by_role('button',name='退出专注',exact=True).tap()
 fallback.close()
 assert not errors,errors
 print('Reader improvements passed: native fullscreen/exit/cleanup/fallback, proximity and touch reveal, shared controls, modal motion/reduced motion, nested skits/final appendices, numbering/search/jumps, source-order navigation and raw/grouped progress/bookmark migration.')
 browser.close()
