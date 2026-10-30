// Tool options live only for the mounted page. Never persist visitor input or options.
export function load(_key, fallback) {
  return fallback
}
export function save() {}
