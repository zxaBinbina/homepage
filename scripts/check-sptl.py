"""Check SPTL navigation, demo controls, copy, source download and layout."""
import json
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
base = os.environ.get("HOMEPAGE_TEST_URL", "http://127.0.0.1:5173").rstrip("/")
route = "/projects/SPTL"
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        executable_path=os.environ.get("HOMEPAGE_BROWSER", "/usr/bin/google-chrome"),
        args=["--no-sandbox"],
    )
    context = browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
    context.grant_permissions(["clipboard-read", "clipboard-write"], origin=base)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(base + "/project", wait_until="networkidle")
    page.evaluate("window.sptlNavigationProbe = true")
    page.get_by_role("searchbox", name="搜索项目").fill("SPTL")
    expect(page.locator(".project-card")).to_have_count(1)
    page.locator(".project-card").click()
    expect(page).to_have_title("SPTL · SPlayer 任务栏歌词")
    expect(page.locator(".sptl-header")).to_be_visible()
    assert page.evaluate("window.sptlNavigationProbe"), "Navigation replaced the document"
    expect(page.locator('link[rel="canonical"]')).to_have_attribute("href", "https://zxabinbina.cc.cd/projects/SPTL")
    expect(page.locator('link[rel="icon"]')).to_have_attribute("href", "/images/sptl.png")
    expect(page.locator('meta[property="og:image"]')).to_have_attribute("content", "https://zxabinbina.cc.cd/images/sptl-share.png")
    expect(page.locator('a[href^="mailto:"], a[href="/"], a[href="/project"]')).to_have_count(0)
    assert "zxabinbina@mcyzw.top" not in page.locator("body").inner_text()
    assert "AGPL" not in page.locator("body").inner_text()
    assert "https://zxabinbina.cc.cd/projects/SPTL" not in page.locator("body").inner_text()
    page.go_back()
    expect(page).to_have_title("项目目录 · a彬彬a")
    expect(page.locator('link[rel="icon"]')).to_have_attribute("href", "/favicon.svg")
    page.go_forward()
    expect(page).to_have_title("SPTL · SPlayer 任务栏歌词")

    # Reduced motion starts paused. Advancing and changing layout remain usable.
    expect(page.get_by_role("button", name="播放歌词演示", exact=True)).to_be_visible()
    expect(page.locator(".sptl-demo-primary")).to_have_text("把今天唱给你听")
    page.get_by_role("button", name="下一句演示歌词").click()
    expect(page.locator(".sptl-demo-primary")).to_have_text("让旋律陪你走过每一步")
    page.get_by_role("button", name="上一句演示歌词").click()
    page.get_by_role("radio", name="歌词 + 信息", exact=True).click()
    expect(page.locator(".sptl-demo-lyrics p").last).to_have_text("今天的旋律 · SPTL")
    page.get_by_role("radio", name="双行歌词", exact=True).click()
    expect(page.locator(".sptl-demo-lyrics p").last).to_have_text("Sing today for you")
    page.get_by_role("button", name="播放歌词演示", exact=True).click()
    expect(page.get_by_role("button", name="暂停歌词演示", exact=True)).to_be_visible()
    page.wait_for_timeout(350)
    page.get_by_role("button", name="暂停歌词演示", exact=True).click()
    highlight = page.locator(".sptl-demo-primary").get_attribute("style")
    page.wait_for_timeout(250)
    assert page.locator(".sptl-demo-primary").get_attribute("style") == highlight

    page.get_by_role("navigation", name="SPTL 导航").get_by_role("link", name="安装指南").click()
    expect(page).to_have_url(base + route + "#install")
    expect(page.locator("#install h2")).to_be_in_viewport()
    page.get_by_role("button", name="复制安装命令").click()
    expect(page.locator(".sptl-copy-status")).to_have_text("安装命令已复制")
    assert page.evaluate("navigator.clipboard.readText()") == "cd SPTL-0.1.1\npython3 tools/install.py"
    with page.expect_download() as download_info:
        page.get_by_role("link", name="完整源码包 v0.1.1").click()
    download = download_info.value
    assert download.suggested_filename == "sptl-0.1.1-source.zip"
    with zipfile.ZipFile(download.path()) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert "SPTL-0.1.1/tools/install.py" in names
        assert "SPTL-0.1.1/LICENSE" in names
        assert not any(".git/" in name or ".env" in name for name in names)
        metadata = json.loads(archive.read("SPTL-0.1.1/plasmoid/metadata.json"))
        assert metadata["KPlugin"]["Website"] == "https://zxabinbina.cc.cd/projects/SPTL"
        assert metadata["KPlugin"]["Authors"][0]["Email"] == "zxabinbina@mcyzw.top"
        assert metadata["KPlugin"]["License"] == "AGPL-3.0-only"
        with tempfile.TemporaryDirectory(prefix="sptl-website-source-") as directory:
            archive.extractall(directory)
            result = subprocess.run(["python3", "tools/build.py"], cwd=Path(directory) / "SPTL-0.1.1", capture_output=True, text=True)
            assert result.returncode == 0, result.stdout + result.stderr

    # FAQ keeps native details semantics and works with the keyboard.
    question = page.locator(".sptl-faq summary").first
    question.focus()
    page.keyboard.press("Enter")
    expect(question).to_have_attribute("aria-expanded", "true")
    expect(page.locator(".sptl-faq details").first.locator("p")).to_be_visible()
    page.keyboard.press("Enter")
    expect(question).to_have_attribute("aria-expanded", "false")

    for palette in ("fufu-blue", "hutao-red"):
        for theme in ("dark", "light"):
            page.evaluate("([palette, theme]) => { localStorage.setItem('homepage-palette', palette); localStorage.setItem('homepage-theme', theme) }", [palette, theme])
            page.goto(base + route, wait_until="networkidle")
            for width in (320, 390, 768, 1024, 1440):
                page.set_viewport_size({"width": width, "height": 1000})
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (palette, theme, width)
                assert page.locator(".sptl-page img, .sptl-header img").evaluate_all("items => items.every(item => item.complete && item.naturalWidth > 0)")
                bounds = page.locator(".sptl-header").bounding_box()
                assert bounds and bounds["height"] <= 66 and bounds["width"] <= width, bounds
                if width in (390, 1440):
                    page.screenshot(path=str(ROOT / f"artifacts/sptl-{palette}-{theme}-{width}.png"), full_page=True)

    assert not errors, errors
    browser.close()
print("SPTL routing, metadata, demo pause/layout/skip, clipboard, source download/build, FAQ keyboard and 20 theme/width combinations passed")
