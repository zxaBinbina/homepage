export const toolCatalog = {
  json: {
    name: 'JSON 格式化',
    label: 'JSON',
    description: '校验、格式化或压缩 JSON。',
    category: '开发',
    keywords: '格式化 校验 压缩 format minify',
    hint: '',
  },
  base64: {
    name: 'Base64 编解码',
    label: 'BASE64',
    description: 'UTF-8 文本与 Base64 互转，支持 URL 安全格式。',
    category: '编码',
    keywords: '编码 解码 encode decode utf8',
    hint: '仅支持 UTF-8 文本，不支持二进制文件。',
  },
  url: {
    name: 'URL 编解码',
    label: 'URL',
    description: '编码或解码 URL 参数及完整网址。',
    category: '编码',
    keywords: '网址 链接 百分号 percent uri encode decode',
    hint: '单个查询参数请选择「参数值」；「完整网址」保留 /、?、& 等结构符号。',
  },
  timestamp: {
    name: '时间戳转换',
    label: 'TIME',
    description: '秒、毫秒与日期时间互转。',
    category: '开发',
    keywords: '时间 日期 unix epoch 时区',
    hint: '',
  },
  uuid: {
    name: 'UUID 生成',
    label: 'UUID',
    description: '批量生成 UUID v4，可选大写和连字符。',
    category: '开发',
    keywords: '随机 id 标识符 guid uuid4',
    hint: '每次可生成 1–100 个 UUID v4。',
  },
  text: {
    name: '文本整理',
    label: 'TEXT',
    description: '按行去重、移除空行、清理空格和转换大小写。',
    category: '文本',
    keywords: '去重 空行 统计 字数 大写 小写 deduplicate',
    hint: '去重区分大小写和空格，保留首次出现的顺序；字符数按 Unicode 码点统计。',
  },
} as const

export type ToolId = keyof typeof toolCatalog
export const toolIds = Object.keys(toolCatalog) as ToolId[]
export function isToolId(value: unknown): value is ToolId {
  return typeof value === 'string' && Object.hasOwn(toolCatalog, value)
}
