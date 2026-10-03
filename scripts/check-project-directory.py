import os
base = os.environ.get("HOMEPAGE_TEST_URL", "http://127.0.0.1:5173").rstrip("/")
from playwright.sync_api import sync_playwright,expect
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
 page=b.new_page(reduced_motion='reduce'); errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 for route in ['/', '/project']:
  page.goto(base+route)
  nav=page.get_by_role('navigation',name='主导航',exact=True)
  expect(nav.get_by_role('link',name='项目',exact=True)).to_have_attribute('href','/project')
  expect(nav.get_by_role('link',name='首页',exact=True)).to_have_attribute('href','/')
  expect(nav.get_by_role('link',name='悠哉世界',exact=True)).to_have_attribute('href','https://mcyzw.top')
  expect(nav.get_by_role('link',name='关于',exact=True)).to_have_count(0)
  expect(nav.locator('[aria-current="page"]')).to_have_text('首页' if route=='/' else '项目')
  assert nav.get_by_role('link').count()==3
  assert page.get_by_role('button',name='打开网易云音乐播放器').count()==1
  page.set_viewport_size(dict(width=390,height=844))
  page.get_by_role('button',name='打开菜单').click()
  mobile=page.get_by_role('navigation',name='移动导航',exact=True)
  expect(mobile.get_by_role('link',name='首页',exact=True)).to_have_attribute('href','/')
  expect(mobile.get_by_role('link',name='悠哉世界',exact=True)).to_have_attribute('href','https://mcyzw.top')
  expect(mobile.get_by_role('link',name='关于',exact=True)).to_have_count(0)
  page.keyboard.press('Escape');expect(page.locator('#mobile-nav')).to_have_count(0)
  page.set_viewport_size(dict(width=1440,height=1000))
 page.goto(base+'/project')
 page.set_viewport_size(dict(width=390,height=844))
 page.get_by_role('button',name='打开菜单').click()
 expect(page.locator('#mobile-nav a[href="/project"]')).to_be_visible()
 page.keyboard.press('Escape');expect(page.locator('#mobile-nav')).to_have_count(0)
 page.set_viewport_size(dict(width=1440,height=1000))
 for route in ['/project','/project']:
  page.goto(base+route)
  expect(page).to_have_title('项目目录 · a彬彬a')
  expect(page.locator('.project-card')).to_have_count(4)
 page.get_by_role('searchbox',name='搜索项目').fill('webAuthn')
 expect(page.locator('.project-card')).to_have_count(1)
 assert 'RDP Access Auth' in page.locator('.project-card').inner_text()
 page.get_by_role('searchbox').fill('not-a-project');expect(page.locator('.directory-empty')).to_be_visible()
 page.get_by_role('button',name='查看全部项目').click();expect(page.locator('.project-card')).to_have_count(4)
 for theme in ['dark','light']:
  page.evaluate('(v)=>localStorage.setItem("homepage-theme",v)',theme);page.reload()
  for w in [320,390,768,1024,1440]:
   page.set_viewport_size(dict(width=w,height=1000))
   page.locator('.project-card').last.scroll_into_view_if_needed()
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(theme,w)
   assert page.locator('.project-card img').evaluate_all('(els)=>els.every(e=>e.complete && e.naturalWidth>0)')
   if w in [390,1440]:
    page.evaluate('window.scrollTo({top:0,behavior:"instant"})')
    page.screenshot(path=f'artifacts/project-directory-{theme}-{w}.png',full_page=True)
 page.goto(base+'/');page.get_by_role('link',name='查看全部项目').click();expect(page).to_have_title('项目目录 · a彬彬a')
 assert not errors,errors
 b.close()
print('Directory routes, title, four projects, search/empty/reset, images, both themes and five widths passed')
