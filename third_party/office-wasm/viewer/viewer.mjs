// office-wasm viewer: offline preview and conversion of Office files, entirely in the browser.
//   file -> x2t.wasm (worker) -> Editor.bin -> sdkjs/web-apps viewer, with no document server
//   PDF: sdkjs lays the document out and emits a "pdf.bin" command stream -> x2t.wasm writes the PDF
//
// This page is meant to run inside an <iframe>. The embedding page talks to it only with postMessage:
//   host -> viewer   {target: 'office-wasm-viewer', id, method, params}
//   viewer -> host   {source: 'office-wasm-viewer', id, ok: true, result} | {source, id, ok: false, error}
//   viewer -> host   {source: 'office-wasm-viewer', type: 'event', event, data}
// Methods: open {name, data, mode?: 'embedded'|'desktop'|'edit', localFonts?: [{family, style?, data}]}, exportPdf {},
//          save {to?} (edit mode: the edited file), convert {to, name?, data?}, fontNames {name, data} (fonts a file uses),
//          close {}, getState {}.
// localFonts: font files of the user's computer for the fonts the document uses (see fonts/local-fonts.mjs).
// Events:  ready, phase, log, editorError, editorWarning, pdf, modified {modified}.
// Opened directly (not in a frame) the page shows a file picker instead.
//
// SPDX-License-Identifier: AGPL-3.0-or-later
import { X2tClient } from './x2t/browser-client.mjs';
import { FORMAT, docTypeOf, extOf, mediaMimeOf } from './x2t/formats.mjs';
import { MathFonts } from './fonts/math-compat.mjs';
import { preparePackage, fontNamesOf, scanDocument } from './x2t/prepare-package.mjs';
import { prepareLocalFonts, installLocalFonts, LOCAL_PREFIX } from './fonts/local-fonts.mjs';

const VERSION = '0.2.0-homepage.2';
const TAG = 'office-wasm-viewer';
const ROOT = new URL('./', import.meta.url);
const query = new URLSearchParams(location.search);
const embedded = window.parent !== window;
const now = () => performance.now();
const ms = (t0) => Math.round(now() - t0);
const sourceUrl = document.querySelector('meta[name="office-wasm-viewer:source"]')?.content || '';
let uiTheme = query.get('theme') === 'dark' ? 'theme-night' : 'theme-white';

const state = { phase: 'idle', timings: {}, error: null, x2t: null };

// ---------- messaging ----------
// Origin of the embedding page: ?host=<origin> (set by the SDK), else the origin of the first request accepted.
let hostOrigin = query.get('host') || null;
function post(msg, transfer = []) {
  if (!embedded) return;
  // Before a request has been accepted only "ready" and start-up log lines are sent: nothing about a document.
  window.parent.postMessage({ source: TAG, ...msg }, hostOrigin && hostOrigin !== 'null' ? hostOrigin : '*', transfer);
}
function emit(event, data, transfer) {
  post({ type: 'event', event, data }, transfer);
}
function log(text) {
  if (!embedded) console.log('[viewer] ' + text);
  emit('log', text);
}
let emitSaveButton = () => {};
function setPhase(phase, error = null) {
  if (phase === 'ready') emitSaveButton();
  state.phase = phase;
  state.error = error;
  emit('phase', { phase, error });
}

// The CryptPad build of sdkjs looks for hooks on window.parent.APP (getImageURL, printPdf, ...).
window.APP = {
  // Called by sdkjs/common/AllFonts.js in the editor frame while it loads (hook added by tools/font-pack.cjs): adds the
  // fonts of the user's computer that were handed over with the document to the font list sdkjs reads next.
  localFonts(win) {
    const local = doc && doc.local;
    if (!local || !local.families.length) return;
    try {
      local.installed = installLocalFonts(win, local.families);
      log('fonts of this computer in the editor: ' + (local.installed.join(', ') || 'none (all in the pack)'));
    } catch (e) {
      log('local fonts not installed in the editor: ' + e.message);
    }
  },
};

