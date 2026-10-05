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
