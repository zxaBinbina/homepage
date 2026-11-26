import os
base = os.environ.get("HOMEPAGE_TEST_URL", "http://127.0.0.1:5173").rstrip("/")
from playwright.sync_api import sync_playwright,expect

project_count = 13
github_projects = {
 'myriad': 'myriad',
 'myriad-api': 'myriad_api',
 'browser-api': 'homepage-browser-api',
}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
 page=b.new_page(reduced_motion='reduce'); errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 for route in ['/', '/project']:
  page.goto(base+route)
  nav=page.get_by_role('navigation',name='主导航',exact=True)
  expect(nav.get_by_role('link',name='项目',exact=True)).to_have_attribute('href','/project')
  expect(nav.get_by_role('link',name='首页',exact=True)).to_have_attribute('href','/')
  # UI-FIX P0-4 · 同名入口统一指向站内介绍区块，官网入口留在该区块内。
  expect(nav.get_by_role('link',name='悠哉世界',exact=True)).to_have_attribute('href','/#world')
  expect(nav.get_by_role('link',name='关于',exact=True)).to_have_count(0)
  expect(nav.locator('[aria-current="page"]')).to_have_text('首页' if route=='/' else '项目')
  expect(nav.get_by_role('link',name='工具',exact=True)).to_have_attribute('href','/tool')
  expect(nav.get_by_role('link',name='游戏',exact=True)).to_have_attribute('href','/game')
  assert nav.get_by_role('link').count()==7
  assert page.get_by_role('button',name='打开网易云音乐播放器').count()==1
  page.set_viewport_size(dict(width=390,height=844))
  page.get_by_role('button',name='打开菜单').click()
  mobile=page.get_by_role('navigation',name='移动导航',exact=True)
  expect(mobile.get_by_role('link',name='首页',exact=True)).to_have_attribute('href','/')
  expect(mobile.get_by_role('link',name='悠哉世界',exact=True)).to_have_attribute('href','/#world')
  expect(mobile.get_by_role('link',name='关于',exact=True)).to_have_count(1)
  page.keyboard.press('Escape');expect(page.locator('#mobile-nav')).to_have_count(0)
  page.set_viewport_size(dict(width=1440,height=1000))
 page.goto(base+'/project')
 page.set_viewport_size(dict(width=390,height=844))
 page.get_by_role('button',name='打开菜单').click()
 expect(page.locator('#mobile-nav a[href="/project"]')).to_be_visible()
 page.keyboard.press('Escape');expect(page.locator('#mobile-nav')).to_have_count(0)
 page.set_viewport_size(dict(width=1440,height=1000))
 for route in ['/project','/project/']:
  page.goto(base+route)
  expect(page).to_have_title('项目目录 · a彬彬a')
  expect(page.locator('.project-card')).to_have_count(project_count)
 expect(page.get_by_role('status')).to_have_text(f'全部 {project_count} 个项目')
 for card_id, repo in github_projects.items():
  card = page.locator(f'.project-{card_id}')
  expect(card).to_have_attribute('href', f'https://github.com/zxaBinbina/{repo}')
  expect(card).to_have_attribute('target', '_blank')
  expect(card.locator('.project-logo-art')).to_be_visible()
 sptl = page.locator('.project-sptl')
 expect(sptl).to_have_attribute('href', '/projects/SPTL')
 expect(sptl.locator('.project-logo-art img')).to_have_attribute('src', '/images/sptl.png')
 for term, count in [
  ('zxaBinbina', 6), ('Youzai-World-Team', 7), ('SPTL', 1),
  ('SplayerPlasmaTaskbarLyrics', 1), ('YouzaiWorldWebNew', 1),
  ('YouzaiWorldDonaimEmailWorker', 1), ('myriad', 2), ('myriad_api', 1),
  ('homepage-browser-api', 1), ('homepage', 1), ('.github', 0), ('自我介绍', 0),
 ]:
  page.get_by_role('searchbox',name='搜索项目').fill(term)
  expect(page.locator('.project-card')).to_have_count(count)
 page.get_by_role('searchbox',name='搜索项目').fill('webAuthn')
 expect(page.locator('.project-card')).to_have_count(1)
 assert 'RDP Access Auth' in page.locator('.project-card').inner_text()
 page.get_by_role('searchbox').fill('not-a-project');expect(page.locator('.directory-empty')).to_be_visible()
 page.get_by_role('button',name='查看全部项目').click();expect(page.locator('.project-card')).to_have_count(project_count)
 for palette in ['fufu-blue','hutao-red']:
  for theme in ['dark','light']:
   page.evaluate('([palette, theme]) => { localStorage.setItem("homepage-palette", palette); localStorage.setItem("homepage-theme", theme); }', [palette, theme])
   page.reload()
   expect(page.locator('html')).to_have_attribute('data-theme', theme)
   expect(page.locator('html')).to_have_attribute('data-palette', palette)
   expect(page.locator('.project-card')).to_have_count(project_count)
   page.locator('.project-card img').evaluate_all('images => images.forEach(image => { image.loading = "eager" })')
   page.wait_for_function('[...document.querySelectorAll(".project-card img")].every(image => image.complete && image.naturalWidth > 0)')
   for w in [320,390,481,760,1024,1440]:
    page.set_viewport_size(dict(width=w,height=1000))
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(palette,theme,w)
    columns = page.locator('.directory-project-grid').evaluate('grid => getComputedStyle(grid).gridTemplateColumns.split(" ").length')
    assert columns == (1 if w <= 480 else 2), (palette,theme,w,columns)
    for card_id in ['sptl', *github_projects]:
     card = page.locator(f'.project-{card_id}')
     art = card.locator('.project-logo-art').bounding_box()
     title = card.locator('h2').bounding_box()
     assert art['y'] + art['height'] < title['y'], (palette,theme,w,card_id)
    if palette == 'fufu-blue' and w in [390,1440]:
     page.screenshot(path=f'artifacts/project-directory-{theme}-{w}.png',full_page=True)
 page.goto(base+'/')
 featured = page.locator('#projects .project-card')
 expect(featured).to_have_count(6)
 expect(featured.nth(4)).to_have_attribute('href', 'https://github.com/zxaBinbina/myriad')
 expect(featured.nth(5)).to_have_attribute('href', '/projects/SPTL')
 featured.nth(5).click()
 expect(page).to_have_url(f'{base}/projects/SPTL')
 page.go_back()
 page.get_by_role('link',name='查看全部项目').click()
 expect(page).to_have_title('项目目录 · a彬彬a')
 assert not errors,errors
 # Capture actual card animations, including cards mounted again after searching.
 motion_page=b.new_page(viewport=dict(width=1440,height=1000))
 motion_page.on('pageerror',lambda e:errors.append(str(e)))
 motion_page.add_init_script("""
 window.cardReveals = [];
 window.cardFlashes = [];
 const previousOpacity = new WeakMap();
 function sampleCards() {
   document.querySelectorAll('.directory-project-grid .project-card').forEach(card => {
     const opacity = Number(getComputedStyle(card).opacity);
     const previous = previousOpacity.get(card);
     if (previous !== undefined && opacity < previous - 0.03)
       window.cardFlashes.push({ previous, opacity });
     previousOpacity.set(card, opacity);
   });
   requestAnimationFrame(sampleCards);
 }
 requestAnimationFrame(sampleCards);
 // Expose the gap between first paint and observer delivery deterministically.
 const Observer = window.IntersectionObserver;
 window.IntersectionObserver = class extends Observer {
   constructor(callback, options) {
     super((entries, observer) => setTimeout(() => callback(entries, observer), 120), options);
   }
 };
 const animate = Element.prototype.animate;
 Element.prototype.animate = function(frames, options) {
   if (this.matches('.project-card')) window.cardReveals.push({
     title: this.querySelector('h2').textContent, frames, options
   });
   return animate.call(this, frames, options);
 };
 """)
 for width in [1440,390]:
  motion_page.set_viewport_size(dict(width=width,height=1000))
  motion_page.goto(base+'/project')
  motion_page.wait_for_function('window.cardReveals.length > 0')
  motion_page.wait_for_timeout(1000)
  assert motion_page.evaluate('window.cardFlashes')==[], 'Cards flashed after first paint'
  for card in motion_page.locator('.project-card').all():
   card.scroll_into_view_if_needed()
   expect(card).to_have_css('opacity','1')
  motion_page.wait_for_function(f'window.cardReveals.length === {project_count}')
  records=motion_page.evaluate('window.cardReveals')
  assert all(r['options']['duration']==650 and r['frames'][0]['translate']=='0 20px' for r in records)
  assert [r['options']['delay'] for r in records]==[i % 2 * 90 if width==1440 else 0 for i in range(project_count)]
  motion_page.evaluate('window.scrollTo({top:0,behavior:"instant"})')
  motion_page.wait_for_timeout(800)
  assert motion_page.evaluate('window.cardReveals.length')==project_count
  motion_page.get_by_role('searchbox').fill('not-a-project')
  expect(motion_page.locator('.project-card')).to_have_count(0)
  motion_page.get_by_role('button',name='查看全部项目').click()
  motion_page.wait_for_function(f'window.cardReveals.length > {project_count}')
  motion_page.wait_for_timeout(1000)
  assert motion_page.evaluate('window.cardFlashes')==[], 'Cards flashed after scrolling or search'
  motion_page.emulate_media(reduced_motion='reduce')
  motion_page.wait_for_function("[...document.querySelectorAll('.project-card')].every(e => e.getAnimations().length === 0)")
  motion_page.reload()
  for card in motion_page.locator('.project-card').all():
   card.scroll_into_view_if_needed()
   assert card.evaluate('e => getComputedStyle(e).opacity')=='1'
  assert motion_page.evaluate('window.cardReveals.length')==0
  motion_page.emulate_media(reduced_motion='no-preference')
 assert not errors,errors
 b.close()
print(f'Directory routes, title, {project_count} projects and six featured projects, search/empty/reset, card links and images, four themes, six widths, scroll/search reveals and reduced motion passed')
