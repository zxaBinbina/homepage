// Adapted from jaywcjlove/tools packages/json-xml (MIT).
import { XMLParser, XMLBuilder, XMLValidator } from 'fast-xml-parser'
const options = {
  ignoreAttributes: false,
  attributeNamePrefix: '@_',
  textNodeName: '#text',
  processEntities: false,
}
export function transform(input, { mode = 'encode' } = {}) {
  if (mode === 'decode') {
    if (/<!DOCTYPE|<!ENTITY/i.test(input)) throw new Error('请移除 DTD 与自定义实体后重试。')
    const result = XMLValidator.validate(input)
    if (result !== true) throw new Error(`XML 第 ${result.err.line} 行：${result.err.msg}`)
    return JSON.stringify(new XMLParser(options).parse(input), null, 2)
  }
  const value = JSON.parse(input)
  if (!value || Array.isArray(value) || typeof value !== 'object')
    throw new Error('请输入包含根节点的 JSON 对象。')
  const output = new XMLBuilder({ ...options, format: true }).build(value)
  const result = XMLValidator.validate(output)
  if (result !== true) throw new Error('JSON 中含有无法用作 XML 标签的键名。')
  return output
}
