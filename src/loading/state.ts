let nextId = 0

function send(action: 'begin' | 'end' | 'error', id: string, options = {}) {
  window.dispatchEvent(new CustomEvent('site:loading', { detail: { action, id, ...options } }))
}

export function beginPageLoading(href: string, reset = false) {
  const id = `page-${++nextId}`
  send('begin', id, { href, reset })
  return {
    finish: () => send('end', id),
    fail: () => send('error', id),
  }
}

export function finishInitialLoading() {
  send('end', 'boot')
}

export function failInitialLoading() {
  send('error', 'boot')
}

export async function waitForInitialStyles() {
  await Promise.all(
    Array.from(document.querySelectorAll<HTMLLinkElement>('link[data-app-style]')).map(
      (link) =>
        new Promise<void>((resolve, reject) => {
          if (link.dataset.loadError) return reject(new Error('Page stylesheet unavailable'))
          if (link.sheet) return resolve()
          link.addEventListener('load', () => resolve(), { once: true })
          link.addEventListener('error', () => reject(new Error('Page stylesheet unavailable')), {
            once: true,
          })
        }),
    ),
  )
}
