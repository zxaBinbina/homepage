export const gameCatalog = {
  twenty48: {
    name: '2048',
    label: 'MERGE THE NUMBERS',
    category: '数字益智',
    description: '让相同的数字相遇，一步步合成 2048。每一次移动，都是新的可能。',
    controls: '方向键 / 滑动 / 按钮',
  },
  minesweeper: {
    name: '扫雷',
    label: 'ONE SAFE STEP',
    category: '逻辑推理',
    description: '从一个数字推理下一步，在方格之间找出所有安全的位置。',
    controls: '点击翻开 / 插旗标记',
  },
  solitaire: {
    name: '纸牌接龙',
    label: 'A LITTLE PATIENCE',
    category: '经典纸牌',
    description: '红黑交替，慢慢理顺。把一副打乱的牌，收成四叠完整的花色。',
    controls: '翻一张 / 点击选牌与放置',
  },
} as const

export type GameId = keyof typeof gameCatalog
export const gameIds = Object.keys(gameCatalog) as GameId[]
export function isGameId(value: unknown): value is GameId {
  return typeof value === 'string' && Object.hasOwn(gameCatalog, value)
}
