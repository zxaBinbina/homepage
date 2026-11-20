"""Render SPTL's 1200 x 630 social card with the live site's CSS and demo."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
base = os.environ.get("HOMEPAGE_TEST_URL", "http://127.0.0.1:5173").rstrip("/")
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        executable_path=os.environ.get("HOMEPAGE_BROWSER", "/usr/bin/google-chrome"),
        args=["--no-sandbox"],
    )
    page = browser.new_page(viewport={"width": 1200, "height": 630}, reduced_motion="reduce")
    page.add_init_script("localStorage.setItem('homepage-theme', 'dark'); localStorage.setItem('homepage-palette', 'fufu-blue')")
    page.goto(base + "/projects/SPTL", wait_until="networkidle")
    page.evaluate("""() => {
      const panel = document.querySelector('.sptl-demo-panel').cloneNode(true);
      const card = document.createElement('main');
      card.className = 'sptl-social-card';
      card.innerHTML = `<div class="sptl-social-top"><img src="/images/sptl.png" width="56" height="56" alt=""><b>SPTL</b><span>SPLAYER TASKBAR LYRICS</span></div>
        <div class="sptl-social-copy"><h1>让歌词，<br><span>留在任务栏。</span></h1><p>SPlayer Next × KDE Plasma</p></div>
        <div class="sptl-social-panel"></div><div class="sptl-social-footer"><span>同步歌词 · 专辑封面 · 播放控制</span><span>SPTL / KDE PLASMA</span></div>`;
      card.querySelector('.sptl-social-panel').append(panel);
      document.body.replaceChildren(card);
      const style = document.createElement('style');
      style.textContent = `body{margin:0;width:1200px;height:630px;background:var(--bg);overflow:hidden}
        .sptl-social-card{padding:56px 64px;height:630px;background:radial-gradient(ellipse at 90% 25%,var(--ambient-glow),transparent 65%)}
        .sptl-social-top{display:flex;align-items:center;gap:16px;font-size:30px}
        .sptl-social-top>span{margin-left:auto;color:var(--muted);font:14px monospace;letter-spacing:2px}
        .sptl-social-copy{display:flex;align-items:end;justify-content:space-between;margin:32px 0}
        .sptl-social-copy h1{margin:0;font-size:64px;line-height:1.3;letter-spacing:0;font-weight:700}
        .sptl-social-copy h1 span{color:var(--accent);background:none;-webkit-text-fill-color:var(--accent)}
        .sptl-social-copy p{font-size:20px;color:var(--muted);padding-bottom:12px}
        .sptl-social-panel .sptl-demo-panel{padding:16px 24px;border-radius:20px;background:var(--panel)}
        .sptl-social-panel .sptl-demo-lyrics{font-size:16px}
        .sptl-social-panel .sptl-demo-primary{font-size:20px}
        .sptl-social-footer{display:flex;justify-content:space-between;margin-top:28px;color:var(--muted);font-size:14px}`;
      document.head.append(style);
    }""")
    page.screenshot(path=str(ROOT / "public/images/sptl-share.png"))
    browser.close()
print("Rendered public/images/sptl-share.png (1200 x 630)")
