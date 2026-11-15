"""Verify the pinned XCPDF engine through all 43 website routes and real exports."""
import io
import json
import os
import zipfile
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright, expect

base = os.environ.get('HOMEPAGE_TEST_URL', 'http://127.0.0.1:5173').rstrip('/')
out = Path('artifacts/xcpdf'); out.mkdir(parents=True, exist_ok=True)
manifest = json.loads(Path('third_party/xcpdf/upstream.json').read_text())
actions = ['merge-btn','merge-alt-btn','split-btn','bookmark-split-btn','bookmark-explode-btn',
 'manage-export','reverse-btn','pad-btn','delete-btn','remove-blank-btn','rotate-btn',
 'rotate-single-save-btn','impose-btn','booklet-btn','booklet-split-btn','unify-btn','split-book-btn',
 'skew-btn','crop-btn','blank-btn','convert-download-all','img2pdf-export','p2t-download','flatten-btn',
 'extimg-download-all','filter-btn','blueprint-btn','scan-btn','pagenum-btn','bates-btn','wmtext-btn',
 'wmimg-btn','stamp-save-btn','perf-apply-btn','mark-apply-btn','red-btn','meta-save-btn',None,
 'bm-save','remove-bm-btn','compress-btn',None,'encrypt-btn']
image_buffer = io.BytesIO(); Image.new('RGB', (180, 120), (210, 30, 50)).save(image_buffer, format='PNG')
image_bytes = image_buffer.getvalue()

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('HOMEPAGE_BROWSER', '/usr/bin/google-chrome'), args=['--no-sandbox'])
    context = browser.new_context(viewport={'width':1440,'height':1000}, reduced_motion='reduce', permissions=['clipboard-read','clipboard-write'])
    page = context.new_page()
    errors, remote, failures, exports = [], [], [], {}
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda r: remote.append(r.url) if r.url.startswith(('http:', 'https:')) and not r.url.startswith(base) else None)
    page.on('dialog', lambda dialog: dialog.accept('test-password') if dialog.type == 'prompt' else dialog.accept())
    def open_tool(item):
        page.goto(base + '/tools/' + item['id'])
        expect(page.locator('.xcpdf-frame-wrap')).to_have_attribute('aria-busy','false', timeout=25000)
        expect(page.locator('main h1')).to_have_text(item['name'])
        expect(page.get_by_role('link', name='MIT 开源许可', exact=True)).to_be_visible()
        f = page.frames[-1]
        expect(f.locator('[data-current]')).to_have_attribute('id',item['panel'])
        return f
    frame = open_tool(manifest['tools'][19])
    # Independent known fixture: two named pages around one blank page, embedded image and outline.
    data = bytes(frame.evaluate('''async image => {
      const { PDFDocument, PDFName, PDFString, rgb } = PDFLib;
      const doc = await PDFDocument.create(); doc.setTitle('Fixture'); doc.setAuthor('Test Author');
      const img = await doc.embedPng(new Uint8Array(image));
      const pages = [doc.addPage([240,180]), doc.addPage([240,180]), doc.addPage([240,180])];
      pages[0].drawText('FIRST PAGE', {x:20,y:130,size:16});
      pages[0].drawImage(img,{x:20,y:20,width:90,height:60});
      pages[2].drawText('LAST PAGE', {x:20,y:130,size:16});
      const root = doc.context.obj({Type:'Outlines',Count:2}); const rootRef = doc.context.register(root);
      const first = doc.context.obj({Title:PDFString.of('First chapter'),Parent:rootRef,Dest:[pages[0].ref,PDFName.of('Fit')]});
      const last = doc.context.obj({Title:PDFString.of('Last chapter'),Parent:rootRef,Dest:[pages[2].ref,PDFName.of('Fit')]});
      const firstRef=doc.context.register(first), lastRef=doc.context.register(last);
      first.set(PDFName.of('Next'),lastRef);last.set(PDFName.of('Prev'),firstRef);
      root.set(PDFName.of('First'),firstRef);root.set(PDFName.of('Last'),lastRef);
      doc.catalog.set(PDFName.of('Outlines'),rootRef);
      return Array.from(await doc.save({useObjectStreams:false}));
    }''', list(image_bytes)))
    (out/'fixture.pdf').write_bytes(data)
    pdf = {'name':'fixture.pdf','mimeType':'application/pdf','buffer':data}
    png = {'name':'stamp.png','mimeType':'image/png','buffer':image_bytes}
    for item, action in zip(manifest['tools'],actions):
        try:
            frame = open_tool(item)
            for width in [320,390,768,1024,1440]:
                page.set_viewport_size({'width':width,'height':1000})
                page.wait_for_timeout(40)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), ('outer overflow',item['id'],width)
                assert frame.evaluate('document.documentElement.scrollWidth <= innerWidth'), ('frame overflow',item['id'],width)
            inputs = frame.locator('[data-current] input[type=file]')
            if inputs.count():
                inputs.first.set_input_files([pdf,pdf] if item['id'] in ['pdf-merge','pdf-merge-alternating','pdf-bates'] else png if item['id']=='pdf-images-to-pdf' else pdf)
                page.wait_for_timeout(650)
            if item['id']=='pdf-blank': frame.locator('#blank-pages').fill('3')
            if item['id']=='pdf-split': frame.locator('input[value="single"]').check()
            if item['id']=='pdf-split-bookmarks': frame.locator('#bookmark-sel-all').click()
            if item['id']=='pdf-delete-pages': frame.locator('#delete-range-input').fill('2')
            if item['id']=='pdf-extract-text':
                frame.locator('#p2t-btn').click()
                expect(frame.locator('#p2t-copy')).to_be_enabled(timeout=20000)
                frame.locator('#p2t-copy').click()
                page.wait_for_function('navigator.clipboard.readText().then(text=>text.includes("FIRST PAGE") && text.includes("LAST PAGE"))')
            if item['id']=='pdf-metadata': frame.locator('#meta-title').fill('Updated title')
            if item['id']=='pdf-text-watermark': frame.locator('#wmtext-text').fill('LOCAL WATERMARK')
            if item['id'] in ['pdf-image-watermark','pdf-stamp','pdf-seam-stamp']:
                inputs.nth(1).set_input_files(png)
                page.wait_for_timeout(300)
                if item['id']=='pdf-stamp': frame.locator('#stamp-apply-btn').click()
            if item['id']=='pdf-encrypt': frame.locator('#encrypt-user-pwd').fill('test-password')
            if item['id']=='pdf-redact':
                box = frame.locator('#red-overlay').bounding_box()
                page.mouse.move(box['x']+20,box['y']+20);page.mouse.down()
                page.mouse.move(box['x']+160,box['y']+75,steps=6);page.mouse.up()
            if item['id']=='pdf-edit-bookmarks': frame.locator('#bm-import').click()
            if action:
                button = frame.locator('#'+action)
                expect(button).to_be_enabled(timeout=20000)
                with page.expect_download(timeout=30000) as event: button.click()
                target=out/(item['id']+'-'+event.value.suggested_filename)
                event.value.save_as(target)
                result=target.read_bytes(); assert len(result)>0
                if zipfile.is_zipfile(target):
                    with zipfile.ZipFile(target) as zipped:
                        assert zipped.namelist(), item['id']
                        if item['id'] in ['pdf-to-images','pdf-split']: assert len(zipped.namelist())==3
                elif item['id']=='pdf-extract-text':
                    assert b'FIRST PAGE' in result and b'LAST PAGE' in result
                else: assert result.startswith(b'%PDF-'), item['id']
                exports[item['id']]=target
            for width in [320,390,768,1024,1440]:
                page.set_viewport_size({'width':width,'height':1000});page.wait_for_timeout(40)
                assert frame.evaluate('document.documentElement.scrollWidth <= innerWidth'), ('loaded overflow',item['id'],width)
            assert not page.locator('.xcpdf-error').count(), (item['id'],page.locator('.xcpdf-error').all_text_contents())
            # Fixed inline colors originally left loaded lists and result notices in the upstream theme.
            fixed_ui_colors=frame.evaluate(r'''Array.from(document.querySelectorAll('[data-current] [style]'))
              .filter(el=>el.getBoundingClientRect().width>0 && !el.matches('canvas,img,.color-preset,.color-swatch,.bm-preset,.bm-title'))
              .flatMap(el=>Array.from(el.style).filter(property=>/color|background|border|outline|shadow/.test(property)
                && /#[a-f0-9]{3,8}\b|rgba?\(/i.test(el.style.getPropertyValue(property)))
                .map(property=>[el.id,property,el.style.getPropertyValue(property)]))''')
            assert not fixed_ui_colors,(item['id'],fixed_ui_colors)
            print('PASS',item['id'],flush=True)
        except Exception as error:
            detail = frame.locator('[data-current]').inner_text()[-1000:]
            failures.append((item['id'],str(error)[:900],detail));print('FAIL',item['id'],str(error)[:500],detail,flush=True)
    # Check exported content independently with the original PDF renderer, including encrypted output.
    frame = open_tool(manifest['tools'][19])
    expected_counts={'pdf-merge':6,'pdf-merge-alternating':6,'pdf-reverse':3,'pdf-pad-even':4,'pdf-delete-pages':2,'pdf-remove-blank-pages':2,'pdf-booklet':2,'pdf-split-spread':6}
    for id,count in expected_counts.items():
        if id not in exports: continue
        actual=frame.evaluate('''async data => { const task=pdfjsLib.getDocument({...PDF_JS_OPTS,data:new Uint8Array(data)}); const pdf=await task.promise; const count=pdf.numPages;await task.destroy();return count }''',list(exports[id].read_bytes()))
        assert actual==count,(id,actual,count)
    if 'pdf-encrypt' in exports:
        encrypted=exports['pdf-encrypt'].read_bytes()
        assert frame.evaluate('''async data => {const task=pdfjsLib.getDocument({...PDF_JS_OPTS,data:new Uint8Array(data),password:'test-password'});const pdf=await task.promise;const n=pdf.numPages;await task.destroy();return n}''',list(encrypted))==3
        item=next(t for t in manifest['tools'] if t['id']=='pdf-decrypt')
        frame=open_tool(item);frame.locator('#unlock-file-input').set_input_files({'name':'encrypted.pdf','mimeType':'application/pdf','buffer':encrypted})
        expect(frame.locator('#unlock-btn')).to_be_enabled(timeout=20000)
        with page.expect_download() as d:frame.locator('#unlock-btn').click()
        target=out/'decrypted.pdf';d.value.save_as(target)
        assert frame.evaluate('''async data => {const task=pdfjsLib.getDocument({...PDF_JS_OPTS,data:new Uint8Array(data)});const pdf=await task.promise;const n=pdf.numPages;await task.destroy();return n}''',list(target.read_bytes()))==3
    # Actual theme propagation, screenshots and stored input isolation.
    for id in ['pdf-blank','pdf-merge','pdf-annotate','pdf-edit-bookmarks','pdf-image-watermark']:
        item=next(t for t in manifest['tools'] if t['id']==id)
        frame=open_tool(item)
        inputs=frame.locator('[data-current] input[type=file]')
        if inputs.count():
            inputs.first.set_input_files(pdf)
            if id=='pdf-image-watermark':inputs.nth(1).set_input_files(png)
            page.wait_for_timeout(500)
        export_colors=frame.locator('[data-current] .color-preset, [data-current] .color-swatch, [data-current] .bm-preset').evaluate_all('els=>els.map(el=>getComputedStyle(el).backgroundColor)')
        for theme in ['dark','light']:
            for palette in ['fufu-blue','hutao-red']:
                page.evaluate('''([theme,palette])=>{document.documentElement.dataset.theme=theme;document.documentElement.dataset.palette=palette}''',[theme,palette])
                page.wait_for_timeout(100)
                tokens=page.evaluate('getComputedStyle(document.documentElement).getPropertyValue("--panel").trim()')
                assert frame.evaluate('getComputedStyle(document.documentElement).getPropertyValue("--card-bg").trim()')==tokens
                expected=page.evaluate('''()=>{
                  const el=document.createElement('span');el.style.transition='none';document.body.appendChild(el);
                  const values={};for(const token of ['--blue','--text','--status-success']){
                    el.style.color=`var(${token})`;values[token]=getComputedStyle(el).color;
                  }el.remove();return values;
                }''')
                sliders=frame.locator('[data-current] input[type=range]').evaluate_all('els=>els.map(el=>getComputedStyle(el).accentColor)')
                assert all(color==expected['--blue'] for color in sliders),(id,theme,palette,sliders,expected)
                controls=frame.locator('[data-current] input[type=number], [data-current] input[type=text], [data-current] select, [data-current] textarea').evaluate_all('els=>els.filter(el=>!el.disabled).map(el=>getComputedStyle(el).color)')
                assert all(color==expected['--text'] for color in controls),(id,theme,palette,controls,expected)
                if id in ['pdf-annotate','pdf-image-watermark']:
                    status=frame.locator('#mark-status' if id=='pdf-annotate' else '#wmimg-image-loaded')
                    assert status.evaluate('el=>getComputedStyle(el).color')==expected['--status-success'],(id,theme,palette,status.get_attribute('style'))
                assert frame.locator('[data-current] .color-preset, [data-current] .color-swatch, [data-current] .bm-preset').evaluate_all('els=>els.map(el=>getComputedStyle(el).backgroundColor)')==export_colors,(id,'export colors changed')
                for width in [320,390,768,1024,1440]:
                    page.set_viewport_size({'width':width,'height':1000});page.wait_for_timeout(40)
                    assert frame.evaluate('document.documentElement.scrollWidth <= innerWidth'),(id,width,theme,palette)
                    if width in [390,1440]:page.screenshot(path=str(out/f'{id}-{theme}-{palette}-{width}.png'),full_page=True)
        assert frame.evaluate('localStorage.length===0 && sessionStorage.length===0')
    # Hold canvas encoding to prove cancellation prevents a late download.
    item=next(t for t in manifest['tools'] if t['id']=='pdf-flatten')
    frame=open_tool(item);frame.locator('#flatten-file-input').set_input_files(pdf)
    expect(frame.locator('#flatten-btn')).to_be_enabled(timeout=20000)
    cancelled_downloads=[]
    page.on('download',lambda download:cancelled_downloads.append(download.suggested_filename))
    frame.evaluate('''const nativeDownload=ToolUtils.downloadBlob;window.downloadHeld=false;ToolUtils.downloadBlob=(...args)=>{window.downloadHeld=true;setTimeout(()=>nativeDownload(...args),2000)}''')
    frame.locator('#flatten-btn').click()
    frame.wait_for_function('window.downloadHeld')
    page.get_by_role('button',name='取消并清空',exact=True).click()
    expect(page.locator('.xcpdf-frame-wrap')).to_have_attribute('aria-busy','false')
    frame=page.frames[-1];assert frame.locator('#flatten-file-input').input_value()==''
    page.wait_for_timeout(2200)
    assert not cancelled_downloads,cancelled_downloads
    assert not remote,remote
    assert not errors,errors
    browser.close()
    assert not failures, failures
print('43 XCPDF routes: real files and exports, PDF structure, ZIP/text/images, encryption round trip, 5 widths, 4 themes and isolated state passed.')
