export const MAX_INPUT_LENGTH = 1_000_000

export function checkInput(input: string) {
  if (input.length > MAX_INPUT_LENGTH)
    throw new Error('内容过长，请控制在 100 万个 UTF-16 字符以内。')
}

/** Validate with the native parser, then format tokens without changing numeric values or keys. */
export function formatJson(input: string, indent = '  ') {
  checkInput(input)
  if (!input.trim()) throw new Error('请先输入 JSON 内容。')
  try {
    JSON.parse(input)
  } catch (error) {
    throw new Error(
      `JSON 语法有误：${error instanceof Error ? error.message : '请检查引号、逗号和括号。'}`,
    )
  }
  const tokens = input.match(/"(?:[^"\\]|\\[\s\S])*"|[^\s{}\[\],:]+|[{}\[\],:]/g) || []
  let depth = 0
  let length = 0
  const chunks: string[] = []
  function append(value: string) {
    length += value.length
    if (length > 4_000_000) throw new Error('格式化结果过大，请缩小内容或使用更短的缩进。')
    chunks.push(value)
  }
  const newline = () => (indent ? `\n${indent.repeat(depth)}` : '')
  tokens.forEach((token, index) => {
    if (token === '{' || token === '[') {
      depth++
      if (depth > 64) throw new Error('JSON 嵌套超过 64 层，请简化内容后再试。')
      append(token)
      if (tokens[index + 1] !== '}' && tokens[index + 1] !== ']') append(newline())
    } else if (token === '}' || token === ']') {
      depth--
      if (tokens[index - 1] !== '{' && tokens[index - 1] !== '[') append(newline())
      append(token)
    } else if (token === ',') append(`,${newline()}`)
    else if (token === ':') append(indent ? ': ' : ':')
    else append(token)
  })
  return chunks.join('')
}

export function encodeBase64(input: string, urlSafe = false) {
  checkInput(input)
  const bytes = new TextEncoder().encode(input)
  let binary = ''
  for (let i = 0; i < bytes.length; i += 8192) {
    binary += String.fromCharCode(...bytes.subarray(i, i + 8192))
  }
  const result = btoa(binary)
  return urlSafe ? result.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '') : result
}

export function decodeBase64(input: string, urlSafe = false) {
  checkInput(input)
  let value = input.replace(/\s/g, '')
  const alphabet = urlSafe ? /^[A-Za-z0-9_-]*={0,2}$/ : /^[A-Za-z0-9+/]*={0,2}$/
  if (
    !alphabet.test(value) ||
    value.length % 4 === 1 ||
    (value.includes('=') && value.length % 4 !== 0)
  ) {
    throw new Error('Base64 格式有误，请检查字符、填充符与所选格式。')
  }
  if (urlSafe) value = value.replace(/-/g, '+').replace(/_/g, '/')
  try {
    const binary = atob(value)
    return new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(
      Uint8Array.from(binary, (char) => char.charCodeAt(0)),
    )
  } catch {
    throw new Error('无法解码为 UTF-8 文本，请检查 Base64 内容；二进制文件不适用于此工具。')
  }
}

export function transformUrl(
  input: string,
  decode: boolean,
  mode: 'component' | 'uri',
  plusAsSpace = false,
) {
  checkInput(input)
  try {
    if (decode) {
      const source = mode === 'component' && plusAsSpace ? input.replace(/\+/g, ' ') : input
      return mode === 'component' ? decodeURIComponent(source) : decodeURI(source)
    }
    return mode === 'component' ? encodeURIComponent(input) : encodeURI(input)
  } catch {
    throw new Error('URL 转换失败，请检查不完整的 % 转义或无效的 Unicode 字符。')
  }
}

export type TextAction = 'deduplicate' | 'trim' | 'empty' | 'upper' | 'lower'
export function transformText(input: string, action: TextAction) {
  checkInput(input)
  const lines = input.split(/\r\n|\r|\n/)
  switch (action) {
    case 'deduplicate':
      return [...new Set(lines)].join('\n')
    case 'trim':
      return lines.map((line) => line.trim()).join('\n')
    case 'empty':
      return lines.filter((line) => line.trim()).join('\n')
    case 'upper':
      return input.toUpperCase()
    case 'lower':
      return input.toLowerCase()
  }
}

