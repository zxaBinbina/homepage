export type CleaningMode = 'precise' | 'broad' | 'fields'
export type JsonValue = null | boolean | number | string | JsonValue[] | JsonObject
type JsonObject = { [key: string]: JsonValue }
export interface CleaningResult {
  inputLines: number
  outputLines: number | null
  removedLines: number | null
  modifiedLines: number
  invalidLines: number
  issues: { line: number; message: string }[]
  output: string
}

export const MAX_INPUT_BYTES = 20 * 1024 * 1024
const MAX_ISSUES = 100
const isObject = (value: JsonValue): value is JsonObject =>
  value !== null && typeof value === 'object' && !Array.isArray(value)
const isReasoning = (value: JsonObject) => value.type === 'reasoning' || value.type === 'Reasoning'

function containsSensitiveObject(value: JsonValue): boolean {
  const pending = [value]
  while (pending.length) {
    const item = pending.pop()!
    if (Array.isArray(item)) {
      for (const child of item) pending.push(child)
    } else if (isObject(item)) {
      if (Object.hasOwn(item, 'encrypted_content') || isReasoning(item)) return true
      // A loop also supports arrays/objects wider than the argument limit.
      for (const child of Object.values(item)) pending.push(child)
    }
  }
  return false
}

// undefined is a removal marker; actual JSON nulls and empty objects are retained.
function stripFields(value: JsonValue, depth = 0): JsonValue | undefined {
  if (depth > 256) throw new Error('嵌套超过 256 层，请简化该事件后重试。')
  if (Array.isArray(value)) {
    const result: JsonValue[] = []
    for (const child of value) {
      const cleaned = stripFields(child, depth + 1)
      if (cleaned !== undefined) result.push(cleaned)
    }
    return result
  }
  if (!isObject(value)) return value
  if (isReasoning(value)) return undefined
  const result: JsonObject = Object.create(null)
  for (const [key, child] of Object.entries(value)) {
    if (key === 'encrypted_content' || key === 'reasoning') continue
    const cleaned = stripFields(child, depth + 1)
    if (cleaned !== undefined) result[key] = cleaned
  }
  return result
}

export function cleanJsonl(input: string, mode: CleaningMode = 'precise'): CleaningResult {
  if (!['precise', 'broad', 'fields'].includes(mode)) throw new Error('请选择有效的清理模式。')
  if (input.length > MAX_INPUT_BYTES || new TextEncoder().encode(input).length > MAX_INPUT_BYTES)
    throw new Error('输入请控制在 20 MB 以内。')

  // Accept UTF-8 BOM and Windows line endings. A final newline terminates the last
  // record; internal blank lines are invalid JSONL and keep their physical number.
  const source = input.replace(/^\uFEFF/, '')
  const lines = source ? source.split(/\r\n|\n|\r/) : []
  if (lines.at(-1) === '') lines.pop()
  const result: CleaningResult = {
    inputLines: lines.length,
    outputLines: null,
    removedLines: null,
    modifiedLines: 0,
    invalidLines: 0,
    issues: [],
    output: '',
  }
  const output: string[] = []
  for (const [index, line] of lines.entries()) {
    try {
      if (!line.trim()) throw new Error('空行不是 JSON 事件，请删除该空行。')
      let event: JsonValue
      try {
        event = JSON.parse(line)
      } catch {
        // Do not echo input snippets (which may contain secrets) in diagnostics.
        throw new Error('JSON 语法无效，请检查引号、逗号或是否跨行。')
      }
      if (!isObject(event)) throw new Error('每行必须是一个 JSON 事件对象。')
      if (mode === 'fields') {
        const cleaned = stripFields(event) ?? {}
        const serialized = JSON.stringify(cleaned)
        if (serialized !== JSON.stringify(event)) result.modifiedLines++
        output.push(serialized)
      } else {
        const remove =
          mode === 'broad'
            ? /encrypted_content|reasoning/i.test(line)
            : /"type"\s*:\s*"(?:reasoning|Reasoning)"/.test(line) ||
              /"encrypted_content"/.test(line) ||
              containsSensitiveObject(event)
        if (!remove) output.push(line)
      }
    } catch (error) {
      result.invalidLines++
      if (result.issues.length < MAX_ISSUES)
        result.issues.push({
          line: index + 1,
          message: error instanceof Error ? error.message : '该行无法处理。',
        })
    }
  }
  // Fail the whole export instead of silently losing malformed records, even
  // when a malformed line happens to contain a filtering keyword.
  if (result.invalidLines) return result
  result.outputLines = output.length
  result.removedLines = lines.length - output.length
  result.output = output.length ? `${output.join('\n')}\n` : ''
  return result
}