// ---------- x2t ----------
// ?x2t=prebuilt|st|mt forces one build. Default: our single-threaded build (CryptPad's prebuilt one when ours is not
// there), upgraded to the multi-threaded build when this page is cross-origin isolated.
const x2tInfo = await fetch(new URL('x2t-info.json', ROOT)).then((r) => r.json()).catch(() => ({ prebuilt: true }));
const forced = query.get('x2t');
const baseOf = (name) => new URL('wasm/' + name + '/', ROOT).href;
const stName = forced && forced !== 'mt' ? forced : x2tInfo.st ? 'st' : 'prebuilt';
const useMt = forced ? forced === 'mt' : x2tInfo.mt;
const x2t = new X2tClient({
  workerUrl: new URL('x2t/x2t-worker.js', ROOT),
  x2tBase: baseOf(stName),
  x2tBaseMt: useMt ? baseOf('mt') : undefined,
  threads: query.get('threads') === null ? undefined : Number(query.get('threads')), // pool size of the mt build
});
const t0x2t = now();
const x2tReady = x2t.init().then(
  (r) => {
    state.timings.x2tInitMs = ms(t0x2t);
    state.x2t = { build: r.variant === 'mt' ? 'mt' : stName, threads: r.threads, crossOriginIsolated: !!globalThis.crossOriginIsolated };
    log(`x2t ready (${state.x2t.build}${r.threads ? ', ' + r.threads + ' threads' : ''}): wasm ${r.wasmMs} ms, init ${r.initMs} ms`);
  },
  (e) => log('x2t init failed: ' + e.message),
);

// ?mathFonts=embedded (default) | installed-first | off     see fonts/math-compat.mjs
const mathMode = query.get('mathFonts') || 'embedded';
const math = mathMode === 'off' ? null : new MathFonts(new URL('fonts/math/', ROOT).href, { preferInstalled: mathMode === 'installed-first' });

let editor = null;
let doc = null; // {name, ext, docType, bytes, editorBin, media, mediaUrls, binUrl}
let fontsLoaded = null;
let openSeq = 0;
let readyWaiter = null;

function editorApi() {
  const w = editor && editor.getIframe && editor.getIframe()?.contentWindow;
  return w && w.Asc ? { w, api: w.Asc.editor || w.editor } : null;
}

function disposeDoc() {
  if (readyWaiter) readyWaiter.reject(new Error('superseded'));
  readyWaiter = null;
  if (editor) {
    try { editor.destroyEditor(); } catch { /* the editor may not be initialised yet */ }
    editor = null;
  }
  if (doc) {
    clearInterval(doc.dirtyTimer);
    URL.revokeObjectURL(doc.binUrl);
    for (const u of Object.values(doc.mediaUrls)) URL.revokeObjectURL(u);
    doc = null;
  }
  document.getElementById('stage').innerHTML = '<div id="placeholder"></div>';
}

