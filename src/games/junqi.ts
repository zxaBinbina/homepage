export type JSide = 1 | -1
export type JPiece = { side: JSide; rank: number; id: number; flag?: boolean; mine?: boolean; bomb?: boolean }
export type JState = { board: (JPiece | null)[]; turn: JSide; selected: number | null; finished: 0 | JSide }
export const rows = 12
export const cols = 5
export const rankNames = ['地雷', '工兵', '排长', '连长', '营长', '团长', '旅长', '师长', '军长', '司令', '军旗']
export const camps = new Set([6, 8, 12, 16, 18, 41, 43, 47, 51, 53])
export const headquarters = new Set([1, 3, 56, 58])
export const rail = (at: number) => { const r = Math.floor(at / cols), c = at % cols; return r > 0 && r < rows - 1 && (c === 0 || c === 2 || c === 4 || r === 5 || r === 6) }
const pieces = [9, 8, 7, 7, 6, 6, 5, 5, 4, 4, 3, 3, 3, 2, 2, 2, 1, 1, 1, 0, 0, 0, 10, 1, 1]
export function newJunqi(random = Math.random): JState {
  const board: (JPiece | null)[] = Array(rows * cols).fill(null)
  for (const side of [1, -1] as JSide[]) {
    const home = side === 1 ? [6, 7, 8, 9, 10, 11] : [0, 1, 2, 3, 4, 5]
    const available = home.flatMap(r => Array.from({ length: cols }, (_, c) => r * cols + c)).filter(at => !camps.has(at))
    const shuffle = <T,>(values: T[]) => {
      const result = [...values]
      for (let i = result.length - 1; i > 0; i--) { const j = Math.floor(random() * (i + 1)); [result[i], result[j]] = [result[j]!, result[i]!] }
      return result
    }
    const flagAt = shuffle([...headquarters].filter(at => home.includes(Math.floor(at / cols))))[0]!
    const backRows = side === 1 ? [10, 11] : [0, 1]
    const mines = shuffle(available.filter(at => backRows.includes(Math.floor(at / cols)) && at !== flagAt)).slice(0, 3)
    const frontline = side === 1 ? 7 : 4
    const free = shuffle(available.filter(at => at !== flagAt && !mines.includes(at)))
    const bombSpots = free.filter(at => Math.floor(at / cols) !== frontline).slice(0, 2)
    const reserved = new Map<number, number>([[flagAt, 10], ...mines.map(at => [at, 0] as [number, number]), ...bombSpots.map(at => [at, 1] as [number, number])])
    const rest = shuffle(pieces.filter((rank, index) => rank !== 10 && (rank !== 0 || index < 22) && !(rank === 1 && index >= 22)))
    const slots = shuffle(available.filter(at => !reserved.has(at)))
    slots.forEach((at, i) => reserved.set(at, rest[i]!))
    available.forEach((at, i) => {
      const rank = reserved.get(at)!
      board[at] = { side, rank, id: i + (side === 1 ? 0 : 25), flag: rank === 10, mine: rank === 0, bomb: rank === 1 }
    })
  }
  return { board, turn: 1, selected: null, finished: 0 }
}
export function location(at: number) { return `第 ${Math.floor(at / cols) + 1} 行，第 ${(at % cols) + 1} 列` }
export function neighbors(at: number) { return [at - cols, at + cols, at - 1, at + 1].filter(n => n >= 0 && n < rows * cols && Math.abs((n % cols) - (at % cols)) + Math.abs(Math.floor(n / cols) - Math.floor(at / cols)) === 1) }
function clearRail(board: (JPiece | null)[], from: number, to: number) { if (Math.floor(from / cols) === Math.floor(to / cols)) { const step = from < to ? 1 : -1; for (let n = from + step; n !== to; n += step) if (board[n]) return false; return true } if (from % cols === to % cols) { const step = from < to ? cols : -cols; for (let n = from + step; n !== to; n += step) if (board[n]) return false; return true } return false }
export function canMove(state: JState, from: number, to: number) { const piece = state.board[from], target = state.board[to]; if (!piece || piece.side !== state.turn || piece.flag || piece.mine || target?.side === piece.side || (target && camps.has(to))) return false; if (camps.has(from) && target) return false; const dr = Math.abs(Math.floor(from / cols) - Math.floor(to / cols)), dc = Math.abs(from % cols - to % cols); if (dr === 1 && dc === 1 && (camps.has(from) || camps.has(to))) return true; const straight = dr === 0 || dc === 0; if (!straight) return piece.rank === 1 && rail(from) && rail(to) && engineerPath(state.board, from, to); if (rail(from) && rail(to)) return clearRail(state.board, from, to); return neighbors(from).includes(to) }
function engineerPath(board: (JPiece | null)[], from: number, to: number) { const queue = [from], seen = new Set([from]); while (queue.length) { const at = queue.shift()!; if (at === to) return true; for (const next of neighbors(at)) if (rail(next) && !seen.has(next) && (!board[next] || next === to)) { seen.add(next); queue.push(next) } } return false }
export function battle(attacker: JPiece, defender: JPiece) { if (defender.flag) return 'win'; if (attacker.bomb || defender.bomb) return 'both'; if (defender.mine) return attacker.rank === 1 ? 'win' : 'lose'; if (attacker.rank === defender.rank) return 'both'; return attacker.rank > defender.rank ? 'win' : 'lose' }
export function moveJunqi(state: JState, from: number, to: number): JState | null { if (!canMove(state, from, to)) return null; const board = [...state.board], attacker = board[from]!, defender = board[to]; board[from] = null; if (!defender) board[to] = attacker; else { const result = battle(attacker, defender); if (result === 'win') board[to] = attacker; else if (result === 'lose') board[to] = defender } if (defender?.flag && battle(attacker, defender) === 'win') return { board, turn: state.turn, selected: null, finished: state.turn }; const enemyHasFlag = board.some(p => p?.side === -state.turn && p.flag); return { board, turn: state.turn === 1 ? -1 : 1, selected: null, finished: enemyHasFlag ? 0 : state.turn } }
export function chooseJunqi(state: JState) { const moves: [number, number][] = []; state.board.forEach((piece, from) => { if (piece?.side !== state.turn) return; for (let to = 0; to < state.board.length; to++) if (canMove(state, from, to)) moves.push([from, to]) }); return moves.find(([, to]) => state.board[to]?.flag) ?? moves.find(([, to]) => state.board[to]?.side === -state.turn) ?? moves[0] ?? null }
