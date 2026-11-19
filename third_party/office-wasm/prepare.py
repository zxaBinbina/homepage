#!/usr/bin/env python3
"""Prepare the independently licensed static viewer from verified upstream files.

SPDX-License-Identifier: AGPL-3.0-or-later
Usage: python3 third_party/office-wasm/prepare.py /path/to/downloads
Inputs and hashes are recorded in manifest.json. No documents are inputs to this script.
"""
import hashlib
import gzip
import json
import pathlib
import re
import shutil
import subprocess
import tarfile
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent


def digest(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def prepare(downloads):
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    for name, expected in manifest['inputs'].items():
        if digest(downloads / name) != expected['sha256']:
            raise ValueError(f'Upstream input checksum mismatch: {name}')
    temp = ROOT.parents[1] / '.cache/office-wasm-prepare'
    temp.mkdir(parents=True, exist_ok=True)
    upstream = temp / 'upstream'
    upstream.mkdir(exist_ok=True)
    with tarfile.open(ROOT / 'viewer-source.tar.gz') as archive:
        archive.extractall(upstream, filter='data')
    source = next(upstream.iterdir())
    site = temp / 'site'
    if site.exists():
        shutil.rmtree(site)
    site.mkdir(exist_ok=True)
    keep_fonts = re.compile(r'^(Arimo|Tinos|Carlito|Cousine)-.+\.ttf$')
    with zipfile.ZipFile(downloads / 'onlyoffice-editor.zip') as archive:
        for entry in archive.infolist():
            rel = entry.filename
            if entry.is_dir() or rel.endswith(('.map', '.br')):
                continue
            if '/resources/help/' in rel or '/forms/' in rel:
                continue
            if rel.startswith(('sdkjs/visio/', 'sdkjs/pdf/', 'web-apps/vendor/monaco/', 'dictionaries/')):
                continue
            language = re.search(r'/locale/([^/]+)\.json$', rel)
            if language and language[1] not in ('zh', 'en'):
                continue
            if rel.startswith('fonts/fonts/') and not keep_fonts.match(pathlib.Path(rel).name):
                continue
            dest = site / 'oo' / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(archive.read(entry))
    for name in ('Regular', 'Bold'):
        shutil.copyfile(downloads / f'NotoSansCJKsc-{name}.otf', site / 'oo/fonts/fonts' / f'NotoSansCJKsc-{name}.otf')
    all_fonts = site / 'oo/sdkjs/common/AllFonts.js'
    subprocess.run(['node', '-e', r'''
const fs = require('node:fs'), path = require('node:path');
const [src, file] = process.argv.slice(1);
const {parse,removeFonts,addFonts,addLocalFontsHook} = require(path.join(src,'fonts/font-pack.cjs'));
const {addFontAliases} = require(path.join(src,'fonts/font-aliases.cjs'));
let js = fs.readFileSync(file,'utf8');
const allowed = ['Arimo','Tinos','Carlito','Cousine'];
js = removeFonts(js,parse(js).infos.map(i=>i[0]).filter(n=>!allowed.includes(n))).js;
js = addFonts(js,[{name:'Noto Sans CJK SC',cloneFrom:'Arimo',files:{Regular:'NotoSansCJKsc-Regular.otf',Bold:'NotoSansCJKsc-Bold.otf'}}]);
js = addFontAliases(js);
js = addFontAliases(js,{'Microsoft YaHei':'Noto Sans CJK SC','微软雅黑':'Noto Sans CJK SC','SimSun':'Noto Sans CJK SC','宋体':'Noto Sans CJK SC','SimHei':'Noto Sans CJK SC','黑体':'Noto Sans CJK SC'});
fs.writeFileSync(file,addLocalFontsHook(js));
''', str(source), str(all_fonts)], check=True)
    for directory in ('x2t', 'fonts/math'):
        shutil.copytree(source / directory, site / directory, dirs_exist_ok=True)
    for rel in ('fonts/math-compat.mjs', 'fonts/local-fonts.mjs'):
        shutil.copyfile(source / rel, site / rel)
    engine = site / 'wasm/prebuilt'
    engine.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(downloads / 'x2t.zip') as archive:
        for name in ('x2t.js', 'x2t.wasm.br'):
            (engine / name).write_bytes(archive.read(name))
    # CryptPad's native UI expects this file at the editor root.
    shutil.copyfile(site / 'oo/web-apps/apps/common/main/resources/themes/themes.json', site / 'oo/themes.json')
    for app in ('documenteditor', 'spreadsheeteditor', 'presentationeditor'):
        file = site / f'oo/web-apps/apps/{app}/main/index.html'
        html = file.read_text()
        html = re.sub(r'^\+function registerServiceWorker\(\).*$', '', html, flags=re.M)
        html = html.replace('<head>', '<head>\n<script src="../../../../../privacy.js"></script>', 1)
        file.write_text(html)
    (site / 'fonts-manifest.json').write_text(json.dumps({'base': 'oo/fonts/fonts/', 'files': sorted(f.name for f in (site / 'oo/fonts/fonts').iterdir())}))
    (site / 'x2t-info.json').write_text(json.dumps({'coi': False, 'prebuilt': True, 'st': False, 'mt': False, 'apps': ['word', 'cell', 'slide']}))
    # Package engine resources only. The build overlays the reviewable viewer sources.
    packed = temp / 'runtime.tar.gz'
    files = sorted(f for f in site.rglob('*') if f.is_file())
    with packed.open('wb') as stream, gzip.GzipFile(filename='', fileobj=stream, mode='wb', mtime=0) as compressed, tarfile.open(fileobj=compressed, mode='w') as archive:
        for file in files:
            info = archive.gettarinfo(file, arcname=file.relative_to(site).as_posix())
            info.mtime = 0
            info.uid = info.gid = 0
            info.uname = info.gname = ''
            with file.open('rb') as stream:
                archive.addfile(info, stream)
    parts = []
    with packed.open('rb') as stream:
        index = 0
        while chunk := stream.read(20 * 1024 * 1024):
            name = f'runtime-{index:02}.tar.gz.part'
            file = ROOT / name
            file.write_bytes(chunk)
            parts.append({'file': name, 'sha256': digest(file), 'bytes': len(chunk)})
            index += 1
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    manifest['runtime'] = parts
    manifest['assets'] = [{'file': f.relative_to(site).as_posix(), 'bytes': f.stat().st_size, 'sha256': digest(f)} for f in files]
    (ROOT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'{len(files)} resources, {sum(f.stat().st_size for f in files) / 1048576:.1f} MiB, {packed.stat().st_size / 1048576:.1f} MiB archived')


if __name__ == '__main__':
    import sys
    prepare(pathlib.Path(sys.argv[1]).resolve())
