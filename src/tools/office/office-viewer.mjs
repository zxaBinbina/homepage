// SPDX-License-Identifier: Apache-2.0
// Adapted for homepage: sandboxed frame, local editing and complete startup cancellation.
// Host-side SDK for the office-wasm viewer.
//
// The viewer (x2t.wasm + sdkjs, AGPL-3.0) runs in an <iframe>, preferably on its own origin. This module only
// creates that frame and exchanges messages with it; it contains no code of the viewer, so an application that
// uses it is a separate program that talks to the viewer over postMessage.
//
//   import { OfficeViewer } from './office-viewer.mjs';
//   const viewer = await OfficeViewer.create(document.getElementById('box'), { url: 'https://viewer.example/' });
//   viewer.on('log', (line) => console.log(line));
//   await viewer.open({ name: 'a.docx', data: arrayBuffer });          // shows the document
//   const { data } = await viewer.exportPdf();                         // Uint8Array with the PDF
//   await viewer.open({ name: 'a.docx', data, mode: 'edit' });         // editable; viewer.on('modified', ...) then
//   const saved = await viewer.save();                                 // {data, name}: the edited .docx
//   const txt = await viewer.convert({ to: 'out.txt' });               // x2t conversion without layout
//   await viewer.enableLocalFonts();                                    // in a click handler (Chromium asks the user)
//   await viewer.open({ name: 'a.docx', data, localFonts: true });      // layout with the fonts of this computer
//
// The viewer page needs COOP/COEP only for its multi-threaded build: create the frame from a cross-origin isolated
// page and serve the viewer with COEP + CORP (tools/serve.cjs --coi); the frame gets allow="cross-origin-isolated".
const TAG = 'office-wasm-viewer';

export class OfficeViewer {
  /**
   * Creates the frame and waits until the viewer has started.
   * @param {HTMLElement} container
   * @param {{url: string, timeoutMs?: number, title?: string, params?: Record<string, string>}} opts
   *   url: address of the viewer page; params: extra query parameters for it (x2t, threads, mathFonts)
   */
  static async create(container, opts) {
    const v = new OfficeViewer(container, opts);
    await v.ready;
    return v;
  }

  constructor(container, { url, timeoutMs = 60000, title = 'Document viewer', params = {} }) {
    const u = new URL(url, location.href);
    for (const [k, val] of Object.entries(params)) if (val !== undefined && val !== null && val !== '') u.searchParams.set(k, String(val));
    u.searchParams.set('host', location.origin); // the viewer answers only this origin
    this.origin = u.origin;
    this.listeners = new Map();
    this.pending = new Map();
    this.seq = 0;
    this.info = null;
    this.localFontList = null;
    this.iframe = document.createElement('iframe');
    this.iframe.title = title;
    this.iframe.sandbox = 'allow-scripts allow-same-origin';
    this.iframe.allow = 'fullscreen; clipboard-read; clipboard-write';
    this.iframe.referrerPolicy = 'no-referrer';
    this.iframe.style.cssText = 'border:0;width:100%;height:100%;display:block';
    this.ready = new Promise((resolve, reject) => {
      this.readyReject = reject;
      this.readyTimer = setTimeout(() => reject(new Error('viewer did not start within ' + timeoutMs + ' ms')), timeoutMs);
      this.readyWaiter = (info) => {
        clearTimeout(this.readyTimer);
        this.readyReject = null;
        resolve(info);
      };
    });
    this.onMessage = (ev) => this.#receive(ev);
    window.addEventListener('message', this.onMessage);
    this.iframe.src = u.href;
    container.appendChild(this.iframe);
  }