async function openDocument(name, bytes, mode = 'embedded', timeoutMs = 120000, localFonts = null) {
  if (!['embedded', 'desktop', 'edit'].includes(mode)) throw new Error('unsupported mode');
  const docType = docTypeOf(name);
  if (!docType) throw new Error('unsupported file type: ' + name);
  // A site packed for some editors only (tools/pack.mjs --apps) lists them in x2t-info.json: say so at once instead of timing out.
  if (Array.isArray(x2tInfo.apps) && !x2tInfo.apps.includes(docType)) throw new Error(`this viewer serves only ${x2tInfo.apps.join('/')} documents, not ${docType}: ${name}`);
  disposeDoc();
  const seq = ++openSeq;
  const stale = () => seq !== openSeq;
  setPhase('converting');
  state.timings = { x2tInitMs: state.timings.x2tInitMs };
  const ext = extOf(name);
  const t0 = now();
  let r;
  let tcvnFixed = 0;
  try {
    // x2t cannot read EMZ / WMZ pictures and the editor hides U+00AD (u with horn in TCVN3 text): fix the package first
    const prepared = await preparePackage(bytes);
    if (prepared.converted || prepared.tcvnFixed) {
      log(`package prepared: ${prepared.converted} EMZ/WMZ pictures unpacked, ${prepared.tcvnFixed} TCVN3 parts fixed`);
      bytes = prepared.bytes;
      tcvnFixed = prepared.tcvnFixed;
    }
    r = await x2t.convert({ name: 'input.' + ext, data: bytes, to: 'Editor.bin' });
    if (r.exitCode !== 0 || !r.output) throw Object.assign(new Error('x2t exit ' + r.exitCode), { log: r.log });
  } catch (e) {
    if (stale()) throw new Error('superseded');
    setPhase('error', e.message);
    log('x2t failed: ' + e.message + ' ' + JSON.stringify(e.log || ''));
    throw e;
  }
  if (stale()) throw new Error('superseded');
  state.timings.toEditorBinMs = ms(t0);
  // Blob URLs for the pictures; MathType equations (SVG made from WMF) get the substitute math fonts embedded.
  const mediaUrls = {};
  let mathPictures = 0;
  for (const [n, data] of Object.entries(r.media)) {
    let body = data;
    if (math && extOf(n) === 'svg') {
      const s = await math.svg(data).catch((e) => (log('math fonts: ' + e.message), null));
      if (s) {
        body = s;
        mathPictures++;
      }
    }
    mediaUrls[n] = URL.createObjectURL(new Blob([body], { type: mediaMimeOf(n) }));
  }
  if (stale()) {
    for (const u of Object.values(mediaUrls)) URL.revokeObjectURL(u);
    throw new Error('superseded');
  }
  let local = null;
  if (localFonts && localFonts.length) {
    local = prepareLocalFonts(localFonts, { vietnamese: (await scanDocument(bytes)).vietnamese });
    for (const s of local.skipped) log('local font skipped: ' + s);
    const restricted = local.families.filter((f, i) => !local.embeddable[i]).map((f) => f.name);
    if (restricted.length) log('local fonts shown but kept out of the PDF (licence flag "restricted"): ' + restricted.join(', '));
  }
  doc = {
    name, ext, docType, bytes, tcvnFixed, local, editable: mode === 'edit', imageCounter: 0,
    editorBin: r.output,
    media: r.media,
    mediaUrls,
    mathPictures,
    binUrl: URL.createObjectURL(new Blob([r.output], { type: 'application/octet-stream' })),
  };
  log(`${name} (${bytes.length} B) -> Editor.bin ${r.output.length} B, ${Object.keys(r.media).length} media files`
    + (mathPictures ? ` (${mathPictures} with substitute math fonts)` : '') + `; x2t ${r.convertMs} ms, total ${state.timings.toEditorBinMs} ms`);
  const ready = new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('document not ready after ' + timeoutMs + ' ms')), timeoutMs);
    readyWaiter = {
      resolve: (v) => { clearTimeout(timer); resolve(v); },
      reject: (e) => { clearTimeout(timer); reject(e); },
    };
  });
  mountEditor(mode);
  try {
    await ready;
  } catch (e) {
    if (!stale()) setPhase('error', e.message);
    throw e;
  }
  return describe();
}

// Single-user stand-in for the document server's save and lock protocol, enough for editing without a server:
// every lock is granted, every batch of changes is acknowledged. The changes stay in the editor; save() reads the
// document back from it. (Co-authoring, history and recovery do not exist here.)
const USER_ID = 'viewer1'; // config user id + index the auth message gives
function editServer() {
  let changesIndex = 0;
  const send = (msg) => editor && editor.sendMessageToOO(msg);
  return (m) => {
    switch (m && m.type) {
      case 'isSaveLock':
        send({ type: 'saveLock', saveLock: false });
        break;
      case 'getLock': {
        const locks = {};
        for (const b of m.block || []) locks[typeof b === 'object' ? b.guid : b] = { time: Date.now(), user: USER_ID, block: b };
        send({ type: 'getLock', locks });
        break;
      }
      case 'saveChanges':
        if (!state.modified) { state.modified = true; emit('modified', { modified: true }); }
        if (m.endSaveChanges === false) send({ type: 'savePartChanges', changesIndex });
        else send({ type: 'unSaveLock', index: ++changesIndex, time: Date.now(), syncChangesIndex: changesIndex });
        break;
      case 'unLockDocument':
        send({ type: 'unSaveLock', index: -1, time: -1, syncChangesIndex: -1 });
        break;
      default:
    }
  };
}

