"""M5 integration: real built packages, visitor isolation, routing, media and responsive UI."""
import io
import json
import os
import wave
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:4173').rstrip('/')
PREFIX = 'homepage.myriad.visitor.'
OUT = Path(__file__).resolve().parents[1] / 'artifacts'
OUT.mkdir(exist_ok=True)
checks = []
def check(ok, label):
    assert ok, label
    checks.append(label)
    print('PASS ' + label, flush=True)

MOCK = r"""(() => {
window.m5calls = [];
const original = window.fetch.bind(window);
window.fetch = async (input, init = {}) => {
  const u = new URL(typeof input === 'string' ? input : input.url || String(input), location.href);
  if (u.origin === location.origin) return original(input, init);
  window.m5calls.push({url:u.href, auth:new Headers(init.headers).get('Authorization'), credentials:init.credentials});
  if (u.pathname.includes('/me/') || u.pathname.endsWith('/me') || u.pathname.includes('/sync'))
    return Response.json({error:'private'}, {status:401});
  if (u.pathname.endsWith('/hot') || u.pathname.endsWith('/rss')) return Response.json({title:'公开信息流',fetchedAt:Date.now(),items:[
    {id:'article-1',title:'公开文章',url:'https://article.example/read',source:u.searchParams.get('source')||'RSS',description:'<img src=x onerror=window.m5xss=1>'}
  ]});
  if (u.pathname.endsWith('/reader')) return Response.json({title:'文章正文',url:u.searchParams.get('url'),description:'摘要',paragraphs:['兼容正文'],blocks:[
    {type:'text',text:'公开阅读正文。'.repeat(30)},
    {type:'image',url:'https://article.example/missing.jpg',alt:'失效图片'},
    {type:'unavailable',label:'第三方播放器',url:'https://article.example/embed'},
    ...Array.from({length:20},()=>({type:'text',text:'继续阅读文章。'.repeat(30)}))
  ]});
  if (u.hostname === 'registry.npmjs.org') return Response.json({total:1,objects:[{package:{name:'myriad-test',description:'公开软件包',links:{npm:'https://npmjs.com/package/myriad-test'}}}]});
  if (u.hostname === 'api.github.com' && u.pathname.includes('/search')) return Response.json({total_count:1,items:[{full_name:'myriad/test',description:'公开仓库',html_url:'https://github.com/myriad/test'}]});
  if (u.hostname === 'api.open-meteo.com') return Response.json({latitude:30,longitude:120,current:{temperature_2m:20,apparent_temperature:19,weather_code:0,is_day:1},daily:{time:[],sunrise:[],sunset:[]},hourly:{time:[]}});
  if (u.hostname === 'v1.hitokoto.cn') return Response.json({id:1,hitokoto:'本机访客测试',from:'测试'});
  return Response.json({});
};
})()"""

