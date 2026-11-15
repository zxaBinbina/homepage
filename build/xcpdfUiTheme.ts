// Only presentation colors are adapted. PDF ink and export color controls are excluded by the bridge.
const groups: Record<string, string[]> = {
  '--card-bg': ['fff', 'ffffff', '121c2b', '1c2b41'],
  '--bg': ['f1f5f9', 'fafbfc', 'f8fafc', 'fafafa', 'f9fafe', '0b1220'],
  '--border': [
    'eef2f6',
    'cbd5e1',
    'e2e8f0',
    'd1d5db',
    'd0d0d0',
    'bbb',
    'ccc',
    'ddd',
    'eee',
    '26374f',
  ],
  '--text': ['000', '000000', '0f172a', '334155', 'e6edf7'],
  '--text-secondary': [
    '94a3b8',
    '64748b',
    '475569',
    '555',
    '777',
    '888',
    '999',
    '808080',
    '9db0c7',
  ],
  '--primary': [
    '2563eb',
    '4f6ef7',
    '3498db',
    '9b59b6',
    '9650c8',
    'e67e22',
    'f39c12',
    '1d4ed8',
    '6366f1',
    '4f46e5',
    '4338ca',
    'b0b8e0',
    '1e40af',
    '3730a3',
    '60a5fa',
    '3b82f6',
    '93c5fd',
    '818cf8',
    '0891b2',
    '7c3aed',
    'db2777',
    'ea580c',
    '22d3ee',
    'a78bfa',
    'f472b6',
    'fb923c',
    'b45309',
    'f59e0b',
    'd97706',
    '92400e',
    'c2410c',
    '00f',
    '0000ff',
  ],
  '--primary-light': [
    'eff6ff',
    'e6f0ff',
    'dbeafe',
    'e0e7ff',
    'f0f9ff',
    'bfdbfe',
    '16233a',
    'cffafe',
    'ede9fe',
    'fce7f3',
    'ffedd5',
    'fff7ed',
  ],
  '--success': [
    '16a34a',
    '27ae60',
    '1abc9c',
    '2ecc71',
    '008000',
    '047857',
    '065f46',
    '34d399',
    '22c55e',
  ],
  '--success-light': ['f0fdf4', 'd1fae5'],
  '--danger': [
    'dc2626',
    'ef4444',
    'e53935',
    'c0392b',
    'e74c3c',
    'e74c5e',
    'dc2828',
    'b91c1c',
    'fca5a5',
    'f87171',
    'f00',
    'ff0000',
  ],
  '--danger-light': ['fee2e2', 'fff5f5'],
}

export const xcpdfUiColors = Object.fromEntries(
  Object.entries(groups).flatMap(([token, colors]) =>
    colors.map((color) => [
      `#${color.length === 3 ? [...color].map((part) => part + part).join('') : color}`,
      token,
    ]),
  ),
)

// This self-contained function also runs in the sandbox for newly rendered UI.
export function xcpdfUiValue(value: string, property: string, colors: Record<string, string>) {
  return value.replace(
    /#[\da-f]{3,8}\b|rgba?\([\d\s.,]+\)|\b(?:white|black|gray|red|green|blue)\b/gi,
    (literal) => {
      let color = literal.toLowerCase()
      let alpha = 1
      const named: Record<string, string> = {
        white: '#ffffff',
        black: '#000000',
        gray: '#888888',
        red: '#ff0000',
        green: '#008000',
        blue: '#0000ff',
      }
      color = named[color] || color
      if (color.startsWith('rgb')) {
        const channels = color.match(/[\d.]+/g)!.map(Number)
        color = `#${channels
          .slice(0, 3)
          .map((part) => part.toString(16).padStart(2, '0'))
          .join('')}`
        alpha = channels[3] ?? 1
      } else if (color.length === 4) {
        color = `#${[...color.slice(1)].map((part) => part + part).join('')}`
      }
      let token = colors[color]
      if (!token) return literal
      if (property.includes('shadow') && color === '#000000') token = '--shadow-color'
      else if (property === 'color' && token === '--card-bg') token = '--text'
      else if (property.startsWith('background')) {
        if (['--primary', '--success', '--danger'].includes(token)) token += '-light'
        else if (token === '--text') token = '--card-bg'
        else if (token === '--text-secondary') token = '--border'
      } else if (
        /border|outline/.test(property) &&
        ['--card-bg', '--bg', '--text-secondary'].includes(token)
      ) {
        token = '--border'
      }
      return alpha < 1
        ? `color-mix(in srgb, var(${token}) ${alpha * 100}%, transparent)`
        : `var(${token})`
    },
  )
}