function mountEditor(mode) {
  const tOpen = now();
  setPhase('loading-editor');
  const edit = mode === 'edit';
  state.modified = false;
  const config = {
    // 'embedded' = light viewer, 'desktop' = full editor UI in view mode, 'edit' = full editor UI, editable
    type: mode === 'desktop' || edit ? 'desktop' : 'embedded',
    width: '100%',
    height: '100%',
    documentType: doc.docType,
    document: {
      fileType: doc.ext,
      key: 'k' + Date.now(),
      title: doc.name,
      url: doc.binUrl, // the mock server answers "documentOpen" with this URL as Editor.bin
      permissions: { edit, download: false, print: false, comment: false, review: false, copy: true, chat: false },
    },
    editorConfig: {
      mode: edit ? 'edit' : 'view',
      lang: 'zh',
      user: { id: 'viewer', name: '访客' },
      customization: { compactHeader: true, uiTheme, features: { featuresTips: false }, comments: false, help: false, plugins: false, feedback: false, autosave: false },
      embedded: { toolbarDocked: 'top' },
    },
    events: {
      onAppReady: () => {
        state.timings.appReadyMs = ms(tOpen);
        log(`editor app ready: ${state.timings.appReadyMs} ms`);
      },
      onDocumentReady: () => {
        state.timings.documentReadyMs = ms(tOpen);
        if (edit) installEditingBridge();
        if (doc.docType === 'word') editorApi()?.api.zoomFitToWidth?.();
        setPhase('ready');
        log(`document shown: ${state.timings.documentReadyMs} ms`);
        if (readyWaiter) readyWaiter.resolve();
        readyWaiter = null;
      },
      onError: (e) => {
        state.error = e && e.data;
        emit('editorError', e && e.data);
      },
      onWarning: (e) => emit('editorWarning', e && e.data),
      onDocumentStateChange: (e) => {
        if (edit) { state.modified = !!e.data; emit('modified', { modified: state.modified }); }
      },
    },
  };
  editor = new window.DocsAPI.DocEditor('placeholder', config);
  // Stand-in for the document server's co-authoring socket.
  editor.connectMockServer({
    getParticipants: () => ({
      index: 1,
      list: [{ id: 1, idOriginal: 'viewer', username: 'Viewer', indexUser: 1, connectionId: 'c1', isCloseCoAuthoring: false, view: !edit }],
    }),
    getImageURL: async (name) => doc?.mediaUrls[String(name).replace(/^.*[\\/]/, '')] || '',
    onMessage: edit ? editServer() : () => {},
  });
}

