import { readFileSync } from 'node:fs'
import { Marked } from 'marked'

export function compileRdpWiki(path: string) {
  const toc: { id: string; text: string }[] = []
  const markdown = new Marked({
    renderer: {
      heading({ tokens, depth, text }) {
        const id =
          text === '部署'
            ? 'deployment'
            : text === '架构与适用范围'
              ? 'architecture'
              : `section-${toc.length}`
        toc.push({ id, text })
        return `<h${depth + 1} id="${id}">${this.parser.parseInline(tokens)}</h${depth + 1}>`
      },
      code({ text, lang }) {
        if (lang === 'mermaid')
          return '<div class="rdp-note"><p>浏览器 → Cloudflare HTTPS / Tunnel → 本机认证服务 → SakuraFrp IP 授权 API</p><p>RDP 客户端 → SakuraFrp TCP 隧道准入 → 现有远程桌面服务</p></div>'
        const escaped = text
          .replaceAll('&', '&amp;')
          .replaceAll('<', '&lt;')
          .replaceAll('>', '&gt;')
        return `<pre tabindex="0" aria-label="${lang || '文本'}代码"><code>${escaped}</code></pre>`
      },
    },
  })
  const source = readFileSync(path, 'utf8')
    .replace('](LICENSE)', '](https://github.com/zxaBinbina/rdp-access-auth/blob/main/LICENSE)')
    .replace(
      '](wordlists/readme.md)',
      '](https://github.com/zxaBinbina/rdp-access-auth/blob/main/wordlists/readme.md)',
    )

  const wikiHtml = markdown.parse(source)

  return { html: wikiHtml, toc }
}
