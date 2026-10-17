import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { Marked } from 'marked'
import { gazeGuideIds } from '../src/gaze/catalog'

export type GazeBlock =
  | { type: 'html'; html: string }
  | { type: 'code'; code: string; language: string; label?: string }
  | { type: 'code-group'; items: { label: string; code: string; language: string }[] }
  | { type: 'admonition'; kind: string; title: string; blocks: GazeBlock[] }
  | { type: 'details'; title: string; blocks: GazeBlock[] }
  | { type: 'heading'; depth: number; id: string; html: string; text: string }

export interface GazeGuideDoc {
  id: string
  title: string
  intro: GazeBlock[]
  sections: { id: string; title: string; htmlTitle: string; blocks: GazeBlock[] }[]
  outline: { id: string; depth: number; title: string }[]
  search: string
}

interface AnchorMaps {
  [guideId: string]: { [englishSlug: string]: string }
}

/** 与 VitePress/GitHub 相同风格的标题锚点；中文标题保留汉字，中英文之间不留连字符。 */
function slugify(raw: string, used: Map<string, number>): string {
  const han = /[一-鿿㐀-䶿]/
  let base = raw
    .replace(/<[^>]+>/g, '')
    .replace(/[`*~_[\]()]/g, '')
    .trim()
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s-]/gu, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
    .replace(/-(?=[一-鿿㐀-䶿])/g, '')
    .replace(/([一-鿿㐀-䶿])-/g, '$1')
  if (!base) base = 'section'
  const count = used.get(base) ?? 0
  used.set(base, count + 1)
  return count ? `${base}-${count + 1}` : base
}

function parseFenceInfo(info: string): { language: string; label?: string } {
  const match = info.trim().match(/^([\w+#-]*)?\s*(?:\[(.+)\])?$/)
  return { language: match?.[1] || 'text', label: match?.[2] }
}

function plainText(html: string): string {
  return html
    .replace(/<[^>]+>/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, ' ')
    .trim()
}

class GuideParser {
  private md = new Marked()
  private used = new Map<string, number>()
  readonly outline: { id: string; depth: number; title: string }[] = []
  readonly searchParts: string[] = []

  constructor(private anchors: Record<string, string>) {}

  heading(raw: string, depth: number): GazeBlock & { type: 'heading' } {
    const id = this.anchors[raw.trim()] ?? slugify(raw, this.used)
    // 记录英文标题对应的锚点别名，供正文中遗留的英文锚点链接重写。
    const englishId = slugify(raw, new Map())
    if (englishId !== id && !(englishId in this.anchors)) this.anchors[englishId] = id
    const paragraph = this.md.parser(this.md.lexer(raw))
    const html = paragraph.replace(/^<p>/, '').replace(/<\/p>$/, '')
    const text = plainText(html)
    this.outline.push({ id, depth, title: text })
    this.searchParts.push(text)
    return { type: 'heading', depth, id, html, text }
  }

  inlineHtml(raw: string): string {
    return this.md.parser(this.md.lexer(raw))
  }

  parseBlocks(lines: string[]): GazeBlock[] {
    const blocks: GazeBlock[] = []
    let buffer: string[] = []
    let searchBuffer: string[] = []
    const flush = () => {
      if (!buffer.length) return
      const html = this.inlineHtml(buffer.join('\n'))
      blocks.push({ type: 'html', html })
      this.searchParts.push(plainText(html))
      buffer = []
      searchBuffer = []
    }
    let i = 0
    while (i < lines.length) {
      const line = lines[i]
      const fence = line.match(/^```(\S*)\s*(.*)$/)
      if (fence) {
        flush()
        const info = parseFenceInfo(fence[2] ? `${fence[1]} ${fence[2]}` : fence[1])
        const codeLines: string[] = []
        i += 1
        while (i < lines.length && !/^```\s*$/.test(lines[i])) {
          codeLines.push(lines[i])
          i += 1
        }
        i += 1 // 跳过结束围栏
        const code = codeLines.join('\n')
        this.searchParts.push(code)
        blocks.push({ type: 'code', code, language: info.language, label: info.label })
        continue
      }
      const container = line.match(/^:::\s*(\S*)\s*(.*)$/)
      if (container && container[1]) {
        flush()
        const kind = container[1]
        const title = container[2].trim()
        const inner: string[] = []
        i += 1
        while (i < lines.length && !/^:::\s*$/.test(lines[i])) {
          inner.push(lines[i])
          i += 1
        }
        i += 1 // 跳过 ::: 结束行
        if (kind === 'code-group') {
          const items: { label: string; code: string; language: string }[] = []
          let j = 0
          while (j < inner.length) {
            const itemFence = inner[j].match(/^```(\S*)\s*(.*)$/)
            if (!itemFence) {
              j += 1
              continue
            }
            const info = parseFenceInfo(
              itemFence[2] ? `${itemFence[1]} ${itemFence[2]}` : itemFence[1],
            )
            const codeLines: string[] = []
            j += 1
            while (j < inner.length && !/^```\s*$/.test(inner[j])) {
              codeLines.push(inner[j])
              j += 1
            }
            j += 1
            items.push({
              label: info.label || info.language,
              code: codeLines.join('\n'),
              language: info.language,
            })
          }
          this.searchParts.push(items.map((item) => item.code).join('\n'))
          blocks.push({ type: 'code-group', items })
        } else if (kind === 'details') {
          const innerBlocks = this.parseBlocks(inner)
          this.searchParts.push(title)
          blocks.push({ type: 'details', title, blocks: innerBlocks })
        } else {
          const innerBlocks = this.parseBlocks(inner)
          this.searchParts.push(title)
          blocks.push({ type: 'admonition', kind, title, blocks: innerBlocks })
        }
        continue
      }
      const alert = line.match(/^> \[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*$/)
      if (alert) {
        flush()
        const quote: string[] = []
        i += 1
        while (i < lines.length && /^>/.test(lines[i])) {
          quote.push(lines[i].replace(/^> ?/, ''))
          i += 1
        }
        blocks.push({
          type: 'admonition',
          kind: alert[1].toLowerCase(),
          title: '',
          blocks: this.parseBlocks(quote),
        })
        continue
      }
      const heading = line.match(/^(#{1,6})\s+(.*)$/)
      if (heading) {
        flush()
        blocks.push(this.heading(heading[2], heading[1].length))
        i += 1
        continue
      }
      buffer.push(line)
      searchBuffer.push(line)
      i += 1
    }
    flush()
    return blocks
  }
}

/** 正文中的站内锚点可能在标题翻译后失效，用别名表把英文锚点改写到新锚点。 */
function rewriteAnchors(html: string, anchors: Record<string, string>): string {
  return html.replace(/href="#([^"]+)"/g, (match, slug: string) => {
    const target = anchors[decodeURIComponent(slug)]
    return target ? `href="#${encodeURIComponent(target)}"` : match
  })
}

function rewriteGuideLinks(source: string): string {
  return source
    .replace(/https:\/\/gaze\.gundulabs\.com(\/guide\/[a-z0-9-]+)(\.html)?/g, '/projects/gaze$1')
    .replace(/]\((\/guide\/[a-z0-9-]+)(\.html)?/g, '](/projects/gaze$1')
}

export function compileGazeGuide(id: string, path: string, anchorMaps: AnchorMaps): GazeGuideDoc {
  const source = rewriteGuideLinks(readFileSync(path, 'utf8'))
  const anchors: Record<string, string> = { ...(anchorMaps[id] ?? {}) }
  const parser = new GuideParser(anchors)
  const blocks = parser.parseBlocks(source.split('\n'))
  const firstHeading = blocks.findIndex((block) => block.type === 'heading')
  const title =
    blocks
      .filter((block): block is GazeBlock & { type: 'heading' } => block.type === 'heading')
      .find((block) => block.depth === 1)?.text ?? id
  const doc: GazeGuideDoc = {
    id,
    title,
    intro: [],
    sections: [],
    outline: parser.outline.filter((entry) => entry.depth > 1),
    search: '',
  }
  // 拆分：h1 之后、h2 之前是引言；每个 h2 开启一个小节。
  const isHeading = (block: GazeBlock, depth: number): block is GazeBlock & { type: 'heading' } =>
    block.type === 'heading' && block.depth === depth
  let section: GazeGuideDoc['sections'][number] | undefined
  const body = firstHeading === -1 ? blocks : blocks.slice(firstHeading + 1)
  for (const block of body) {
    if (isHeading(block, 2)) {
      section = { id: block.id, title: block.text, htmlTitle: block.html, blocks: [] }
      doc.sections.push(section)
    } else if (section) {
      section.blocks.push(block)
    } else {
      doc.intro.push(block)
    }
  }
  const rewrite = (blocks: GazeBlock[]): GazeBlock[] =>
    blocks.map((block) => {
      if (block.type === 'html') return { ...block, html: rewriteAnchors(block.html, anchors) }
      if (block.type === 'admonition' || block.type === 'details')
        return { ...block, blocks: rewrite(block.blocks) }
      return block
    })
  doc.intro = rewrite(doc.intro)
  doc.sections = doc.sections.map((item) => ({ ...item, blocks: rewrite(item.blocks) }))
  doc.search = [title, ...parser.searchParts].join('\n').toLocaleLowerCase()
  return doc
}

export function compileGazeContent(contentDir: string): { guides: Record<string, GazeGuideDoc> } {
  const anchorPath = resolve(contentDir, 'anchors.json')
  const anchorMaps: AnchorMaps = existsSync(anchorPath)
    ? (JSON.parse(readFileSync(anchorPath, 'utf8')) as AnchorMaps)
    : {}
  const guides: Record<string, GazeGuideDoc> = {}
  for (const id of gazeGuideIds) {
    guides[id] = compileGazeGuide(id, resolve(contentDir, 'guide', `${id}.md`), anchorMaps)
  }
  return { guides }
}
