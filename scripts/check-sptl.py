"""Check SPTL navigation, real recording, feature photos, downloads and layout."""
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
version = "1.2.1"
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        executable_path=os.environ.get("HOMEPAGE_BROWSER", "/usr/bin/google-chrome"),
        args=["--no-sandbox"],
    )
    context = browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
    context.grant_permissions(["clipboard-read", "clipboard-write"], origin=base)
    api_payload = None
    def release_fixture(request):
        request.fulfill(status=200 if api_payload else 503,
                        content_type="application/json", body=json.dumps(api_payload or {"error": "offline"}))
    context.route("**/api/projects/SPTL/release", release_fixture)
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
    # The installation command contains the site URL; project contact details stay hidden.
    text_without_commands = page.locator("body").evaluate("""element => {
        const copy = element.cloneNode(true)
        copy.querySelectorAll('pre').forEach(command => command.remove())
        return copy.textContent
    }""")
    assert "https://zxabinbina.cc.cd/projects/SPTL" not in text_without_commands
    page.go_back()
    expect(page).to_have_title("项目目录 · a彬彬a")
    expect(page.locator('link[rel="icon"]')).to_have_attribute("href", "/favicon.svg")
    page.go_forward()
    expect(page).to_have_title("SPTL · SPlayer 任务栏歌词")

    # The hero uses recorded desktop frames, with a still image for reduced motion.
    recording = page.locator(".sptl-recording-stage img")
    def recording_path(): return recording.evaluate("image => new URL(image.src).pathname")
    expect(page.get_by_role("button", name="播放实拍动图", exact=True)).to_be_visible()
    assert recording_path() == "/images/sptl/hero-poster.webp"
    expect(page.locator(".sptl-demo")).to_have_count(0)
    expect(page.locator(".sptl-feature")).to_have_count(6)
    expect(page.locator(".sptl-feature-photo")).to_have_count(10)
    for feature in page.locator(".sptl-feature").all():
        assert feature.locator(".sptl-feature-photo").count() >= 1
    page.get_by_role("button", name="播放实拍动图", exact=True).click()
    expect(page.get_by_role("button", name="暂停实拍动图", exact=True)).to_be_visible()
    assert recording_path() == "/images/sptl/hero-live.gif"
    page.get_by_role("button", name="暂停实拍动图", exact=True).click()
    assert recording_path() == "/images/sptl/hero-poster.webp"
    page.emulate_media(reduced_motion="no-preference")
    page.get_by_role("button", name="播放实拍动图", exact=True).click()
    page.emulate_media(reduced_motion="reduce")
    expect(page.get_by_role("button", name="播放实拍动图", exact=True)).to_be_visible()
    assert recording_path() == "/images/sptl/hero-poster.webp"
    page.get_by_role("button", name="播放实拍动图", exact=True).click()

    page.get_by_role("navigation", name="SPTL 导航").get_by_role("link", name="安装指南").click()
    expect(page).to_have_url(base + route + "#install")
    expect(page.locator("#install h2")).to_be_in_viewport()
    expect(page.get_by_role("button", name="播放实拍动图", exact=True)).to_be_attached()
    assert recording_path() == "/images/sptl/hero-poster.webp", "Offscreen recording must use a still frame"
    page.get_by_role("button", name="复制安装命令").click()
    expect(page.locator(".sptl-copy-status")).to_have_text("安装命令已复制")
    command = "curl -fsSL 'https://zxabinbina.cc.cd/projects/SPTL/install.sh' | sh"
    assert page.evaluate("navigator.clipboard.readText()") == command
    expect(page.get_by_role("list", name="安装要求")).to_contain_text("SPlayer Next 插件 API 5+")
    assert page.locator(".sptl-feature-photo img").evaluate_all("images => images.every(image => new URL(image.src).pathname.startsWith('/images/sptl/'))")
    from PIL import Image
    with Image.open(ROOT / "public/images/sptl/hero-live.gif") as gif:
        assert gif.n_frames >= 20 and gif.info.get("loop") == 0
    expect(page.locator(".sptl-release-status")).to_contain_text("已核对的 v1.2.1")
    with page.expect_download() as script_download:
        page.get_by_role("link", name="下载安装脚本", exact=True).click()
    assert Path(script_download.value.path()).read_bytes() == (ROOT / "public/projects/SPTL/install.sh").read_bytes()
    with page.expect_download() as download_info:
        page.get_by_role("link", name=f"本站源码包 v{version}").click()
    download = download_info.value
    assert download.suggested_filename == f"sptl-{version}-source.zip"
    with zipfile.ZipFile(download.path()) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert f"SPTL-{version}/tools/install.py" in names
        assert f"SPTL-{version}/LICENSE" in names
        assert not any(".git/" in name or ".env" in name for name in names)
        metadata = json.loads(archive.read(f"SPTL-{version}/plasmoid/metadata.json"))
        assert metadata["KPlugin"]["Version"] == version
        assert metadata["KPlugin"]["Website"] == "https://zxabinbina.cc.cd/projects/SPTL"
        assert metadata["KPlugin"]["Authors"][0]["Email"] == "zxabinbina@mcyzw.top"
        assert metadata["KPlugin"]["License"] == "AGPL-3.0-only"
        with tempfile.TemporaryDirectory(prefix="sptl-website-source-") as directory:
            archive.extractall(directory)
            source_root = Path(directory) / f"SPTL-{version}"
            result = subprocess.run(["python3", "tools/build.py"], cwd=source_root, capture_output=True, text=True)
            assert result.returncode == 0, result.stdout + result.stderr
            assert (source_root / f"dist/sptl-plasma5-{version}.plasmoid").is_file()
            assert (source_root / f"dist/sptl-plasma6-{version}.plasmoid").is_file()

    # A new release updates version, notes and download targets without changing website source.
    future = "1.3.0"
    release_url = f"https://github.com/zxaBinbina/SplayerPlasmaTaskbarLyrics/releases/tag/v{future}"
    source_url = f"https://github.com/zxaBinbina/SplayerPlasmaTaskbarLyrics/releases/download/v{future}/sptl-source-{future}.tar.gz"
    api_payload = {"version": future, "url": release_url, "publishedAt": "2026-12-01T00:00:00Z",
                   "body": "新版发行说明 <script>window.sptlInjected = true</script>",
                   "assets": [{"name": f"sptl-source-{future}.tar.gz", "url": source_url, "size": 100}]}
    page.get_by_role("button", name="刷新最新版本").click()
    expect(page.locator(".sptl-hero-copy .sptl-caption")).to_contain_text(f"v{future} 正式版")
    expect(page.get_by_role("link", name=f"完整源码 v{future}")).to_have_attribute("href", source_url)
    expect(page.get_by_role("link", name="完整发行说明")).to_have_attribute("href", release_url)
    expect(page.locator(".sptl-release-notes")).to_contain_text("新版发行说明")
    assert page.evaluate("window.sptlInjected === undefined")
    api_payload["assets"] = []
    page.get_by_role("button", name="刷新最新版本").click()
    expect(page.get_by_role("link", name="查看发行文件", exact=True)).to_have_attribute("href", release_url)
    expect(page.get_by_role("link", name=f"本站源码包 v{version}")).to_have_count(0)
    api_payload = None
    page.get_by_role("button", name="刷新最新版本").click()
    expect(page.locator(".sptl-release-status")).to_contain_text(f"上次同步的 v{future}")
    assert page.evaluate("navigator.clipboard.readText()") == command

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
print("SPTL routing, metadata, real recording pause/reduced motion/offscreen state, 10 feature photos, installation/downloads, dynamic versions, FAQ keyboard and 20 theme/width combinations passed")
