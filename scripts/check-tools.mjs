import assert from 'node:assert/strict'
import { build } from 'esbuild'

const bundle = await build({
  entryPoints: ['src/tools/transform.ts'],
  bundle: true,
  format: 'esm',
  platform: 'browser',
  write: false,
})
const {
  formatJson,
  encodeBase64,
  decodeBase64,
  transformUrl,
  transformText,
  textStats,
  parseTimestamp,
  parseDateInput,
  dateInputValue,
  generateUuids,
} = await import(
  `data:text/javascript;base64,${Buffer.from(bundle.outputFiles[0].text).toString('base64')}`
)

const precise =
  '{"id":900719925474099312345,"tiny":1e-999,"negative":-0,"duplicate":1,"duplicate":2,"empty":[],"escaped":"a\\\"b\\n {} : ,"}'
assert.equal(formatJson(formatJson(precise), ''), precise)
assert.equal(
  formatJson('{"a":[1,{"b":true}],"c":null}'),
  '{\n  "a": [\n    1,\n    {\n      "b": true\n    }\n  ],\n  "c": null\n}',
)
for (const value of ['null', 'true', '42', '"中文"', '{}', '[]'])
  assert.equal(formatJson(value), value)
for (const value of ['', '{a:1}', '{"a":1,}', '[1,]', 'undefined'])
  assert.throws(() => formatJson(value))
assert.throws(() => formatJson('['.repeat(65) + '0' + ']'.repeat(65)), /64/)
assert.throws(() => encodeBase64('a'.repeat(1_000_001)), /100 万/)
for (const value of ['hello', '你好，世界🌍', '\uFEFF保留 BOM', 'a\0b', '']) {
  for (const safe of [false, true])
    assert.equal(decodeBase64(encodeBase64(value, safe), safe), value)
}
assert.equal(encodeBase64('hello'), 'aGVsbG8=')
assert.equal(decodeBase64('aG Vs\nbG8='), 'hello')
for (const value of ['a', 'a===', 'ab=c', 'aGVsbG8===', '###', '/w=='])
  assert.throws(() => decodeBase64(value))
assert.equal(encodeBase64('😀', true), '8J-YgA')
assert.equal(decodeBase64('8J-YgA', true), '😀')
assert.throws(() => decodeBase64('8J-YgA'))

const url = '你好 + &/?='
assert.equal(transformUrl(transformUrl(url, false, 'component'), true, 'component'), url)
assert.equal(
  transformUrl('https://example.com/中文?q=1&x=2', false, 'uri'),
  'https://example.com/%E4%B8%AD%E6%96%87?q=1&x=2',
)
assert.equal(transformUrl('%2F%3F%26', true, 'uri'), '%2F%3F%26')
assert.equal(transformUrl('a+b%2Bc', true, 'component', true), 'a b+c')
assert.equal(transformUrl('a+b', true, 'component'), 'a+b')
assert.throws(() => transformUrl('%E4%A', true, 'component'))
assert.equal(transformText('a\r\nb\ra\nA', 'deduplicate'), 'a\nb\nA')
assert.equal(transformText('  a  \n b ', 'trim'), 'a\nb')
assert.equal(transformText('\n  \na\n\t\nb\n', 'empty'), 'a\nb')
assert.equal(transformText('a彬B', 'upper'), 'A彬B')
assert.equal(transformText('a彬B', 'lower'), 'a彬b')
assert.deepEqual(textStats('🌍\n中'), { characters: 3, lines: 2 })
assert.deepEqual(textStats(''), { characters: 0, lines: 0 })

assert.equal(parseTimestamp('0', 'seconds').toISOString(), '1970-01-01T00:00:00.000Z')
assert.equal(parseTimestamp('-1', 'milliseconds').toISOString(), '1969-12-31T23:59:59.999Z')
assert.equal(parseTimestamp('1704067200', 'seconds').getTime(), 1704067200000)
for (const value of ['', '123abc', '1e3', '1.5', '999999999999999999999'])
  assert.throws(() => parseTimestamp(value, 'seconds'))
assert.equal(
  parseDateInput('2024-02-29T12:34:56.123', 'utc').toISOString(),
  '2024-02-29T12:34:56.123Z',
)
assert.equal(parseDateInput('0099-01-01T00:00', 'utc').getUTCFullYear(), 99)
for (const value of [
  '2023-02-29T12:00',
  '2024-13-01T00:00',
  '2024-01-01T24:00',
  '0000-01-01T00:00',
  '',
])
  assert.throws(() => parseDateInput(value, 'utc'))
process.env.TZ = 'Asia/Shanghai'
assert.equal(parseDateInput('2024-01-01T08:00', 'local').getTime(), 1704067200000)
assert.equal(dateInputValue(new Date(1704067200123), 'local'), '2024-01-01T08:00:00.123')
process.env.TZ = 'America/New_York'
assert.throws(() => parseDateInput('2024-03-10T02:30', 'local'), /日期不存在/)
assert.equal(parseDateInput('2024-11-03T01:30', 'local').toISOString(), '2024-11-03T05:30:00.000Z')

const ids = generateUuids(100).split('\n')
assert.equal(new Set(ids).size, 100)
assert.ok(
  ids.every((value) =>
    /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(value),
  ),
)
assert.match(generateUuids(1, true, false), /^[0-9A-F]{12}4[0-9A-F]{3}[89AB][0-9A-F]{15}$/)
for (const value of [0, -1, 101, 1.2, NaN]) assert.throws(() => generateUuids(value))
console.log(
  'Tools: lossless JSON, Unicode/Base64, URL modes, text operations, timestamp units/time zones/DST, UUID v4 and invalid inputs passed.',
)
