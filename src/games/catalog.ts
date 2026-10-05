export const gameCatalog = {
  twenty48: {
    name: '2048',
    label: 'MERGE THE NUMBERS',
    category: '数字益智',
    description: '让相同的数字相遇，一步步合成 2048。每一次移动，都是新的可能。',
  },
  minesweeper: {
    name: '扫雷',
    label: 'ONE SAFE STEP',
    category: '逻辑推理',
    description: '从一个数字推理下一步，在方格之间找出所有安全的位置。',
  },
  solitaire: {
    name: '纸牌接龙',
    label: 'A LITTLE PATIENCE',
    category: '经典纸牌',
    description: '红黑交替，慢慢理顺。把一副打乱的牌，收成四叠完整的花色。',
  },
  tetris: {
    name: '经典俄罗斯方块黑白版',
    label: 'ROOM FOR ONE MORE',
    category: '方块挑战',
    description: '在极简黑白之间，旋转、堆叠、消除。用一局 30 行的小挑战，找回专注的节奏。',
  },
  sudoku: {
    name: '数独经典版',
    label: 'EVERY NUMBER BELONGS',
    category: '数字推理',
    description: '从一格空白开始，让每个数字各归其位。三档难度，留给自己一点安静思考的时间。',
  },
  xiangqi: {
    name: '中国象棋单机版',
    label: 'ACROSS THE RIVER',
    category: '棋艺策略',
    description: '楚河汉界，一步一思量。与电脑对弈，在车马炮之间练习谋划与取舍。',
  },
  gomoku: {
    name: '五子棋单机版',
    label: 'FIVE IN A ROW',
    category: '休闲对弈',
    description: '黑白交错，把五颗棋子连成一线。随时与电脑开一局，简单的规则也有巧妙的变化。',
  },
} as const

export type GameId = keyof typeof gameCatalog
export const gameIds = Object.keys(gameCatalog) as GameId[]
export function isGameId(value: unknown): value is GameId {
  return typeof value === 'string' && Object.hasOwn(gameCatalog, value)
}
