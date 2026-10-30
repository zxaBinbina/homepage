// Adapted from jaywcjlove/tools packages/amount-in-rmb (MIT).
import nzh from 'nzh'
export function transform(input) {
  const value = input.trim()
  if (!/^-?\d{1,16}(?:\.\d{1,2})?$/.test(value))
    throw new Error('请输入最多 16 位整数、2 位小数的金额，不要包含逗号。')
  // Keep the decimal string so long amounts do not lose precision through Number.
  return `中文小写：${nzh.cn.encodeS(value)}\n中文大写：${nzh.cn.encodeB(value)}\n人民币大写：${nzh.cn.toMoney(value)}`
}
