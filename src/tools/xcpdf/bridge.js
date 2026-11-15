/* XCPDF MIT release adapter: isolate state and synchronize the website theme. */
;(function () {
  let generation = -1
  let requestId = 0
  const copies = new Map()
  const urls = new Set()
  const workers = new Set()
  const memoryStorage = () => {
    const values = new Map()
    return {
      getItem: (key) => values.get(String(key)) ?? null,
      setItem: (key, value) => values.set(String(key), String(value)),
      removeItem: (key) => values.delete(String(key)),
      clear: () => values.clear(),
      key: (index) => [...values.keys()][index] ?? null,
      get length() {
        return values.size
      },
    }
  }
  // The opaque sandbox has no site storage. Upstream favorites can initialize,
  // but cannot persist or access the homepage's data.
  Object.defineProperty(window, 'localStorage', { value: memoryStorage() })
  Object.defineProperty(window, 'sessionStorage', { value: memoryStorage() })
  const post = (type, data = {}) => parent.postMessage({ type, generation, ...data }, '*')
  const nativeCreate = URL.createObjectURL.bind(URL)
  const nativeRevoke = URL.revokeObjectURL.bind(URL)
  URL.createObjectURL = (blob) => {
    const url = nativeCreate(blob)
    urls.add(url)
    return url
  }
  URL.revokeObjectURL = (url) => {
    urls.delete(url)
    nativeRevoke(url)
  }
  const NativeWorker = window.Worker
  window.Worker = class extends NativeWorker {
    constructor(...args) {
      super(...args)
      workers.add(this)
    }
    terminate() {
      workers.delete(this)
      super.terminate()
    }
  }
  addEventListener('pagehide', () => {
    for (const worker of workers) worker.terminate()
    for (const url of urls) nativeRevoke(url)
    for (const pending of copies.values()) pending.reject(new Error('工具已关闭'))
    copies.clear()
  })
  const copy = (text) =>
    new Promise((resolve, reject) => {
      const request = ++requestId
      const timer = setTimeout(() => {
        copies.delete(request)
        reject(new Error('复制未完成，请重试'))
      }, 5000)
      copies.set(request, { resolve, reject, timer })
      post('xcpdf:copy', { text: String(text), request })
    })
  Object.defineProperty(navigator, 'clipboard', { value: { writeText: copy } })
  const nativeExec = document.execCommand.bind(document)
  document.execCommand = (command, ...args) => {
    if (command !== 'copy') return nativeExec(command, ...args)
    const active = document.activeElement
    const text = active && 'value' in active ? active.value : getSelection()?.toString() || ''
    void copy(text).catch(() =>
      post('xcpdf:error', { message: '复制失败，请检查浏览器的剪贴板权限。' }),
    )
    return true
  }
  function reportHeight() {
    const container = document.querySelector('.main-container')
    if (container)
      post('xcpdf:height', { height: Math.ceil(container.getBoundingClientRect().height) + 2 })
  }
  function themeInlineStyle(element) {
    if (!(element instanceof HTMLElement) || element.closest('svg')) return
    const documentColor = element.matches('canvas, img, .color-preset, .color-swatch, .bm-preset')
    for (const property of [...element.style]) {
      if (!/color|background|border|outline|shadow/.test(property)) continue
      if (documentColor && property.startsWith('background')) continue
      if (element.matches('.bm-title') && property === 'color') continue
      const value = element.style.getPropertyValue(property)
      const themed = xcpdfUiValue(value, property, xcpdfUiColors)
      if (themed !== value)
        element.style.setProperty(property, themed, element.style.getPropertyPriority(property))
    }
  }
  function themeInlineTree(root) {
    if (!(root instanceof HTMLElement)) return
    themeInlineStyle(root)
    for (const element of root.querySelectorAll('[style]')) themeInlineStyle(element)
  }
  const tokens = new Set([
    '--bg',
    '--card-bg',
    '--primary',
    '--action-bg',
    '--primary-hover',
    '--text',
    '--text-secondary',
    '--border',
    '--danger',
    '--action-text',
    '--preview-h',
    '--success',
    '--panel-hover',
    '--shadow-color',
    '--scrollbar-thumb',
    '--scrollbar-thumb-hover',
    '--scrollbar-track',
    '--selection-bg',
  ])
  let enginePatched = false
  let booted = false
  addEventListener('DOMContentLoaded', () => {
    booted = true
    themeInlineTree(document.body)
    // Upstream also assigns inline colors while importing files and rendering results.
    // Normalize those UI updates once, leaving controls and PDF pixels in their chosen colors.
    new MutationObserver((records) => {
      const changed = new Set()
      for (const record of records) {
        if (record.type === 'attributes') changed.add(record.target)
        else for (const node of record.addedNodes) changed.add(node)
      }
      for (const node of changed) themeInlineTree(node)
    }).observe(document.body, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ['style'],
    })
  })
  function patchEngine() {
    if (enginePatched) return
    enginePatched = true
    const load = PDFLib.PDFDocument.load
    PDFLib.PDFDocument.load = async function (...args) {
      const pdf = await load.apply(this, args)
      // A legal blank PDF page may omit Contents. The bundled embedder expects
      // a stream even for blank pages; add an empty stream without changing ink.
      for (const page of pdf.getPages()) {
        if (!page.node.get(PDFLib.PDFName.of('Contents')))
          page.node.set(
            PDFLib.PDFName.of('Contents'),
            pdf.context.register(pdf.context.flateStream('')),
          )
      }
      return pdf
    }
  }
  addEventListener('message', (event) => {
    if (event.source !== parent) return
    const data = event.data
    if (data?.type === 'xcpdf:copied') {
      if (data.generation !== generation) return
      const pending = copies.get(data.request)
      if (!pending) return
      clearTimeout(pending.timer)
      copies.delete(data.request)
      if (data.success) pending.resolve()
      else pending.reject(new Error('复制失败，请检查剪贴板权限'))
    } else if (data?.type === 'xcpdf:init') {
      if (!booted) return
      const panel = document.getElementById(data.panel)
      if (!panel?.classList.contains('tab-panel') || ['tab-home', 'tab-about'].includes(data.panel))
        return
      generation = data.generation
      patchEngine()
      for (const [key, value] of Object.entries(data.tokens || {}))
        if (tokens.has(key) && typeof value === 'string')
          document.documentElement.style.setProperty(key, value)
      document.documentElement.style.colorScheme = data.theme === 'light' ? 'light' : 'dark'
      if (!panel.hasAttribute('data-current')) {
        document.querySelector(`.tool-card[data-target="${data.panel}"]`)?.click()
        for (const item of document.querySelectorAll('.tab-panel')) {
          item.toggleAttribute('data-current', item === panel)
          item.inert = item !== panel
        }
        if (panel.id === 'tab-unlock') {
          const button = panel.querySelector('#unlock-btn')
          const status = panel.querySelector('#unlock-status')
          const guard = () => {
            if (status.textContent.startsWith('正在检测') && !button.disabled)
              button.disabled = true
          }
          new MutationObserver(guard).observe(panel, {
            subtree: true,
            childList: true,
            characterData: true,
            attributes: true,
            attributeFilter: ['disabled'],
          })
        }
        // Only initial UI text changes; file names, inputs and document ink stay intact.
        const walker = document.createTreeWalker(panel, NodeFilter.SHOW_TEXT)
        while (walker.nextNode()) {
          const node = walker.currentNode
          if (node.parentElement?.closest('textarea, svg')) continue
          const cleaned = node.textContent
            .replace(/([0-9])\uFE0F?\u20E3/g, '$1. ')
            .replace(/\p{Extended_Pictographic}(?:\uFE0F|\u200D\p{Extended_Pictographic})*/gu, '')
          if (cleaned.trim()) node.textContent = cleaned
        }
        // Replace decorative control icons with readable labels while keeping document colors.
        for (const input of panel.querySelectorAll('input, select, textarea')) {
          if (input.labels?.length || input.getAttribute('aria-label')) continue
          const group = input.closest('.config-row, .opt-group, .range-row, .upload-area')
          const label =
            group?.querySelector('.config-label, .primary-text')?.textContent ||
            input.parentElement?.querySelector('span')?.textContent ||
            input.placeholder ||
            input.id ||
            '选项'
          input.setAttribute('aria-label', label.trim().slice(0, 80))
        }
        for (const input of panel.querySelectorAll('input[id$="pwd"]')) {
          input.type = 'password'
          input.autocomplete = 'new-password'
        }
        for (const swatch of panel.querySelectorAll(
          'span.color-preset, div.color-swatch, span.color-swatch',
        )) {
          swatch.setAttribute('role', 'button')
          swatch.tabIndex = 0
          swatch.setAttribute(
            'aria-label',
            swatch.title || `选择颜色 ${swatch.dataset.color || ''}`,
          )
        }
        for (const button of panel.querySelectorAll('button')) {
          const text = button.textContent.trim()
          if (/^[◀▶↪↩🔍×]+\uFE0F?$/.test(text))
            button.setAttribute(
              'aria-label',
              text.includes('◀')
                ? '上一页'
                : text.includes('▶')
                  ? '下一页'
                  : button.title || '预览页面',
            )
        }
      }
      reportHeight()
      post('xcpdf:ready')
    }
  })
  // Bound memory use before any original file handler sees the new input.
  document.addEventListener(
    'change',
    (event) => {
      if (event.target.type !== 'file') return
      if ([...(event.target.files || [])].some((file) => file.size > 30 * 1024 * 1024)) {
        event.stopImmediatePropagation()
        event.target.value = ''
        post('xcpdf:error', { message: '单个文件请控制在 30 MB 以内。' })
      }
    },
    true,
  )
  document.addEventListener(
    'drop',
    (event) => {
      if ([...(event.dataTransfer?.files || [])].some((file) => file.size > 30 * 1024 * 1024)) {
        event.preventDefault()
        event.stopImmediatePropagation()
        post('xcpdf:error', { message: '单个文件请控制在 30 MB 以内。' })
      }
    },
    true,
  )
  document.addEventListener('keydown', (event) => {
    if (
      ['Enter', ' '].includes(event.key) &&
      event.target.matches('[role="button"].color-preset, [role="button"].color-swatch')
    ) {
      event.preventDefault()
      event.target.click()
    }
  })
  new ResizeObserver(reportHeight).observe(document.querySelector('.main-container'))
  addEventListener('error', (event) => {
    post('xcpdf:error', { message: event.message || '工具运行失败，请取消并清空后重试。' })
  })
})()
