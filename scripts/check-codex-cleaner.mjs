import assert from 'node:assert/strict'
import { build } from 'esbuild'

const bundle = await build({
  entryPoints: ['src/tools/codex/cleaner.ts'],
  bundle: true,
  format: 'esm',
  write: false,
})
const { cleanJsonl, MAX_INPUT_BYTES } = await import(
  `data:text/javascript;base64,${Buffer.from(bundle.outputFiles[0].text).toString('base64')}`
)
const records = [
  { type: 'message', content: '中文 🌍，普通正文与换行\n都应保留' },
  { type: 'reasoning', summary: ['内部内容'] },
  { type: 'Reasoning', summary: ['内部内容'] },
  { type: 'response_item', payload: { type: 'reasoning', encrypted_content: 'secret' } },
  { type: 'message', payload: { encrypted_content: 'secret', content: '保留正文' } },
  { type: 'turn_context', reasoning_effort: 'high', usage: { reasoning_output_tokens: 42 } },
  { type: 'message', content: '正文提及 reasoning 应在精确模式保留' },
  { type: 'event_msg', reasoning: '删字段时移除', safe: true },
  { type: 'message', content: [null, { type: 'Reasoning', text: '删' }, { text: '保留' }] },
]
// Deliberately include whitespace around keys/values like a normal Codex export.
const input = records.map((r) => JSON.stringify(r).replaceAll(':', ': ')).join('\r\n') + '\r\n'
function output(result) {
  assert.equal(result.invalidLines, 0)
  assert.equal(result.outputLines + result.removedLines, result.inputLines)
  const lines = result.output ? result.output.trimEnd().split('\n') : []
  assert.equal(lines.length, result.outputLines)
  return lines.map((line) => JSON.parse(line))
}
const precise = cleanJsonl('\uFEFF' + input)
assert.deepEqual(output(precise), [records[0], records[5], records[6], records[7]])
assert.equal(precise.removedLines, 5)
assert.ok(precise.output.includes(': '), 'Line filtering must preserve surviving source text')
assert.deepEqual(output(cleanJsonl(input, 'broad')), [records[0]])
const fields = cleanJsonl(input, 'fields')
assert.deepEqual(output(fields), [
  records[0],
  {},
  {},
  { type: 'response_item' },
  { type: 'message', payload: { content: '保留正文' } },
  records[5],
  records[6],
  { type: 'event_msg', safe: true },
  { type: 'message', content: [null, { text: '保留' }] },
])
assert.equal(fields.removedLines, 0)
assert.equal(fields.modifiedLines, 6)

// Encoded keys/types, deeply nested arrays and __proto__ must not hide fields or
// alter unrelated data. Metadata alone is preserved outside broad mode.
assert.equal(cleanJsonl('{"payload":{"encrypted_\\u0063ontent":"s"}}').output, '')
assert.equal(cleanJsonl('{"type":"rea\\u0073oning"}').output, '')
assert.equal(cleanJsonl('{"text":"REASONING"}', 'broad').output, '')
assert.equal(cleanJsonl('{"text":"reasoning"}').removedLines, 0)
assert.equal(cleanJsonl('{"type":"reasoning","type":"message"}').removedLines, 1)
assert.deepEqual(output(cleanJsonl('{"__proto__":{"ok":1,"encrypted_content":"s"}}', 'fields')), [
  JSON.parse('{"__proto__":{"ok":1}}'),
])
const wide = { items: Array(150000).fill(null) }
assert.equal(output(cleanJsonl(JSON.stringify(wide))).length, 1)
const deep = '{"v":'.repeat(260) + '{}' + '}'.repeat(260)
assert.equal(cleanJsonl(deep, 'fields').invalidLines, 1)

for (const mode of ['precise', 'broad', 'fields']) {
  const invalid = cleanJsonl('{}\r\n{"encrypted_content":broken}\r\n\r\nnull\r\n[]\r\n{}\r\n', mode)
  assert.equal(invalid.inputLines, 6)
  assert.equal(invalid.invalidLines, 4)
  assert.deepEqual(
    invalid.issues.map((e) => e.line),
    [2, 3, 4, 5],
  )
  assert.equal(invalid.output, '')
  assert.equal(invalid.outputLines, null)
  assert.equal(invalid.removedLines, null)
  assert.ok(!JSON.stringify(invalid.issues).includes('encrypted_content'))
  assert.equal(cleanJsonl('bad\n'.repeat(120), mode).issues.length, 100)
  assert.equal(cleanJsonl('bad\n'.repeat(120), mode).invalidLines, 120)
  assert.equal(cleanJsonl('', mode).inputLines, 0)
  assert.equal(cleanJsonl('{}\n', mode).inputLines, 1)
  assert.equal(cleanJsonl('{}\n\n', mode).invalidLines, 1)
  assert.equal(cleanJsonl('\n', mode).invalidLines, 1)
}
assert.equal(cleanJsonl('{"encrypted_content":"s"}').outputLines, 0)
assert.throws(() => cleanJsonl('x'.repeat(MAX_INPUT_BYTES + 1)), /20 MB/)
assert.throws(() => cleanJsonl('中'.repeat(Math.ceil(MAX_INPUT_BYTES / 3))), /20 MB/)
assert.throws(() => cleanJsonl('{}', 'unknown'))
console.log(
  'Codex JSONL: modes, nested fields, metadata, line counts, validation, empty output and input limits passed.',
)
