/* eslint-env worker */
// Classic web worker that owns one x2t wasm instance.
// Messages in:  {id, type: 'init', base, threads}             base = URL prefix of x2t.js / x2t.wasm
//                                                             threads = pthread pool size (multi-threaded build only)
//               {id, type: 'fonts', base, files: [name]}      fetch fonts into /working/fonts (needed for PDF only)
//               {id, type: 'localFonts', files: {name: Uint8Array}}  replaces the fonts of the user's computer in /working/fonts
//               {id, type: 'convert', inputName, input, outputName, paramsXml, files: {relPath: Uint8Array}}
// Messages out: {id, ok: true, ...result} | {id, ok: false, error}
'use strict';

let M = null;
let initPromise = null;
const loadedFonts = new Set();
const logLines = [];

function init(base, threads) {
  if (initPromise) return initPromise;
  initPromise = new Promise((resolve, reject) => {
    const t0 = performance.now();
    let tWasm = t0;
    self.Module = {
      // Multi-threaded build only (ignored by the single-threaded one): x2t.js is loaded with importScripts,
      // so emscripten must be told which script its thread workers have to start from.
      mainScriptUrlOrBlob: base + 'x2t.js',
      pthreadPoolSize: threads | 0,
      print: (s) => logLines.push(String(s)),
      printErr: (s) => logLines.push(String(s)),
      // Take over wasm loading: streaming compile, and the URL does not depend on the worker location.
      instantiateWasm(imports, done) {
        // Pages limits individual assets to 25 MiB. HTTP Brotli decoding supplies the
        // original 38 MiB module to WebAssembly without publishing that oversized file.
        const url = base + 'x2t.wasm.br';
        const viaBuffer = () => fetch(url).then((r) => r.arrayBuffer()).then((b) => WebAssembly.instantiate(b, imports));
        const p = WebAssembly.instantiateStreaming ? WebAssembly.instantiateStreaming(fetch(url), imports).catch(viaBuffer) : viaBuffer();
        p.then((r) => {
          tWasm = performance.now();
          done(r.instance, r.module);
        }).catch(reject);
        return {};
      },
      onAbort: (what) => reject(new Error('x2t aborted: ' + what)),
      onRuntimeInitialized() {
        M = self.Module;
        for (const d of ['/tmp', '/working', '/working/media', '/working/fonts', '/working/themes']) {
          if (!M.FS.analyzePath(d).exists) M.FS.mkdir(d);
        }
        resolve({ wasmMs: Math.round(tWasm - t0), initMs: Math.round(performance.now() - t0) });
      },
    };
    try {
      importScripts(base + 'x2t.js');
    } catch (e) {
      reject(e);
    }
  });
  return initPromise;
}

function mkdirp(dir) {
  let cur = '';
  for (const part of dir.split('/').filter(Boolean)) {
    cur += '/' + part;
    if (!M.FS.analyzePath(cur).exists) M.FS.mkdir(cur);
  }
}

function listFiles(dir, prefix, out) {
  for (const name of M.FS.readdir(dir)) {
    if (name === '.' || name === '..') continue;
    const p = dir + '/' + name;
    if (M.FS.isDir(M.FS.stat(p).mode)) listFiles(p, prefix + name + '/', out);
    else out.push(prefix + name);
  }
  return out;
}

function cleanWorking() {
  const rm = (dir, keep) => {
    for (const name of M.FS.readdir(dir)) {
      if (name === '.' || name === '..' || (keep && keep.includes(name))) continue;
      const p = dir + '/' + name;
      if (M.FS.isDir(M.FS.stat(p).mode)) {
        rm(p);
        M.FS.rmdir(p);
      } else M.FS.unlink(p);
    }
  };
  rm('/working', ['fonts']);
  rm('/tmp');
  mkdirp('/working/media');
  mkdirp('/working/themes');
}