export function textStats(input: string) {
  let characters = 0
  for (const _character of input) characters++
  return { characters, lines: input ? input.split(/\r\n|\r|\n/).length : 0 }
}

export type TimeZone = 'local' | 'utc'
export function dateInputValue(date: Date, zone: TimeZone) {
  const parts =
    zone === 'utc'
      ? [
          date.getUTCFullYear(),
          date.getUTCMonth() + 1,
          date.getUTCDate(),
          date.getUTCHours(),
          date.getUTCMinutes(),
          date.getUTCSeconds(),
          date.getUTCMilliseconds(),
        ]
      : [
          date.getFullYear(),
          date.getMonth() + 1,
          date.getDate(),
          date.getHours(),
          date.getMinutes(),
          date.getSeconds(),
          date.getMilliseconds(),
        ]
  const [year, month, day, hour, minute, second, ms] = parts.map((part, i) =>
    String(part).padStart(i === 0 ? 4 : i === 6 ? 3 : 2, '0'),
  )
  return `${year}-${month}-${day}T${hour}:${minute}:${second}.${ms}`
}

function validDate(date: Date) {
  if (
    !Number.isFinite(date.getTime()) ||
    date.getUTCFullYear() < 1 ||
    date.getUTCFullYear() > 9999 ||
    date.getFullYear() < 1 ||
    date.getFullYear() > 9999
  ) {
    throw new Error('时间超出支持范围，请使用公元 0001 至 9999 年的日期。')
  }
  return date
}

export function parseTimestamp(value: string, unit: 'seconds' | 'milliseconds') {
  if (!/^-?\d+$/.test(value.trim())) throw new Error('请输入整数时间戳，并选择秒或毫秒。')
  const milliseconds = Number(value.trim()) * (unit === 'seconds' ? 1000 : 1)
  if (!Number.isSafeInteger(milliseconds)) throw new Error('时间戳超出安全整数范围。')
  return validDate(new Date(milliseconds))
}

export function parseDateInput(value: string, zone: TimeZone) {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{1,3}))?)?$/.exec(value)
  if (!match) throw new Error('请输入完整的日期与时间。')
  const parts = [
    Number(match[1]),
    Number(match[2]) - 1,
    Number(match[3]),
    Number(match[4]),
    Number(match[5]),
    Number(match[6] || 0),
    Number((match[7] || '').padEnd(3, '0')),
  ]
  const [year, month, day, hour, minute, second, ms] = parts as [
    number,
    number,
    number,
    number,
    number,
    number,
    number,
  ]
  const date = new Date(0)
  if (zone === 'utc') {
    date.setUTCFullYear(year, month, day)
    date.setUTCHours(hour, minute, second, ms)
  } else {
    date.setFullYear(year, month, day)
    date.setHours(hour, minute, second, ms)
  }
  validDate(date)
  const expected = `${match[1]}-${match[2]}-${match[3]}T${match[4]}:${match[5]}:${match[6] || '00'}.${String(ms).padStart(3, '0')}`
  if (dateInputValue(date, zone) !== expected)
    throw new Error('日期不存在，或位于本地夏令时跳过的时段，请检查输入。')
  return date
}