// Native image insertion uses this CryptPad hook instead of an upload server.
// Keep both the image bytes and the engine's URL mapping in this document's memory.
async function addLocalImage(file) {
  const active = doc;
  if (!active?.editable) throw new Error('no editable document');
  if (file.size > 10 * 1048576) throw new Error('image exceeds 10 MiB');
  const bitmap = await createImageBitmap(file);
  let blob = file;
  try {
    if (bitmap.width * bitmap.height > 16000000) throw new Error('image exceeds 16 megapixels');
    if (!['image/png', 'image/jpeg'].includes(file.type)) {
      const canvas = new OffscreenCanvas(bitmap.width, bitmap.height);
      canvas.getContext('2d').drawImage(bitmap, 0, 0);
      blob = await canvas.convertToBlob({ type: 'image/png' });
    }
  } finally { bitmap.close(); }
  const bytes = new Uint8Array(await blob.arrayBuffer());
  if (active !== doc) throw new Error('superseded');
  const size = Object.values(active.media).reduce((n, data) => n + data.length, 0);
  if (size + bytes.length > 60 * 1048576) throw new Error('image total exceeds 60 MiB');
  const name = 'inserted-' + Date.now() + '-' + (++active.imageCounter) + (blob.type === 'image/jpeg' ? '.jpg' : '.png');
  const url = URL.createObjectURL(blob);
  active.media[name] = bytes;
  active.mediaUrls[name] = url;
  editorApi().w.AscCommon.g_oDocumentUrls.addUrls({ ['media/' + name]: url });
  // CryptPad's native insertion callback registers res.name as the package image
  // ID. It displays res.url, and the binary writer resolves that URL back to name.
  return { url, name, path: 'media/' + name };
}
window.APP.UploadImageFiles = (files, _id, _user, _jwt, callback) => {
  Promise.all(Array.from(files).map(addLocalImage)).then(
    (images) => callback(0, images.map((image) => image.url)),
    () => callback(editorApi()?.w.Asc.c_oAscError.ID.UploadImageError || -1, []),
  );
};
window.APP.AddImage = (callback) => {
  const active = doc;
  const input = document.createElement('input');
  input.type = 'file'; input.accept = 'image/*'; input.hidden = true;
  document.body.append(input);
  input.addEventListener('cancel', () => input.remove(), { once: true });
  input.addEventListener('change', async () => {
    try {
      if (input.files[0]) {
        const image = await addLocalImage(input.files[0]);
        if (doc === active) callback(image);
      }
    } catch { emit('editorWarning', { message: '图片未能插入，请使用小于 10 MB 的有效图片。' }); }
    finally { input.remove(); }
  }, { once: true });
  input.click();
};
function installEditingBridge() {
  const { w, api } = editorApi();
  const active = doc;
  const markModified = () => {
    if (doc !== active || state.phase !== 'ready') return;
    if (!state.modified) { state.modified = true; emit('modified', { modified: true }); }
  };
  // Cell/text composition can be pending before the engine commits its history.
  // Mark user input immediately, and cover ribbon/drawing operations via history.
  w.addEventListener('input', markModified, true);
  w.addEventListener('paste', markModified, true);
  active.dirtyTimer = setInterval(() => {
    if (api.isDocumentModified?.() || w.AscCommon.History.Have_Changes()) markModified();
  }, 500);
  // Pasted data/blob images use the same local path. Remote images cannot cause
  // a document upload or an implicit external request.
  w.AscCommon.sendImgUrls = (_api, images, callback) => {
    Promise.all(images.map(async (url) => {
      if (!String(url).startsWith('data:image/') && !String(url).startsWith('blob:')) throw new Error('remote image is unavailable');
      return addLocalImage(await (await fetch(url)).blob());
    })).then(callback, () => callback(images.map(() => ({ url: 'error', path: '' }))));
  };
  w.addEventListener('keydown', (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
      event.preventDefault(); event.stopImmediatePropagation(); emit('saveRequested', {});
    }
  }, true);
  w.addEventListener('click', (event) => {
    if (event.target.closest?.('#id-toolbar-btn-save')) {
      event.preventDefault(); event.stopImmediatePropagation(); emit('saveRequested', {});
    }
  }, true);
  api.asc_registerCallback('asc_onDocumentModifiedChanged', () => {
    state.modified = api.isDocumentModified?.() !== false;
    emit('modified', { modified: state.modified });
  });
}

function describe() {
  const e = editorApi();
  let pages = null;
  try { pages = e && e.api && e.api.asc_getPageCount ? e.api.asc_getPageCount() : null; } catch { /* not every editor has pages */ }
  return {
    phase: state.phase,
    error: state.error,
    timings: { ...state.timings },
    x2t: state.x2t,
    document: doc ? { name: doc.name, docType: doc.docType, media: Object.keys(doc.media).length, mathPictures: doc.mathPictures } : null,
    localFonts: doc && doc.local ? { families: doc.local.families.map((f) => f.name), installed: doc.local.installed || [], notInPdf: doc.local.families.filter((f, i) => !doc.local.embeddable[i]).map((f) => f.name), skipped: doc.local.skipped } : null,
    editor: { api: !!(e && e.api), downloadAs: !!(e && e.api && e.api.asc_DownloadAs), pages },
  };
}

