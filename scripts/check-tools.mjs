import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
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
  convertRadix,
  hashAlgorithms,
  hashText,
  escapeHtml,
  parseJwt,
  generatePasswords,
  convertColor,
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
const huge = '1234567890123456789012345678901234567890'
assert.equal(convertRadix(huge, 10, 16), BigInt(huge).toString(16).toUpperCase())
assert.equal(convertRadix(convertRadix(huge, 10, 36), 36, 10), huge)
assert.equal(convertRadix('-0xFF', 16, 10), '-255')
assert.equal(convertRadix('+0b1010', 2, 8), '12')
assert.equal(convertRadix('0o77', 8, 10), '63')
assert.equal(convertRadix('-0', 10, 2), '0')
assert.equal(convertRadix('z', 36, 10), '35')
for (const input of ['', '2', '1.1', '1 0', '0x10', '1'.repeat(4097)])
  assert.throws(() => convertRadix(input, 2, 10))
for (const base of [1, 37, 2.5, NaN]) {
  assert.throws(() => convertRadix('10', base, 10))
  assert.throws(() => convertRadix('10', 10, base))
}

for (const algorithm of hashAlgorithms) {
  for (const input of ['', 'abc', '你好 🌍\n'])
    assert.equal(
      await hashText(input, algorithm),
      createHash(algorithm.replace('-', '')).update(input).digest('hex'),
    )
}
await assert.rejects(() => hashText('abc', 'unsupported'))
await assert.rejects(() => hashText('a'.repeat(1_000_001), 'SHA-256'))
assert.equal(
  escapeHtml('<p title="a & b">\'中文\'</p>'),
  '&lt;p title=&quot;a &amp; b&quot;&gt;&#39;中文&#39;&lt;/p&gt;',
)
assert.equal(escapeHtml('&amp;'), '&amp;amp;')

const jwt = (payload, header = '{"alg":"HS256"}', signature = 'c2FtcGxl') =>
  [header, payload]
    .map((value) => encodeBase64(value, true))
    .concat(signature)
    .join('.')
const report = parseJwt(
  jwt('{"sub":900719925474099312345,"name":"中文","iat":0,"exp":100,"nbf":50}'),
  50000,
)
assert.match(report, /900719925474099312345/)
assert.match(report, /中文/)
assert.match(report, /1970-01-01T00:00:00.000Z/)
assert.match(report, /签名：未验证/)
assert.match(report, /exp：尚未到期/)
assert.match(parseJwt(jwt('{"exp":100}'), 100000), /exp：已过期/)
assert.match(parseJwt(jwt('{"nbf":100}'), 99999), /nbf：尚未到开始时间/)
assert.match(parseJwt(jwt('{"exp":"100"}')), /不是可显示的数字时间戳/)
assert.match(parseJwt(jwt('{}', '{"alg":"none"}', '')), /签名：未验证/)
for (const token of [
  'abc',
  'a.b.c',
  'a.b.c.d',
  jwt('[]'),
  jwt('null'),
  jwt('{}', '{}'),
  jwt('{}', '{"alg":"HS256"}', ''),
  jwt('{bad}'),
])
  assert.throws(() => parseJwt(token))

const options = {
  length: 20,
  count: 50,
  lowercase: true,
  uppercase: true,
  numbers: true,
  symbols: true,
  excludeSimilar: true,
}
const passwords = generatePasswords(options).split('\n')
assert.equal(passwords.length, 50)
assert.equal(new Set(passwords).size, 50)
for (const value of passwords) {
  assert.equal(value.length, 20)
  for (const pattern of [/[a-z]/, /[A-Z]/, /[0-9]/, /[^a-zA-Z0-9]/]) assert.match(value, pattern)
  assert.doesNotMatch(value, /[0Oo1Il|]/)
}
assert.match(
  generatePasswords({
    ...options,
    length: 8,
    count: 1,
    lowercase: false,
    uppercase: false,
    symbols: false,
  }),
  /^[2-9]{8}$/,
)
assert.equal(generatePasswords({ ...options, length: 128, count: 1 }).length, 128)
for (const patch of [
  { length: 7 },
  { length: 129 },
  { length: 8.5 },
  { count: 0 },
  { count: 51 },
  { count: NaN },
  { lowercase: false, uppercase: false, numbers: false, symbols: false },
])
  assert.throws(() => generatePasswords({ ...options, ...patch }))

assert.deepEqual(convertColor('#f00'), {
  hex: '#FF0000',
  rgb: 'rgb(255, 0, 0)',
  hsl: 'hsl(0, 100%, 50%)',
})
assert.equal(convertColor('rgb(0, 255, 0)').hsl, 'hsl(120, 100%, 50%)')
assert.equal(convertColor('hsl(-120deg, 100%, 50%)').hex, '#0000FF')
assert.equal(convertColor('hsl(720, 100%, 50%)').hex, '#FF0000')
assert.equal(convertColor('#000').hsl, 'hsl(0, 0%, 0%)')
assert.equal(convertColor('#fff').hsl, 'hsl(0, 0%, 100%)')
for (const color of ['4ea4ef', '#abcdef', '#808080', '#fefefe', '#010101']) {
  const result = convertColor(color)
  assert.equal(convertColor(result.rgb).hex, result.hex)
  assert.equal(convertColor(result.hsl).hex, result.hex)
}
for (const color of [
  '',
  'red',
  '#ffff',
  '#gggggg',
  'rgb(256, 0, 0)',
  'rgb(-1, 0, 0)',
  'rgb(1.5, 0, 0)',
  'hsl(0, 101%, 50%)',
  'hsl(0, 0%, -1%)',
])
  assert.throws(() => convertColor(color))
console.log(
  'Tools: all 12 tools, Unicode and precision, time zones/DST, hash vectors, JWT fields, password constraints, color conversion and invalid inputs passed. HTML decoding is covered in the browser check.',
)