export function generateUuids(count: number, uppercase = false, hyphens = true) {
  if (!Number.isInteger(count) || count < 1 || count > 100)
    throw new Error('生成数量须为 1 至 100 的整数。')
  return Array.from({ length: count }, () => {
    const bytes = crypto.getRandomValues(new Uint8Array(16))
    bytes[6] = (bytes[6]! & 0x0f) | 0x40
    bytes[8] = (bytes[8]! & 0x3f) | 0x80
    const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('')
    let uuid = hyphens
      ? `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
      : hex
    if (uppercase) uuid = uuid.toUpperCase()
    return uuid
  }).join('\n')
}

export function convertRadix(input: string, from: number, to: number) {
  checkInput(input)
  if (![from, to].every((base) => Number.isInteger(base) && base >= 2 && base <= 36)) {
    throw new Error('进制须为 2 至 36 的整数。')
  }
  let digits = input.trim().toLowerCase()
  const negative = digits.startsWith('-')
  if (/^[+-]/.test(digits)) digits = digits.slice(1)
  const prefixes: Record<number, string> = { 2: '0b', 8: '0o', 16: '0x' }
  const prefix = prefixes[from]
  if (prefix && digits.startsWith(prefix)) digits = digits.slice(2)
  if (!digits || digits.length > 4096) throw new Error('请输入 1 至 4096 位整数。')
  const alphabet = '0123456789abcdefghijklmnopqrstuvwxyz'
  let value = 0n
  for (const digit of digits) {
    const number = alphabet.indexOf(digit)
    if (number < 0 || number >= from) throw new Error(`字符「${digit}」不属于 ${from} 进制。`)
    value = value * BigInt(from) + BigInt(number)
  }
  return (negative ? -value : value).toString(to).toUpperCase()
}

export const hashAlgorithms = ['SHA-256', 'SHA-384', 'SHA-512', 'SHA-1'] as const
export type HashAlgorithm = (typeof hashAlgorithms)[number]
export async function hashText(input: string, algorithm: HashAlgorithm) {
  checkInput(input)
  if (!hashAlgorithms.includes(algorithm)) throw new Error('不支持该哈希算法。')
  if (!globalThis.crypto?.subtle)
    throw new Error('当前浏览器无法计算哈希，请使用 HTTPS 或本地预览地址。')
  const bytes = await crypto.subtle.digest(algorithm, new TextEncoder().encode(input))
  return Array.from(new Uint8Array(bytes), (byte) => byte.toString(16).padStart(2, '0')).join('')
}

export function escapeHtml(input: string) {
  checkInput(input)
  const entities: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }
  return input.replace(/[&<>"']/g, (character) => entities[character]!)
}

export function unescapeHtml(input: string) {
  checkInput(input)
  const decoder = document.createElement('textarea')
  // Only feed individual character references to the parser, never user-supplied tags.
  return input.replace(/&(?:#[xX][\da-fA-F]+|#\d+|[A-Za-z][A-Za-z0-9]+);/g, (entity) => {
    decoder.innerHTML = entity
    return decoder.value
  })
}

export function parseJwt(input: string, now = Date.now()) {
  checkInput(input)
  const segments = input.trim().split('.')
  if (
    segments.length !== 3 ||
    !segments[0] ||
    !segments[1] ||
    !segments.every((segment) => /^[A-Za-z0-9_-]*$/.test(segment) && segment.length % 4 !== 1)
  ) {
    throw new Error('请输入由三个 Base64URL 段组成的 JWT，以两个句点分隔。')
  }
  let headerText: string, payloadText: string
  let header: Record<string, unknown>, payload: Record<string, unknown>
  try {
    headerText = decodeBase64(segments[0]!, true)
    payloadText = decodeBase64(segments[1]!, true)
    header = JSON.parse(headerText)
    payload = JSON.parse(payloadText)
    if (
      !header ||
      Array.isArray(header) ||
      typeof header !== 'object' ||
      !payload ||
      Array.isArray(payload) ||
      typeof payload !== 'object' ||
      typeof header.alg !== 'string' ||
      !header.alg
    )
      throw new Error()
  } catch {
    throw new Error('Header 和 Payload 须为有效的 UTF-8 JSON 对象，Header 需包含 alg。')
  }
  if (!segments[2] && header.alg !== 'none') throw new Error('JWT 签名段为空，请检查令牌是否完整。')
  const report = [
    'Header',
    formatJson(headerText),
    '',
    'Payload',
    formatJson(payloadText),
    '',
    '签名：未验证',
  ]
  for (const [key, label] of [
    ['iat', '签发时间'],
    ['nbf', '开始时间'],
    ['exp', '到期时间'],
  ] as const) {
    if (!Object.hasOwn(payload, key)) continue
    const seconds = payload[key]
    const date = typeof seconds === 'number' ? new Date(seconds * 1000) : new Date(NaN)
    if (!Number.isFinite(date.getTime())) {
      report.push(`${label}（${key}）：不是可显示的数字时间戳`)
      continue
    }
    report.push(`${label}（${key}，UTC）：${date.toISOString()}`)
    if (key === 'exp') report.push(now >= date.getTime() ? 'exp：已过期' : 'exp：尚未到期')
    if (key === 'nbf' && now < date.getTime()) report.push('nbf：尚未到开始时间')
  }
  return report.join('\n')
}

export interface PasswordOptions {
  length: number
  count: number
  lowercase: boolean
  uppercase: boolean
  numbers: boolean
  symbols: boolean
  excludeSimilar: boolean
}

function randomIndex(max: number) {
  const limit = 0x100000000 - (0x100000000 % max)
  const buffer = new Uint32Array(1)
  do {
    crypto.getRandomValues(buffer)
  } while (buffer[0]! >= limit)
  return buffer[0]! % max
}

export function generatePasswords(options: PasswordOptions) {
  if (!Number.isInteger(options.length) || options.length < 8 || options.length > 128)
    throw new Error('密码长度须为 8 至 128 的整数。')
  if (!Number.isInteger(options.count) || options.count < 1 || options.count > 50)
    throw new Error('生成数量须为 1 至 50 的整数。')
  const groups = [
    options.lowercase ? 'abcdefghijklmnopqrstuvwxyz' : '',
    options.uppercase ? 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' : '',
    options.numbers ? '0123456789' : '',
    options.symbols ? '!@#$%^&*()-_=+[]{};:,.?/|' : '',
  ]
    .map((group) => (options.excludeSimilar ? group.replace(/[0Oo1Il|]/g, '') : group))
    .filter(Boolean)
  if (!groups.length) throw new Error('请至少选择一种字符类型。')
  const alphabet = groups.join('')
  return Array.from({ length: options.count }, () => {
    let password: string
    do {
      password = Array.from(
        { length: options.length },
        () => alphabet[randomIndex(alphabet.length)],
      ).join('')
    } while (!groups.every((group) => [...password].some((character) => group.includes(character))))
    return password
  }).join('\n')
}

export function convertColor(input: string) {
  checkInput(input)
  const value = input.trim()
  const hex = /^#?([\da-f]{3}|[\da-f]{6})$/i.exec(value)
  const rgb = /^rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$/i.exec(value)
  const hsl =
    /^hsl\(\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+))(?:deg)?\s*,\s*((?:\d+(?:\.\d+)?|\.\d+))%\s*,\s*((?:\d+(?:\.\d+)?|\.\d+))%\s*\)$/i.exec(
      value,
    )
  let channels: number[]
  if (hex) {
    const expanded =
      hex[1]!.length === 3 ? [...hex[1]!].map((digit) => digit + digit).join('') : hex[1]!
    channels = [0, 2, 4].map((start) => parseInt(expanded.slice(start, start + 2), 16))
  } else if (rgb) {
    channels = rgb.slice(1).map(Number)
    if (channels.some((channel) => channel > 255))
      throw new Error('RGB 各通道须为 0 至 255 的整数。')
  } else if (hsl) {
    const [hue, saturation, lightness] = hsl.slice(1).map(Number) as [number, number, number]
    if (![hue, saturation, lightness].every(Number.isFinite) || saturation > 100 || lightness > 100)
      throw new Error('HSL 饱和度和亮度须在 0% 至 100% 之间。')
    const h = (((hue % 360) + 360) % 360) / 60
    const s = saturation / 100,
      l = lightness / 100
    const c = (1 - Math.abs(2 * l - 1)) * s
    const x = c * (1 - Math.abs((h % 2) - 1))
    const m = l - c / 2
    const parts = [
      [c, x, 0],
      [x, c, 0],
      [0, c, x],
      [0, x, c],
      [x, 0, c],
      [c, 0, x],
    ][Math.floor(h)]!
    channels = parts.map((part) => Math.round((part + m) * 255))
  } else throw new Error('请输入 HEX、rgb(r, g, b) 或 hsl(h, s%, l%) 格式的颜色。')
  const [r, g, b] = channels.map((channel) => channel / 255) as [number, number, number]
  const max = Math.max(r, g, b),
    min = Math.min(r, g, b),
    delta = max - min
  const l = (max + min) / 2
  let h = 0,
    s = 0
  if (delta) {
    s = delta / (1 - Math.abs(2 * l - 1))
    h = (max === r ? (g - b) / delta : max === g ? (b - r) / delta + 2 : (r - g) / delta + 4) * 60
    if (h < 0) h += 360
  }
  const round = (number: number) => Number(number.toFixed(3))
  return {
    hex:
      '#' +
      channels
        .map((channel) => channel.toString(16).padStart(2, '0'))
        .join('')
        .toUpperCase(),
    rgb: `rgb(${channels.join(', ')})`,
    hsl: `hsl(${round(h)}, ${round(s * 100)}%, ${round(l * 100)}%)`,
  }
}
