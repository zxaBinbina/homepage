/**
 * 构建期预渲染入口：由 scripts/prerender.mjs 通过 Vite SSR 加载。
 * 用内存路由把每个地址渲染为可抓取的静态正文，随后由脚本注入产物 HTML。
 * 仅在 Node 构建环境中运行，不影响客户端入口。
 */
import './prerender-env'
import { createSSRApp } from 'vue'
import { renderToString } from 'vue/server-renderer'
import { createMemoryHistory, createRouter } from 'vue-router'
import App from './App.vue'
import { routes } from './router'

export async function render(path: string): Promise<string> {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const app = createSSRApp(App)
  app.use(router)
  await router.push(path)
  await router.isReady()
  return renderToString(app)
}
