// Adapted from jaywcjlove/tools packages/chinese-pinyin-conversion (MIT).
// pinyin-pro supplies the browser dictionary without the Node-only segmentation dependency.
import { pinyin } from 'pinyin-pro'
export function annotate(input, style = 'tone') {
  return pinyin(input, { type: 'all', toneType: style === 'tone' ? 'symbol' : 'none' }).map(
    (item) => ({ hans: item.origin, py: style === 'first' ? item.first : item.pinyin }),
  )
}
export function transform(input, { style = 'tone' } = {}) {
  return annotate(input, style)
    .map((item) => item.py)
    .join(' ')
    .replace(/[。，（）]/g, (char) => ({ '。': '.', '，': ',', '（': '(', '）': ')' })[char])
}
