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
  radix: {
    name: '进制转换',
    label: 'RADIX',
    description: '在 2–36 进制之间转换整数，支持超长数字。',
    category: '开发',
    keywords: '二进制 八进制 十进制 十六进制 bigint binary hex number',
    hint: '支持正负整数，最多 4096 位；0b、0o、0x 前缀需匹配输入进制。',
  },
  hash: {
    name: '哈希计算',
    label: 'HASH',
    description: '计算文本的 SHA-256、SHA-384、SHA-512 或 SHA-1 摘要。',
    category: '开发',
    keywords: '哈希 散列 校验 sha256 sha384 sha512 sha1 digest checksum',
    hint: '按 UTF-8 计算，空格和换行会影响结果；空输入可计算空文本的摘要。',
  },
  jwt: {
    name: 'JWT 解析',
    label: 'JWT',
    description: '查看 JWT 的 Header、Payload 和时间字段。',
    category: '开发',
    keywords: '令牌 token jwt header payload exp nbf iat',
    hint: '仅解析内容，不验证签名；请勿据此判断令牌可信或授权是否有效。',
  },
  password: {
    name: '密码生成',
    label: 'PASSWORD',
    description: '生成随机密码，自选长度、字符类型和数量。',
    category: '开发',
    keywords: '密码 随机 password random 安全',
    hint: '长度 8–128，每次 1–50 个；每个密码都包含所选的每类字符。',
  },
  html: {
    name: 'HTML 实体转换',
    label: 'HTML',
    description: '转义 HTML 特殊字符，或将实体还原为文本。',
    category: '编码',
    keywords: 'html 实体 转义 escape unescape entity amp lt gt',
    hint: '还原支持带分号的实体，如 &amp;、&#65;、&#x1F30D;；结果按文本显示。',
  },
  color: {
    name: '颜色转换',
    label: 'COLOR',
    description: 'HEX、RGB、HSL 互转，配合取色器预览颜色。',
    category: '设计',
    keywords: '颜色 色值 取色 hex rgb hsl color colour',
    hint: '支持 #RGB、#RRGGBB、rgb(r, g, b) 和 hsl(h, s%, l%)，不含透明度。',
  },
} as const

export type ToolId = keyof typeof toolCatalog
export const toolIds = Object.keys(toolCatalog) as ToolId[]
export function isToolId(value: unknown): value is ToolId {
  return typeof value === 'string' && Object.hasOwn(toolCatalog, value)
}