// ---------- PDF: sdkjs -> pdf.bin -> x2t -> PDF ----------
let pdfWaiter = null;
window.APP.printPdf = (dataContainer, cb) => {
  // Called by sdkjs inside the editor iframe with the rendered command stream.
  try { cb(null); } catch { /* only ends the "saving" action in the editor */ }
  const d = dataContainer && dataContainer.data;
  if (!ArrayBuffer.isView(d)) {
    log('printPdf: unexpected data type ' + Object.prototype.toString.call(d));
    if (pdfWaiter) pdfWaiter.reject(new Error('unexpected pdf.bin type'));
    return;
  }
  const copy = new Uint8Array(d.byteLength);
  copy.set(d);
  if (pdfWaiter) {
    pdfWaiter.resolve(copy);
    return;
  }
  // The viewer's own Print / Download button: hand the PDF to the host, or save it when there is no host.
  const name = doc.name.replace(/\.[^.]+$/, '') + '.pdf';
  buildPdf(copy).then(
    (pdf) => {
      if (embedded) emit('pdf', { name, data: pdf.bytes.buffer }, [pdf.bytes.buffer]);
      else download(pdf.bytes, name, 'application/pdf');
    },
    (e) => log('PDF failed: ' + e.message),
  );
};

async function ensureFonts() {
  if (!fontsLoaded) {
    fontsLoaded = (async () => {
      const t0 = now();
      const manifest = await (await fetch(new URL('fonts-manifest.json', ROOT))).json();
      const r = await x2t.loadFonts(new URL(manifest.base, ROOT).href, manifest.files);
      let n = r.loaded;
      let bytes = r.bytes;
      if (math) {
        await math.load();
        const m = await x2t.loadFonts(math.base, math.ttfFiles());
        n += m.loaded;
        bytes += m.bytes;
      }
      state.timings.fontsMs = ms(t0);
      log(`${n} fonts (${(bytes / 1048576).toFixed(1)} MB) loaded into x2t: ${state.timings.fontsMs} ms`);
    })();
    fontsLoaded.catch(() => { fontsLoaded = null; });
  }
  return fontsLoaded;
}

// The fonts of this computer that x2t needs for the PDF (not those that forbid embedding); the signature tells whether
// the ones in x2t are already the right ones.
let x2tLocalSig = '';
async function syncLocalFonts() {
  const files = {};
  const local = doc && doc.local;
  if (local) {
    local.families.forEach((fam, n) => {
      if (!local.embeddable[n]) return;
      for (const [style, bytes] of Object.entries(fam.styles)) files[LOCAL_PREFIX + n + '-' + style + '.ttf'] = bytes;
    });
  }
  const sig = Object.entries(files).map(([k, v]) => k + ':' + v.length).join('|');
  if (sig === x2tLocalSig) return;
  await x2t.setLocalFonts(Object.fromEntries(Object.entries(files).map(([k, v]) => [k, v.slice()])));
  x2tLocalSig = sig;
}

async function buildPdf(pdfBin) {
  await ensureFonts();
  await syncLocalFonts();
  const files = { 'pdf.bin': pdfBin };
  let mathPictures = 0;
  for (const [n, data] of Object.entries(doc.media)) {
    // x2t draws the WMF/EMF (not the SVG made from it): point its font records at the substitute math fonts
    const ext = extOf(n);
    const w = math ? (ext === 'wmf' ? math.wmf(data) : ext === 'emf' ? math.emf(data) : null) : null;
    if (w) mathPictures++;
    files['media/' + n] = w || data;
  }
  const r = await x2t.convert({ name: 'output.bin', data: doc.editorBin, to: 'output.pdf', formatTo: FORMAT.pdf, files });
  if (r.exitCode !== 0 || !r.output) throw new Error('x2t pdf exit=' + r.exitCode + ' ' + JSON.stringify(r.log));
  return { bytes: r.output, pdfBinBytes: pdfBin.length, x2tMs: r.convertMs, mathPictures };
}

