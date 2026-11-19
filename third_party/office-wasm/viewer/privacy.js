// SPDX-License-Identifier: AGPL-3.0-or-later
// Each viewer window keeps editor preferences in memory for this document only.
// Static engine resources may use the HTTP cache; input documents never enter it.
;(() => {
  function memoryStorage() {
    const values = new Map()
    return {
      get length() {
        return values.size
      },
      key(index) {
        return [...values.keys()][index] ?? null
      },
      getItem(key) {
        return values.get(String(key)) ?? null
      },
      setItem(key, value) {
        values.set(String(key), String(value))
      },
      removeItem(key) {
        values.delete(String(key))
      },
      clear() {
        values.clear()
      },
    }
  }
  for (const name of ['localStorage', 'sessionStorage']) {
    const storage = memoryStorage()
    Object.defineProperty(window, name, { get: () => storage })
  }
})()