audio = io.BytesIO()
with wave.open(audio, 'wb') as wav:
    wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(8000)
    wav.writeframes(b'\0\0' * 8000 * 120)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), headless=True)
    context = browser.new_context(viewport={'width':1440,'height':1000},locale='zh-CN',timezone_id='Asia/Shanghai',color_scheme='dark')
    context.add_init_script(MOCK)
    context.add_init_script("""if (!localStorage.getItem('m5-seeded')) {
      localStorage.setItem('m5-seeded', '1');
      localStorage.setItem('myriad.local', JSON.stringify({sync:{enabled:true,apiBase:'https://private.example',token:'isolated-test-token'}}));
      localStorage.setItem('homepage.myriad.visitor.myriad.local', JSON.stringify({sync:{enabled:true,apiBase:'https://private.example',token:'must-not-leave'}}));
    }""")
    context.route('**/song/media/**',lambda route:route.fulfill(body=audio.getvalue(),content_type='audio/wav'))
    context.route('**/api/music/lyrics?*',lambda route:route.fulfill(json={'lines':[],'instrumental':True}))
    context.route('https://article.example/**',lambda route:route.fulfill(status=404,body='Missing'))
    page = context.new_page()
    errors = []
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE+'/',wait_until='networkidle')
    page.get_by_role('button',name='打开网易云音乐播放器').click()
    page.wait_for_function('document.querySelector("audio")?.currentTime > 0')
    page.evaluate('window.m5audio=document.querySelector("audio"); window.m5time=m5audio.currentTime; window.m5document=document')
    page.get_by_role('button',name='关闭音乐播放器').click()
    page.locator('.desktop-nav').get_by_role('link',name='万象导航').click()
    expect(page.locator('.myriad:not(.is-loading)')).to_be_visible()
    check(page.evaluate('document===m5document && m5audio===document.querySelector("audio") && !m5audio.paused && m5audio.currentTime>=m5time'),'进入万象保持播放并保留实例与进度')
    check(page.get_by_role('button',name='打开网易云音乐播放器').count()==1,'万象显示音乐入口')
    check(page.locator('.m-onb').count()==0,'访客直接使用默认预设')
    page.mouse.move(900,500)
    page.wait_for_function('getComputedStyle(document.querySelector(".app-header-transition")).opacity==="0"')
    check(page.locator('.desktop-nav [aria-current="page"]').inner_text()=='万象导航','主导航正确标记当前页')
    page.mouse.move(700,2)
    page.wait_for_function('getComputedStyle(document.querySelector(".app-header-transition")).opacity==="1"')
    check(True,'鼠标移到顶端显示导航')
    page.mouse.move(900,500)
    page.locator('.desktop-nav a').first.focus()
    page.wait_for_function('getComputedStyle(document.querySelector(".app-header-transition")).opacity==="1"')
    check(True,'键盘焦点也能显示隐藏导航')
    page.locator('.desktop-nav a').first.click()
    expect(page.locator('.hero')).to_be_visible()
    check(page.evaluate('m5audio===document.querySelector("audio") && !m5audio.paused'),'返回主页保留音乐并持续播放')
    page.locator('.desktop-nav').get_by_role('link',name='万象导航').click()
    expect(page.locator('.myriad:not(.is-loading)')).to_be_visible()
    page.wait_for_function("localStorage.getItem('homepage.myriad.visitor.myriad.data')")
    page.locator('.m-toolbar button').last.click()
    drawer=page.locator('.m-drawer')
    expect(drawer).to_be_visible()
    check(drawer.get_by_role('button',name='同步',exact=True).count()==0 and drawer.get_by_role('button',name='服务密钥',exact=True).count()==0,'访客设置不显示同步与服务密钥')
    drawer.get_by_role('button',name='关闭',exact=True).click()
    page.locator('.m-toolbar button').first.click()
    editor=page.locator('dialog[open]')
    editor.locator('input[inputmode="url"]').fill('https://example.com/myriad-visitor')
    editor.locator('input[inputmode="url"]').press('Tab')
    expect(editor.locator('input[maxlength="40"]')).to_have_value('Example')
    editor.locator('input[maxlength="40"]').fill('访客快捷方式')
    editor.get_by_role('button',name='保存',exact=True).click()
    page.wait_for_timeout(700)
    page.wait_for_function("JSON.parse(localStorage.getItem('homepage.myriad.visitor.myriad.data')).items && Object.values(JSON.parse(localStorage.getItem('homepage.myriad.visitor.myriad.data')).items).some(i=>i.title==='访客快捷方式')")
    page.reload()
    expect(page.locator('.myriad:not(.is-loading)')).to_be_visible()
    check(page.locator('.myriad').get_by_text('访客快捷方式',exact=True).count()==1,'快捷方式修改在重载后保留')
    check(page.evaluate("JSON.parse(localStorage.getItem('myriad.local')).sync.token==='isolated-test-token' && !JSON.parse(localStorage.getItem('homepage.myriad.visitor.myriad.local')).sync.enabled"),'访客存储隔离并清除残留同步配置')
    # Set a deterministic multi-feed fixture through the same stored data shape as JSON import.
    page.evaluate("""() => {
      const prefix='homepage.myriad.visitor.',data=JSON.parse(localStorage.getItem(prefix+'myriad.data'));
      data.items['m5-feed']={id:'m5-feed',type:'widget',kind:'feeds',size:'2x4',config:{sources:['v2ex','github'],selectedSource:'v2ex',aiSummary:true}};
      data.items['m5-rss']={id:'m5-rss',type:'widget',kind:'feeds',size:'2x4',config:{mode:'rss',subscriptions:[{id:'m5-sub',title:'测试订阅',url:'https://article.example/rss',rsshub:false}]}};
      data.groups[0].items=['m5-feed','m5-rss'];data.updatedAt=Date.now();localStorage.setItem(prefix+'myriad.data',JSON.stringify(data));
      const settings=JSON.parse(localStorage.getItem(prefix+'myriad.settings'))||{};
      settings.search={...settings.search,aggregate:{enabled:true,engines:['google','bing','github','npm'],routes:{google:'worker',bing:'worker'}}};
      localStorage.setItem(prefix+'myriad.settings',JSON.stringify(settings));
    }""")
    page.reload()
    feed=page.locator('[data-drop-item="m5-feed"]')
    expect(feed).to_contain_text('公开文章')
    expect(page.locator('[data-drop-item="m5-rss"]')).to_contain_text('公开文章')
    check(True,'公开热榜与 RSS 在访客页面可用')
    feed.locator('select').select_option('github')
    page.wait_for_function("JSON.parse(localStorage.getItem('homepage.myriad.visitor.myriad.data')).items['m5-feed'].config.selectedSource==='github'")
    page.reload()
    expect(feed.locator('select')).to_have_value('github')
    check(True,'每个热榜组件保留平台选择')
    feed.get_by_role('button',name='公开文章',exact=True).hover()
    expect(page.locator('.m-feed-hover:popover-open')).to_contain_text('公开阅读正文')
    check(page.locator('.m-feed-hover iframe').count()==0,'悬停以正文阅读模式展示')
    page.mouse.move(900,900)
    feed.get_by_role('button',name='公开文章',exact=True).click()
    preview=page.locator('dialog[open]')
    expect(preview).to_contain_text('公开阅读正文')
    expect(preview).to_contain_text('第三方播放器')
    check(preview.locator('iframe').count()==0,'点击预览保留弹窗并显示媒体占位')
    preview.get_by_role('button',name='关闭',exact=True).click()
    page.locator('.m-search__input').fill('visitor query')
    page.locator('.m-search__input').press('Enter')
    results=page.locator('.m-results')
    expect(results).to_contain_text('myriad-test')
    check(results.locator('a[href^="https://www.google.com/search"]').count()>0,'通用网页搜索提供第三方跳转')
    check(page.evaluate("history.state.current===location.pathname+location.hash && history.state.back.startsWith('/myriad')"),'聚合搜索保留宿主路由历史状态')
    page.go_back()
    expect(feed).to_be_visible()
    page.go_forward()
    expect(results).to_contain_text('myriad-test')
    check(True,'搜索前进后退恢复正确页面')
    results.get_by_role('button',name='返回',exact=True).click()
    for _ in range(5):page.locator('.m-clock').click()
    check(page.url==BASE+'/myriad','连续点击时钟不触发登录')
    page.locator('.m-toolbar button').last.click()
    drawer.get_by_role('button',name='数据',exact=True).click()
    with page.expect_download() as download:
      drawer.get_by_role('button',name='导出数据',exact=True).click()
    backup=json.loads(Path(download.value.path()).read_text())
    check('must-not-leave' not in json.dumps(backup) and 'isolated-test-token' not in json.dumps(backup),'导出 JSON 不包含本机连接凭据')
    backup['data']['groups'][0]['name']='导入访客分组'
    drawer.locator('input[type="file"][accept="application/json,.json"]').set_input_files({'name':'visitor-backup.json','mimeType':'application/json','buffer':json.dumps(backup,ensure_ascii=False).encode()})
    expect(page.locator('.m-toast').filter(has_text='导入完成')).to_be_visible()
    drawer.get_by_role('button',name='关闭',exact=True).click()
    expect(page.locator('.myriad')).to_contain_text('导入访客分组')
    check(True,'JSON 导入恢复访客分组')
    page.evaluate("document.querySelector('.desktop-nav a').focus()")
    page.locator('.desktop-nav').get_by_role('link',name='首页',exact=True).click()
    expect(page.locator('.hero')).to_be_visible()
    page.locator('.desktop-nav').get_by_role('link',name='万象导航').click()
    expect(page.locator('.myriad')).to_contain_text('导入访客分组')
    check(True,'离开并再次进入恢复本机数据')
    page.mouse.move(900,500)
    page.wait_for_function('!document.querySelector(".page-swap-enter-active, .page-swap-leave-active")')
    page.screenshot(path=str(OUT/'myriad-desktop.png'),full_page=True,animations='disabled')
    check(page.evaluate("!window.m5xss && m5calls.every(c=>!c.url.includes('/me/')&&!c.url.endsWith('/me')&&!c.url.includes('/sync')&&!c.auth)"),'访客无私有 API 或令牌请求，正文无脚本执行')
    # Theme changes through settings update the host too; host changes survive leaving the page.
    page.locator('.m-toolbar button').last.click()
    drawer.get_by_role('button',name='外观',exact=True).click()
    drawer.get_by_role('radio',name='胡桃红',exact=True).click()
    page.wait_for_function("document.documentElement.dataset.palette==='hutao-red' && document.querySelector('.myriad').dataset.palette==='hutao-red'")
    check(True,'万象配色同步到主页主题')
    drawer.get_by_role('radio',name='浅色',exact=True).click()
    page.wait_for_function("document.documentElement.dataset.theme==='light' && document.querySelector('.myriad').dataset.theme==='light'")
    drawer.get_by_role('button',name='关闭',exact=True).click()
    expect(drawer).to_have_count(0)
    page.screenshot(path=str(OUT/'myriad-light.png'),full_page=True,animations='disabled')
    check(page.evaluate("document.documentElement.lang==='zh-CN' && !document.documentElement.style.colorScheme"),'嵌入组件不覆盖宿主语言与根色彩模式')
    page.emulate_media(reduced_motion='reduce')
    check(page.locator('.app-header-transition').evaluate("el=>getComputedStyle(el).transitionDuration.split(',').every(v=>parseFloat(v)<=0.001)"),'减少动态效果关闭导航滑动')
    for width in [1024,768]:
        page.set_viewport_size({'width':width,'height':1000})
        check(page.evaluate('document.documentElement.scrollWidth<=innerWidth'),'桌面宽度 '+str(width)+' 无横向溢出')
    check(not errors,'桌面无 JavaScript 错误')
    context.close()
    for width in [320,390,760]:
        mobile=browser.new_context(viewport={'width':width,'height':844},locale='zh-CN',reduced_motion='reduce',color_scheme='dark' if width==390 else 'light')
        resources=[]
        mobile.on('request',lambda r:resources.append(r.url))
        mobilepage=mobile.new_page()
        mobilepage.goto(BASE+'/myriad',wait_until='networkidle')
        expect(mobilepage.get_by_role('heading',name='抱歉，万象暂不支持手机')).to_be_visible()
        check(mobilepage.locator('.myriad').count()==0 and not any('MyriadDesktop' in u for u in resources),'手机 '+str(width)+' 仅展示提示页，不加载桌面包')
        check(mobilepage.evaluate('document.documentElement.scrollWidth<=innerWidth'),'手机 '+str(width)+' 无横向溢出')
        if width==390:mobilepage.screenshot(path=str(OUT/'myriad-mobile.png'),full_page=True)
        mobile.close()
    browser.close()
print(f'{len(checks)} M5 browser checks passed.')