async function exportPdf() {
  const e = editorApi();
  if (!doc || !e || !e.api || state.phase !== 'ready') throw new Error('no document is open');
  const { w, api } = e;
  const t0 = now();
  const pdfBin = await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('timed out waiting for pdf.bin')), 120000);
    pdfWaiter = {
      resolve: (v) => { clearTimeout(timer); resolve(v); },
      reject: (err) => { clearTimeout(timer); reject(err); },
    };
    // No "download event" flag => sdkjs takes the APP.printPdf branch instead of asking a server.
    const opts = new w.Asc.asc_CDownloadOptions(w.Asc.c_oAscFileType.PDF);
    if (doc.docType === 'cell') {
      const adjust = new w.Asc.asc_CAdjustPrint();
      adjust.asc_setPrintType(w.Asc.c_oAscPrintType.EntireWorkbook);
      opts.asc_setAdvancedOptions(adjust);
    }
    api.asc_DownloadAs(opts);
  }).finally(() => { pdfWaiter = null; });
  state.timings.pdfBinMs = ms(t0);
  const pdf = await buildPdf(pdfBin);
  state.timings.pdfTotalMs = ms(t0);
  log(`PDF: pdf.bin ${pdfBin.length} B (sdkjs ${state.timings.pdfBinMs} ms) -> ${pdf.bytes.length} B (x2t ${pdf.x2tMs} ms), total ${state.timings.pdfTotalMs} ms`);
  return pdf;
}

/** Read the edited document and its original/inserted images back into an Office file. */
async function saveDocument(to) {
  const e = editorApi();
  if (!doc || !e || !e.api || state.phase !== 'ready') throw new Error('no document is open');
  if (!doc.editable) throw new Error('document is read-only');
  // Commit a cell being edited (including its formula) before writing the workbook.
  if (doc.docType === 'cell' && e.api.asc_closeCellEditor && !e.api.asc_closeCellEditor()) throw new Error('请先完成当前单元格的编辑。');
  if (doc.docType === 'cell') e.api.wbModel?.dependencyFormulas?.calcTree();
  if (typeof e.api.asc_nativeGetFile !== 'function') throw new Error('this editor cannot return its document');
  const t0 = now();
  const text = e.api.asc_nativeGetFile();
  if (typeof text !== 'string' || !/^[A-Z]{4};v\d+;/.test(text)) throw new Error('unexpected editor output');
  const bin = new Uint8Array(text.length);
  for (let i = 0; i < text.length; i++) bin[i] = text.charCodeAt(i); // ASCII only
  const outExt = to ? (String(to).includes('.') ? extOf(String(to)) : String(to).toLowerCase()) : doc.ext;
  const outName = 'output.' + outExt;
  if (!FORMAT[outExt] || outExt === 'pdf') throw new Error('cannot save as ' + outExt);
  const files = {};
  for (const [n, data] of Object.entries(doc.media)) files['media/' + n] = data;
  const r = await x2t.convert({ name: 'Editor.bin', data: bin, to: outName, formatTo: FORMAT[outExt], files });
  if (r.exitCode !== 0 || !r.output) throw new Error('x2t save exit=' + r.exitCode + ' ' + JSON.stringify(r.log));
  if (r.output.length > 80 * 1048576) throw new Error('saved document exceeds 80 MiB');
  let bytes = r.output;
  if (doc.tcvnFixed && (outExt === 'docx' || outExt === 'pptx')) {
    bytes = (await preparePackage(bytes, { restore: true })).bytes; // U+F0AD back to U+00AD in the TCVN3 runs
  }
  e.w.AscCommon.History.Reset_SavedIndex(true);
  e.api.CheckChangedDocument();
  state.modified = false;
  emit('modified', { modified: false });
  state.timings.saveMs = ms(t0);
  log(`saved ${outName}: ${bin.length} B editor data -> ${bytes.length} B (x2t ${r.convertMs} ms), total ${state.timings.saveMs} ms`);
  return { bytes, name: doc.name.replace(/\.[^.]+$/, '') + '.' + outExt, x2tMs: r.convertMs };
}

/** x2t conversion that needs no layout (text, csv, other document formats). PDF goes through exportPdf. */
async function convert({ to, name, data }) {
  if (typeof to !== 'string' || !/^[\w.-]+$/.test(to)) throw new Error('bad output name');
  if (extOf(to) === 'pdf') throw new Error('PDF needs the layout engine: open the document and call exportPdf');
  const input = data ? { name: 'input.' + extOf(name || ''), data: new Uint8Array(data) } : doc ? { name: 'input.' + doc.ext, data: doc.bytes } : null;
  if (!input) throw new Error('no document is open');
  const t0 = now();
  const r = await x2t.convert({ ...input, to });
  if (r.exitCode !== 0 || !r.output) throw new Error('x2t exit=' + r.exitCode);
  log(`convert -> ${to}: ${r.output.length} B, ${ms(t0)} ms (x2t ${r.convertMs} ms)`);
  return { bytes: r.output, convertMs: r.convertMs, totalMs: ms(t0) };
}