  #receive(ev) {
    if (!this.iframe || ev.source !== this.iframe.contentWindow || ev.origin !== this.origin) return;
    const m = ev.data;
    if (!m || m.source !== TAG) return;
    if (m.type === 'event') {
      if (m.event === 'ready') {
        this.info = m.data;
        if (this.readyWaiter) this.readyWaiter(m.data);
        this.readyWaiter = null;
      }
      for (const fn of this.listeners.get(m.event) || []) {
        try { fn(m.data); } catch (e) { console.error(e); }
      }
      return;
    }
    const p = this.pending.get(m.id);
    if (!p) return;
    this.pending.delete(m.id);
    if (m.ok) p.resolve(m.result);
    else p.reject(new Error(m.error));
  }

  /** @param {'ready'|'phase'|'log'|'editorError'|'editorWarning'|'pdf'|'modified'} event  modified: {modified: boolean}, edit mode only */
  on(event, fn) {
    if (!this.listeners.has(event)) this.listeners.set(event, new Set());
    this.listeners.get(event).add(fn);
    return () => this.listeners.get(event).delete(fn);
  }

  call(method, params = {}, transfer = []) {
    if (!this.iframe) return Promise.reject(new Error('viewer destroyed'));
    return new Promise((resolve, reject) => {
      const id = ++this.seq;
      this.pending.set(id, { resolve, reject });
      this.iframe.contentWindow.postMessage({ target: TAG, id, method, params }, this.origin, transfer);
    });
  }

  /**
   * Converts and shows a document. Resolves when it is displayed.
   * @param {{name: string, data: ArrayBuffer|Uint8Array, mode?: 'embedded'|'desktop'|'edit', timeoutMs?: number,
   *   localFonts?: true|{family: string, style?: string, data: ArrayBuffer|Uint8Array}[]}} doc
   *   name: file name (its extension picks the format); the data is copied, not transferred.
   *   mode: 'embedded' light viewer, 'desktop' full editor UI read-only, 'edit' full editor UI, editable (see save())
   *   localFonts: true = font files of this computer for the fonts the document uses (enableLocalFonts() first);
   *   or font files you supply yourself ({family: name as in the document, style: 'Regular'|'Bold'|'Italic'|'Bold Italic', data}).
   *   They show the document as Word does and go into the PDF, except fonts whose licence flag forbids embedding.
   */
  async open({ name, data, mode = 'embedded', timeoutMs, localFonts }) {
    let fonts = [];
    if (localFonts === true) {
      try {
        fonts = await this.localFontsFor(await this.fontNames({ name, data }));
      } catch (e) {
        console.warn('office-viewer: local fonts not used: ' + e.message); // the document opens with the fonts of the pack
      }
    } else if (Array.isArray(localFonts)) {
      fonts = localFonts;
    }
    const files = fonts.map((f) => ({ family: f.family, style: f.style, data: copyBuffer(f.data) }));
    return this.call('open', { name, data: copyBuffer(data), mode, timeoutMs, localFonts: files }, files.map((f) => f.data));
  }

  /** Names of the fonts a Word / PowerPoint / Excel file uses. @returns {Promise<string[]>} */
  fontNames({ name, data }) {
    return this.call('fontNames', { name, data: copyBuffer(data) });
  }

  /**
   * Reads the list of fonts installed on this computer (Local Font Access API: Chromium, secure context; the browser asks
   * the user for permission, usually only inside a click handler). Needed once before open({localFonts: true}).
   * Only the list is read here; font files are read for the fonts a document uses.
   * @returns {Promise<number>} number of font faces
   */
  async enableLocalFonts() {
    if (typeof window.queryLocalFonts !== 'function') throw new Error('this browser has no Local Font Access API (Chromium only)');
    this.localFontList = await window.queryLocalFonts();
    return this.localFontList.length;
  }

  /**
   * The installed fonts with these family names (or full names), as {family, style, data} for open({localFonts}).
   * @param {string[]} names font names as the document spells them
   */
  async localFontsFor(names) {
    if (!this.localFontList) await this.enableLocalFonts();
    const spelling = new Map(names.map((n) => [n.toLowerCase(), n]));
    const out = [];
    let total = 0;
    for (const f of this.localFontList) {
      const byFamily = spelling.get(String(f.family).toLowerCase());
      const byFull = byFamily ? null : spelling.get(String(f.fullName).toLowerCase());
      if (!byFamily && !byFull) continue;
      const blob = await f.blob();
      total += blob.size;
      if (blob.size > 64 * 1048576 || total > 256 * 1048576) continue; // CJK fonts are big: a document should not cost the browser a gigabyte
      out.push({ family: byFamily || byFull, style: byFamily ? f.style : 'Regular', data: await blob.arrayBuffer() });
    }
    return out;
  }

  /** @returns {Promise<{data: Uint8Array, pdfBinBytes: number, x2tMs: number, mathPictures: number, timings: object}>} */
  async exportPdf() {
    const r = await this.call('exportPdf');
    return { ...r, data: new Uint8Array(r.data) };
  }

  /**
   * Edit mode: the document as it is now, written as an Office file by x2t. Single user, no server: nothing is saved
   * until this is called. Original and locally inserted pictures are included by this deployment.
   * @param {{to?: string}} [opts] to: output file name or extension (docx, xlsx, pptx ...); default: the format opened
   * @returns {Promise<{data: Uint8Array, name: string, x2tMs: number, timings: object}>}
   */
  async save({ to } = {}) {
    const r = await this.call('save', { to });
    return { ...r, data: new Uint8Array(r.data) };
  }

  /**
   * x2t conversion that needs no layout: of the open document, or of {name, data} when given.
   * @param {{to: string, name?: string, data?: ArrayBuffer|Uint8Array}} job  to: output file name, e.g. "out.txt"
   */
  async convert({ to, name, data }) {
    const r = await this.call('convert', { to, name, data: data ? copyBuffer(data) : undefined });
    return { ...r, data: new Uint8Array(r.data) };
  }

  close() {
    return this.call('close');
  }

  getState() {
    return this.call('getState');
  }

  destroy() {
    clearTimeout(this.readyTimer);
    this.readyReject?.(new Error('viewer destroyed'));
    this.readyReject = null;
    this.readyWaiter = null;
    window.removeEventListener('message', this.onMessage);
    for (const p of this.pending.values()) p.reject(new Error('viewer destroyed'));
    this.pending.clear();
    this.listeners.clear();
    this.iframe?.remove();
    this.iframe = null;
  }
}

function copyBuffer(data) {
  const u8 = data instanceof Uint8Array ? data : new Uint8Array(data);
  return u8.slice().buffer;
}
