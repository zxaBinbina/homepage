// This small, dependency-free controller runs before the application can load.
// One shell survives Vue mounting and is reused for delayed navigation/content.
;(() => {
  const screen = document.getElementById('site-loading')
  const title = screen.querySelector('.site-loading-title')
  const status = screen.querySelector('.site-loading-copy')
  const description = screen.querySelector('.site-loading-description')
  const retry = screen.querySelector('.site-loading-retry')
  const tasks = new Set(['boot'])
  let initial = true
  let showTimer
  let slowTimer
  let hideTimer
  let failed = null

  function showRetry(visible) {
    screen.dataset.retry = String(visible)
    retry.inert = !visible
    retry.setAttribute('aria-hidden', String(!visible))
  }

  function show() {
    screen.hidden = false
    screen.inert = false
    screen.removeAttribute('aria-hidden')
    status.setAttribute('role', 'status')
    // Establish the starting opacity before the entrance transition.
    screen.getBoundingClientRect()
    screen.dataset.visible = 'true'
  }

  function schedule() {
    clearTimeout(showTimer)
    clearTimeout(slowTimer)
    clearTimeout(hideTimer)
    failed = null
    screen.dataset.mode = initial ? 'initial' : 'navigation'
    screen.dataset.state = 'waiting'
    title.textContent = initial ? '正在搭建这一页' : '正在打开下一页'
    description.textContent = initial ? '一点点准备，马上见面。' : '页面正在准备，请稍等片刻。'
    showRetry(false)
    if (!screen.hidden) show()
    else showTimer = setTimeout(show, 500)
    slowTimer = setTimeout(() => {
      description.textContent = initial
        ? '加载比平时久一些，可以继续等待或重新加载。'
        : '加载较慢，可稍等或重试。'
      showRetry(true)
    }, 10000)
  }

  function settle() {
    if (tasks.size || failed) return
    initial = false
    clearTimeout(showTimer)
    clearTimeout(slowTimer)
    screen.dataset.visible = 'false'
    // Restore keyboard focus if completion removed the focused retry action.
    if (screen.contains(document.activeElement)) {
      const main = document.querySelector('main')
      if (main) {
        if (!main.hasAttribute('tabindex')) main.tabIndex = -1
        main.focus({ preventScroll: true })
      }
    }
    screen.setAttribute('aria-hidden', 'true')
    status.removeAttribute('role')
    screen.inert = true
    hideTimer = setTimeout(
      () => {
        screen.hidden = true
      },
      matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 220,
    )
  }

  function fail(id = 'boot') {
    failed = id
    clearTimeout(showTimer)
    clearTimeout(slowTimer)
    clearTimeout(hideTimer)
    screen.dataset.state = 'error'
    title.textContent = '这一页暂时没能加载'
    description.textContent = initial
      ? '请检查网络后重新加载，也可以稍后再来。'
      : '请检查网络后重新加载。'
    showRetry(true)
    show()
  }

  retry.href = location.href
  retry.addEventListener('click', (event) => {
    event.preventDefault()
    location.assign(retry.href)
  })
  window.addEventListener('site:loading', ({ detail }) => {
    const { action, id, href, reset } = detail
    if (action === 'begin') {
      const idle = !tasks.size
      const starting = initial && tasks.has('boot') && !failed
      if (reset) {
        // Ignore late completions/errors from a page that has been left behind.
        for (const task of tasks) if (task !== 'boot') tasks.delete(task)
      }
      tasks.add(id)
      if (href) retry.href = href
      if (idle || (reset && !starting)) schedule()
    } else if (tasks.has(id)) {
      if (action === 'error') fail(id)
      else {
        tasks.delete(id)
        if (failed === id) failed = null
        settle()
      }
    }
  })
  // An unavailable entry bundle cannot report through Vue/router hooks.
  window.addEventListener(
    'error',
    (event) => {
      if (!tasks.has('boot')) return
      const target = event.target
      if (target instanceof HTMLLinkElement) target.dataset.loadError = 'true'
      if (
        target === window ||
        target instanceof HTMLScriptElement ||
        (target instanceof HTMLLinkElement && target.rel === 'stylesheet')
      )
        fail()
    },
    true,
  )
  window.addEventListener('unhandledrejection', () => {
    if (tasks.has('boot')) fail()
  })
  schedule()
})()