// ---------- requests from the embedding page ----------
const methods = {
  async open(p) {
    return [await openDocument(String(p.name), new Uint8Array(p.data), p.mode, p.timeoutMs, p.localFonts)];
  },
  async fontNames(p) {
    return [await fontNamesOf(new Uint8Array(p.data))];
  },
  async exportPdf() {
    const pdf = await exportPdf();
    return [{ data: pdf.bytes.buffer, pdfBinBytes: pdf.pdfBinBytes, x2tMs: pdf.x2tMs, mathPictures: pdf.mathPictures, timings: { ...state.timings } }, [pdf.bytes.buffer]];
  },
  async save(p) {
    const r = await saveDocument(p.to);
    return [{ data: r.bytes.buffer, name: r.name, x2tMs: r.x2tMs, timings: { ...state.timings } }, [r.bytes.buffer]];
  },
  async convert(p) {
    const r = await convert(p);
    return [{ data: r.bytes.buffer, convertMs: r.convertMs, totalMs: r.totalMs }, [r.bytes.buffer]];
  },
  async close() {
    openSeq++;
    disposeDoc();
    setPhase('idle');
    return [null];
  },
  async getState() {
    return [describe()];
  },
  async theme(p) {
    uiTheme = p.light ? 'theme-white' : 'theme-night';
    editorApi()?.w.Common?.UI?.Themes?.setTheme(uiTheme);
    return [null];
  },
  async resize() {
    const w = editorApi()?.w;
    if (w) w.dispatchEvent(new w.Event('resize'));
    return [null];
  },
};

window.addEventListener('message', async (ev) => {
  if (!embedded || ev.source !== window.parent) return;
  const m = ev.data;
  if (!m || m.target !== TAG || typeof m.method !== 'string') return;
  if (hostOrigin === null) hostOrigin = ev.origin;
  else if (ev.origin !== hostOrigin) return;
  const fn = Object.hasOwn(methods, m.method) ? methods[m.method] : null;
  try {
    if (!fn) throw new Error('unknown method: ' + m.method);
    const [result, transfer] = await fn(m.params || {});
    post({ id: m.id, ok: true, result }, transfer);
  } catch (e) {
    post({ id: m.id, ok: false, error: String(e && e.message ? e.message : e) });
  }
});

// ---------- stand-alone use (page opened directly) ----------
function download(bytes, name, type) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([bytes], { type }));
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 60000);
}
if (!embedded) {
  const picker = document.getElementById('picker');
  picker.hidden = false;
  const openFile = async (f) => {
    picker.hidden = true;
    try {
      await openDocument(f.name, new Uint8Array(await f.arrayBuffer()), query.get('mode') || 'desktop');
    } catch (e) {
      picker.hidden = false;
      log('open failed: ' + e.message);
    }
  };
  if (query.get('mode') === 'edit') {
    const btn = document.createElement('button');
    btn.id = 'save';
    btn.textContent = 'Save';
    btn.style.cssText = 'position:fixed;right:12px;bottom:12px;z-index:10;padding:6px 14px;display:none';
    btn.addEventListener('click', () => saveDocument().then((r) => download(r.bytes, r.name, mediaMimeOf(r.name)), (e) => log('save failed: ' + e.message)));
    document.body.append(btn);
    emitSaveButton = () => { btn.style.display = 'block'; };
  }
  picker.querySelector('input').addEventListener('change', (ev) => ev.target.files[0] && openFile(ev.target.files[0]));
  document.addEventListener('dragover', (ev) => ev.preventDefault());
  document.addEventListener('drop', (ev) => {
    ev.preventDefault();
    if (ev.dataTransfer.files[0]) openFile(ev.dataTransfer.files[0]);
  });
}

await x2tReady;
emit('ready', { version: VERSION, x2t: state.x2t, source: sourceUrl, crossOriginIsolated: !!globalThis.crossOriginIsolated });
