/**
 * 构建期预渲染脚本：把 Vite 产物中空的 #app 容器替换为各路由的静态正文，
 * 让爬虫与禁用 JavaScript 的访问者直接读到页面内容。
 *
 * 用法：node scripts/prerender.mjs [distDir]   （默认 dist）
 */
import { createServer } from 'vite'
import { readFile, writeFile } from 'node:fs/promises'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const distDir = process.argv[2] || 'dist'
const appMarker = '<div id="app"></div>'

const server = await createServer({
  root: projectRoot,
  logLevel: 'error',
  server: { middlewareMode: true },
  appType: 'custom',
})

try {
  const { render } = await server.ssrLoadModule('/src/prerender.ts')
  const { pages, pageFile } = await server.ssrLoadModule('/src/pages.ts')
  const entries = Object.entries(pages)
  const failures = []
  for (const [name, path] of entries) {
    const fileName = pageFile(name)
    const file = join(projectRoot, distDir, fileName)
    try {
      const document = await readFile(file, 'utf8')
      if (!document.includes(appMarker)) throw new Error('missing #app container marker')
      const body = await render(path)
      await writeFile(file, document.replace(appMarker, () => `<div id="app">${body}</div>`))
    } catch (error) {
      failures.push(`${path} → ${error instanceof Error ? error.message : String(error)}`)
    }
  }
  if (failures.length) {
    console.error(`prerender: ${entries.length - failures.length}/${entries.length} 页注入成功，失败项：`)
    for (const failure of failures) console.error(`  - ${failure}`)
    process.exitCode = 1
  } else {
    console.log(`prerender: 已为 ${entries.length} 个页面注入静态正文`)
  }
} finally {
  await server.close()
}