async function loadFonts(base, files) {
  let bytes = 0;
  const todo = files.filter((f) => !loadedFonts.has(f));
  await Promise.all(todo.map(async (f) => {
    const r = await fetch(base + f);
    if (!r.ok) throw new Error('font HTTP ' + r.status + ': ' + f);
    const data = new Uint8Array(await r.arrayBuffer());
    M.FS.writeFile('/working/fonts/' + f, data);
    loadedFonts.add(f);
    bytes += data.length;
  }));
  return { loaded: todo.length, bytes, total: loadedFonts.size };
}

const LOCAL_FONT_PREFIX = 'local-font-';

/** Font files of the user's computer (the document's own fonts): replaces the ones of the previous document. */
function setLocalFonts(files) {
  const dir = '/working/fonts';
  const FS = M.FS;
  if (FS.analyzePath(dir).exists) for (const f of FS.readdir(dir)) if (f.startsWith(LOCAL_FONT_PREFIX)) FS.unlink(dir + '/' + f);
  let bytes = 0;
  for (const [name, data] of Object.entries(files || {})) {
    if (!name.startsWith(LOCAL_FONT_PREFIX) || name.includes('/')) throw new Error('bad local font name: ' + name);
    FS.writeFile(dir + '/' + name, data);
    bytes += data.length;
  }
  return { count: Object.keys(files || {}).length, bytes };
}

function convert(msg) {
  const FS = M.FS;
  cleanWorking();
  logLines.length = 0;
  const inputs = new Set();
  FS.writeFile('/working/' + msg.inputName, msg.input);
  for (const [rel, data] of Object.entries(msg.files || {})) {
    if (rel.includes('..')) throw new Error('bad file path: ' + rel);
    const full = '/working/' + rel;
    mkdirp(full.slice(0, full.lastIndexOf('/')));
    FS.writeFile(full, data);
    inputs.add(rel);
  }
  FS.writeFile('/working/params.xml', msg.paramsXml);
  const t0 = performance.now();
  const exitCode = M.ccall('main1', 'number', ['string'], ['/working/params.xml']);
  const convertMs = Math.round(performance.now() - t0);
  const outPath = '/working/' + msg.outputName;
  let output = null;
  if (FS.analyzePath(outPath).exists && !FS.isDir(FS.stat(outPath).mode)) output = FS.readFile(outPath);
  // media extracted by x2t next to the output (images of the document)
  const media = {};
  if (FS.analyzePath('/working/media').exists) {
    for (const rel of listFiles('/working/media', '', [])) {
      if (!inputs.has('media/' + rel)) media[rel] = FS.readFile('/working/media/' + rel);
    }
  }
  const transfer = [];
  if (output) transfer.push(output.buffer);
  for (const d of Object.values(media)) transfer.push(d.buffer);
  return [{ exitCode, convertMs, output, media, log: logLines.slice(-20) }, transfer];
}

self.onmessage = async (ev) => {
  const msg = ev.data;
  try {
    if (msg.type === 'init') {
      self.postMessage({ id: msg.id, ok: true, ...(await init(msg.base, msg.threads)) });
    } else if (msg.type === 'fonts') {
      await initPromise;
      self.postMessage({ id: msg.id, ok: true, ...(await loadFonts(msg.base, msg.files)) });
    } else if (msg.type === 'localFonts') {
      await initPromise;
      self.postMessage({ id: msg.id, ok: true, ...setLocalFonts(msg.files) });
    } else if (msg.type === 'convert') {
      await initPromise;
      const [result, transfer] = convert(msg);
      self.postMessage({ id: msg.id, ok: true, ...result }, transfer);
    } else {
      throw new Error('unknown message type: ' + msg.type);
    }
  } catch (e) {
    // After an abort inside the wasm the instance is unusable: the client must create a new worker.
    self.postMessage({ id: msg.id, ok: false, error: String(e && e.message ? e.message : e), log: logLines.slice(-20) });
  }
};
