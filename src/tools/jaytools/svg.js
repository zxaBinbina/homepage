// Adapted from jaywcjlove/tools packages/svg-optimizer/src/compress.ts (MIT).
import { optimize } from 'svgo/browser'
export function compress(input, settings = {}) {
  const precision = Number(settings.floatPrecision ?? 3)
  if (!Number.isInteger(precision) || precision < 1 || precision > 8)
    throw new Error('精度应为 1–8 的整数。')
  const result = optimize(input, {
    multipass: settings.multipass ?? true,
    floatPrecision: precision,
    plugins: [
      { name: 'preset-default', params: { overrides: { removeDesc: false, cleanupIds: false } } },
      ...(settings.removeDimensions ? ['removeDimensions'] : []),
    ],
    js2svg: { indent: 2, pretty: settings.pretty ?? false },
  })
  return result.data
}
