import { readFileSync } from 'node:fs'
import { Marked, type Token } from 'marked'

type Block =
  | { type: 'html'; html: string }
  | { type: 'code'; code: string; language: string }
  | { type: 'diagram' }

export function compileRdpWiki(path: string) {
  const markdown = new Marked()
  const source = readFileSync(path, 'utf8')
    .replace('](LICENSE)', '](https://github.com/zxaBinbina/rdp-access-auth/blob/main/LICENSE)')
    .replace(
      '](wordlists/readme.md)',
      '](https://github.com/zxaBinbina/rdp-access-auth/blob/main/wordlists/readme.md)',
    )
  const sections: {
    id: string
    title: string
    step?: string
    group: string
    blocks: Block[]
    search: string
  }[] = []
  let pending: Token[] = []
  let section: (typeof sections)[number] | undefined
  let parentGroup = '了解项目'
  function flush() {
    if (section && pending.length)
      section.blocks.push({ type: 'html', html: markdown.parser(pending) })
    pending = []
  }
  for (const token of markdown.lexer(source)) {
    if (token.type === 'heading') {
      flush()
      const id = ['部署', '六步完成部署'].includes(token.text)
        ? 'deployment'
        : token.text === '架构与适用范围'
          ? 'architecture'
          : `section-${sections.length}`
      const step = token.depth === 3 ? token.text.match(/^([1-6])\./)?.[1] : undefined
      const rootGroup = ['运行要求', '部署', '部署前准备', '六步完成部署'].includes(token.text)
        ? '开始部署'
        : ['维护与排查', 'Cloudflare Turnstile（可选）', '安装后的管理', '排错'].includes(
              token.text,
            )
          ? '使用与维护'
          : '了解项目'
      const group = step ? '开始部署' : token.depth === 3 ? parentGroup : rootGroup
      if (token.depth === 2) parentGroup = rootGroup
      section = { id, title: token.text, step, group, blocks: [], search: token.text }
      sections.push(section)
    } else if (section) {
      section.search += '\n' + token.raw
      if (token.type === 'code') {
        flush()
        section.blocks.push(
          token.lang === 'mermaid'
            ? { type: 'diagram' }
            : { type: 'code', code: token.text, language: token.lang || 'text' },
        )
      } else pending.push(token)
    }
  }
  flush()
  // Keep existing fragment IDs while placing deployment before reference material.
  const groupOrder = ['开始部署', '使用与维护', '了解项目']
  sections.sort((a, b) => groupOrder.indexOf(a.group) - groupOrder.indexOf(b.group))
  return { sections }
}
