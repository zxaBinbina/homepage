// Adapted from jaywcjlove/tools packages/simplified-traditional-chinese (MIT).
import simplified from 'togscc/data/simplified.convert.json'
import traditional from 'togscc/data/traditional.convert.json'
export function transform(input, { mode = 'traditional' } = {}) {
  const map = mode === 'traditional' ? simplified : traditional
  return Array.from(input, (char) => {
    if (/[瞭乾藉麽]/.test(char)) return char
    const match = map[char]
    return (Array.isArray(match) ? match[0] : match) || char
  }).join('')
}
