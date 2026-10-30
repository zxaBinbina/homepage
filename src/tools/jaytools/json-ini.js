// Adapted from jaywcjlove/tools packages/json-ini (MIT).
import ini from 'ini'
export function transform(input, { mode = 'encode' } = {}) {
  if (mode === 'decode') return JSON.stringify(ini.parse(input), null, 2)
  const value = JSON.parse(input)
  if (!value || Array.isArray(value) || typeof value !== 'object')
    throw new Error('请输入 JSON 对象。')
  return ini.stringify(value)
}
