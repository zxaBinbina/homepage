import {
  Chess,
  newChess,
  playChess,
  chessResult,
  chooseChess,
  squareAt,
  squareIndex,
  pieceNames,
  type ChessState,
  type ChessTurn,
} from '../chess'
import {
  newXiangqi,
  applyChessMove,
  legalChessMoves,
  chessOutcome,
  chessName,
  chooseXiangqi,
} from '../xiangqi'
import { winningLine, chooseGomoku } from '../gomoku'
import { newGo, playGo, passGo, goGroup, scoreGo, chooseGo, type GoState } from '../go'
import {
  newDoudizhu,
  bid,
  playDoudizhu,
  chooseComputer,
  computerBid,
  type DDState,
} from '../doudizhu'
import {
  newJunqi,
  moveJunqi,
  canPlaceJunqi,
  canMove,
  chooseJunqi,
  rankNames,
  type JState,
} from '../junqi'
import {
  createJunqiKnowledge,
  advanceJunqiKnowledge,
  observeJunqi,
  chooseJunqiChallenge,
  type JKnowledge,
} from '../junqiKnowledge'
import type { OnlineKind, RoomSettings, RoomCommand, GameView } from './types'

type GridState = { board: number[]; turn: number; quiet: number; positions: string[] }
type Position = GridState | ChessState | GoState | DDState | JState
type PositionSnapshot = {
  position: Position
  positionCount: number
  last: GameView['last']
  knowledge: JKnowledge | null
  ply: number
}
export type OnlineGame = {
  kind: OnlineKind
  position: Position
  last: GameView['last']
  ply: number
  result: GameView['result']
  history: { seat: number; before: PositionSnapshot }[]
  setupReady: number[]
  dead: number[]
  scoreReady: number[]
  knowledge: JKnowledge | null
}
const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value))
const sideOf = (seat: number) => (seat === 0 ? 1 : -1)
export function newOnlineGame(kind: OnlineKind): OnlineGame {
  const position: Position =
    kind === 'chess'
      ? newChess()
      : kind === 'go'
        ? newGo()
        : kind === 'doudizhu'
          ? newDoudizhu()
          : kind === 'junqi'
            ? newJunqi()
            : {
                board: kind === 'xiangqi' ? newXiangqi() : Array<number>(225).fill(0),
                turn: 1,
                quiet: 0,
                positions: [],
              }
  if (kind === 'xiangqi')
    (position as GridState).positions = [(position as GridState).board.join(',') + ':1']
  return {
    kind,
    position,
    last: null,
    ply: 0,
    result: null,
    history: [],
    setupReady: [],
    dead: [],
    scoreReady: [],
    knowledge: kind === 'junqi' ? createJunqiKnowledge(position as JState) : null,
  }
}
export function gameStatus(game: OnlineGame): GameView['status'] {
  if (game.result) return 'finished'
  if (game.kind === 'junqi' && game.setupReady.length < 2) return 'setup'
  if (game.kind === 'go' && (game.position as GoState).passes >= 2) return 'scoring'
  return 'playing'
}
export function gameTurn(game: OnlineGame) {
  if (game.kind === 'doudizhu') return (game.position as DDState).turn
  if (game.kind === 'chess')
    return new Chess((game.position as ChessState).fen).turn() === 'w' ? 0 : 1
  return (game.position as GridState | GoState | JState).turn === 1 ? 0 : 1
}
export function undoAllowed(game: OnlineGame, settings: RoomSettings, seat: number) {
  return (
    settings.undo !== 'disabled' &&
    game.kind !== 'doudizhu' &&
    !(game.kind === 'junqi' && settings.junqi === 'hidden') &&
    game.history.some((h) => h.seat === seat) &&
    gameStatus(game) !== 'setup'
  )
}
function remember(game: OnlineGame, seat: number, settings: RoomSettings) {
  if (game.kind === 'doudizhu' || (game.kind === 'junqi' && settings.junqi === 'hidden')) return
  const position = clone(game.position)
  const positionCount = 'positions' in position ? position.positions.length : 0
  if ('positions' in position) position.positions = []
  game.history.push({
    seat,
    before: { position, positionCount, last: clone(game.last), knowledge: null, ply: game.ply },
  })
  if (game.history.length > (game.kind === 'junqi' ? 20 : 100)) game.history.shift()
}
export function undoOnlineGame(game: OnlineGame, seat: number) {
  let index = game.history.length - 1
  while (index >= 0 && game.history[index]!.seat !== seat) index--
  if (index < 0) throw new Error('还没有可以撤回的走法。')
  const before = game.history[index]!.before
  const positions =
    'positions' in game.position ? game.position.positions.slice(0, before.positionCount) : []
  game.position = clone(before.position)
  if ('positions' in game.position) game.position.positions = positions
  game.last = clone(before.last)
  game.knowledge = game.kind === 'junqi' ? createJunqiKnowledge(game.position as JState) : null
  game.ply = before.ply
  game.history = game.history.slice(0, index)
  game.dead = []
  game.scoreReady = []
  game.result = null
}
function finish(game: OnlineGame, winner: number, message: string) {
  game.result = { winners: winner ? [winner === 1 ? 0 : 1] : [], message }
}
export function resignOnlineGame(game: OnlineGame, seat: number) {
  if (game.result) return
  if (game.kind === 'doudizhu') return
  finish(game, -sideOf(seat), '对手离开或未能及时重连，本局结束。')
}
export function actOnlineGame(
  game: OnlineGame,
  settings: RoomSettings,
  seat: number,
  action: RoomCommand,
) {
  if (game.result) throw new Error('本局已经结束。')
  const status = gameStatus(game)
  if (status === 'setup') {
    if (game.setupReady.includes(seat)) throw new Error('你已确认布阵，请等待对手。')
    if (action.type === 'setup-ready') {
      game.setupReady.push(seat)
      return
    }
    if (action.type !== 'move') throw new Error('请先完成布阵。')
    const state = game.position as JState
    const a = state.board[action.from ?? -1],
      b = state.board[action.to ?? -1]
    if (
      !a ||
      !b ||
      a.side !== sideOf(seat) ||
      b.side !== sideOf(seat) ||
      !canPlaceJunqi(a, action.to!) ||
      !canPlaceJunqi(b, action.from!)
    )
      throw new Error('这两枚棋子的位置不符合布阵要求。')
    const board = [...state.board]
    ;[board[action.from!]!, board[action.to!]!] = [b, a]
    game.position = { ...state, board }
    game.knowledge = createJunqiKnowledge(game.position)
    return
  }
  if (status === 'scoring') {
    const state = game.position as GoState
    if (action.type === 'dead') {
      const at = action.to ?? -1
      if (!Number.isInteger(at) || !state.board[at]) throw new Error('请点选需要标记的棋子。')
      const group = goGroup(state.board, at).stones
      game.dead = game.dead.includes(at)
        ? game.dead.filter((n) => !group.includes(n))
        : [...new Set([...game.dead, ...group])]
      game.scoreReady = []
    } else if (action.type === 'score') {
      if (!game.scoreReady.includes(seat)) game.scoreReady.push(seat)
      if (game.scoreReady.length === 2) {
        const score = scoreGo(state.board, game.dead)
        finish(game, score.winner, '黑棋 ' + score.black + ' 目，白棋 ' + score.white + ' 目。')
      }
    } else if (action.type === 'resume-play') {
      game.position = { ...state, passes: 0 }
      game.dead = []
      game.scoreReady = []
    } else throw new Error('请双方核对死子并确认数子，或继续对局。')
    return
  }
  if (action.type !== 'move' || gameTurn(game) !== seat) throw new Error('还没有轮到你。')
  const side = sideOf(seat),
    to = action.to ?? -1,
    from = action.from ?? -1
  let next: Position | null = null
  if (game.kind === 'xiangqi') {
    const state = game.position as GridState
    if (!legalChessMoves(state.board, side).some((m) => m.from === from && m.to === to))
      throw new Error('这个走法不合法。')
    const board = applyChessMove(state.board, { from, to })
    next = {
      board,
      turn: -side,
      quiet: state.board[to] ? 0 : state.quiet + 1,
      positions: [...state.positions, board.join(',') + ':' + -side],
    }
  } else if (game.kind === 'gomoku') {
    const state = game.position as GridState
    if (!Number.isInteger(to) || to < 0 || to >= 225 || state.board[to])
      throw new Error('请在空交点落子。')
    const board = [...state.board]
    board[to] = side
    next = { ...state, board, turn: -side }
  } else if (game.kind === 'chess') {
    if (
      !Number.isInteger(from) ||
      !Number.isInteger(to) ||
      from < 0 ||
      from > 63 ||
      to < 0 ||
      to > 63
    )
      throw new Error('请选择棋盘内的位置。')
    if (action.promotion && !['q', 'r', 'b', 'n'].includes(action.promotion))
      throw new Error('请选择正确的升变棋子。')
    next = playChess(
      game.position as ChessState,
      {
        from: squareAt(from),
        to: squareAt(to),
        ...(action.promotion ? { promotion: action.promotion } : {}),
      } as ChessTurn,
    )
  } else if (game.kind === 'go') {
    const state = game.position as GoState
    const move = to === -1 ? { state: passGo(state) } : playGo(state, to)
    if ('error' in move) throw new Error(move.error)
    next = move.state
  } else if (game.kind === 'doudizhu') {
    const state = game.position as DDState
    if (state.landlord === -1) next = bid(state, action.bid ?? -1)
    else {
      if (
        !Array.isArray(action.cards) ||
        action.cards.length > 20 ||
        new Set(action.cards).size !== action.cards.length
      )
        throw new Error('请选择正确的手牌。')
      const cards = action.cards.map((id) => state.hands[seat]!.find((c) => c.id === id))
      if (cards.some((c) => !c)) throw new Error('只能使用自己的手牌。')
      next = playDoudizhu(state, cards as DDState['last'])
    }
  } else {
    next = moveJunqi(game.position as JState, from, to)
  }
  if (!next) throw new Error('这个操作不符合当前游戏规则。')
  remember(game, seat, settings)
  if (game.kind === 'junqi')
    game.knowledge = advanceJunqiKnowledge(
      game.knowledge!,
      game.position as JState,
      next as JState,
      from,
      to,
    )
  game.position = next
  game.ply++
  game.last = ['doudizhu'].includes(game.kind) || to === -1 ? null : { from, to }
  if (game.kind === 'xiangqi') {
    const state = next as GridState,
      winner = chessOutcome(state.board, state.turn)
    if (winner) finish(game, winner, '本局已分出胜负。')
    else if (
      state.quiet >= 120 ||
      state.positions.filter((p) => p === state.positions.at(-1)).length >= 3
    )
      finish(game, 0, '本局和棋。')
  } else if (game.kind === 'gomoku') {
    const state = next as GridState
    if (winningLine(state.board, to).length) finish(game, side, '五子连成一线，本局结束。')
    else if (state.board.every(Boolean)) finish(game, 0, '棋盘已满，本局和棋。')
  } else if (game.kind === 'chess') {
    const result = chessResult(next as ChessState)
    if (result) finish(game, result.winner, result.reason + '。')
  } else if (game.kind === 'junqi' && (next as JState).finished)
    finish(game, (next as JState).finished, '本局已分出胜负。')
  else if (game.kind === 'doudizhu') {
    const state = next as DDState
    if (state.finished !== null)
      game.result = {
        winners:
          state.finished === state.landlord
            ? [state.landlord]
            : [0, 1, 2].filter((s) => s !== state.landlord),
        message:
          (state.finished === state.landlord ? '地主' : '农民') +
          '获胜 · 本局 ' +
          state.multiplier +
          ' 倍。',
      }
    else if (state.bidCount === 3 && state.landlord === -1) {
      game.position = newDoudizhu()
      game.last = null
    }
  }
}
export function automaticAction(game: OnlineGame, settings: RoomSettings): RoomCommand {
  const base: RoomCommand = { type: 'move', revision: 0 }
  const seat = gameTurn(game),
    side = sideOf(seat)
  if (game.kind === 'gomoku') {
    const to = chooseGomoku((game.position as GridState).board, side, 0, 50)
    if (to === null) throw new Error('没有合法走法。')
    return { ...base, to }
  }
  if (game.kind === 'xiangqi')
    return { ...base, ...chooseXiangqi((game.position as GridState).board, side, 0, 50) }
  if (game.kind === 'chess') {
    const move = chooseChess(game.position as ChessState, 0)
    if (!move) throw new Error('没有合法走法。')
    return {
      ...base,
      from: squareIndex(move.from),
      to: squareIndex(move.to),
      promotion: move.promotion,
    }
  }
  if (game.kind === 'go') return { ...base, to: chooseGo(game.position as GoState, 0) }
  if (game.kind === 'doudizhu') {
    const state = game.position as DDState
    return state.landlord === -1
      ? { ...base, bid: computerBid(state.hands[seat]!, Math.max(...state.bids)) }
      : { ...base, cards: chooseComputer(state).map((c) => c.id) }
  }
  const state = game.position as JState
  // Reorient the open-board AI; hidden-board AI receives only this seat's observations.
  const move =
    settings.junqi === 'hidden'
      ? chooseJunqiChallenge(observeJunqi(state, side, game.knowledge!), {})
      : chooseJunqi({ ...state, turn: side })
  if (!move) throw new Error('没有合法走法。')
  return { ...base, from: move[0], to: move[1] }
}
export function projectGame(
  game: OnlineGame,
  settings: RoomSettings,
  seat: number,
  privateView = true,
): GameView {
  const status = gameStatus(game),
    turn = gameTurn(game),
    side = sideOf(seat)
  const view: GameView = {
    board: [],
    columns: 0,
    turn,
    status,
    last: game.last,
    targets: {},
    promotions: {},
    ply: game.ply,
    result: game.result,
    setupReady: game.setupReady,
    dead: game.dead,
    scoreReady: game.scoreReady,
    score: null,
    hand: [],
    counts: [],
    bottom: [],
    lastCards: [],
    lastPlayer: -1,
    landlord: -1,
    bids: [],
    multiplier: 1,
    canPass: false,
    canUndo: privateView && undoAllowed(game, settings, seat),
    hint: [],
  }
  if (game.kind === 'doudizhu') {
    const state = game.position as DDState
    view.hand = privateView ? state.hands[seat]! : []
    view.counts = state.hands.map((h) => h.length)
    view.bottom = state.landlord === -1 ? [] : state.bottom
    view.lastCards = state.last
    view.lastPlayer = state.lastPlayer
    view.landlord = state.landlord
    view.bids = state.bids
    view.multiplier = state.multiplier
    view.canPass = !!state.last.length && state.lastPlayer !== seat
    if (privateView && turn === seat && state.landlord !== -1 && !game.result)
      view.hint = chooseComputer(state).map((c) => c.id)
    return view
  }
  if (game.kind === 'chess') {
    const state = game.position as ChessState,
      chess = new Chess(state.fen)
    view.columns = 8
    view.board = chess
      .board()
      .flat()
      .map((piece) =>
        piece
          ? { side: piece.color === 'w' ? 1 : -1, label: pieceNames[piece.type], piece: piece.type }
          : null,
      )
    if (privateView && turn === seat && status === 'playing')
      for (const move of chess.moves({ verbose: true })) {
        const from = squareIndex(move.from),
          to = squareIndex(move.to)
        ;(view.targets[from] ??= []).push(to)
        if (move.promotion) (view.promotions[from + ':' + to] ??= []).push(move.promotion)
      }
  } else if (game.kind === 'junqi') {
    const state = game.position as JState
    const observation = observeJunqi(state, side, game.knowledge!)
    view.columns = 5
    view.board = state.board.map((piece, at) => {
      if (!piece) return null
      const rank =
        settings.junqi === 'open' ? piece.rank : privateView ? observation.board[at]?.rank : null
      return {
        side: piece.side,
        label: rank == null ? '暗棋' : rankNames[rank]!,
        hidden: rank == null,
      }
    })
    if (privateView && status === 'setup' && !game.setupReady.includes(seat))
      state.board.forEach((piece, from) => {
        if (piece?.side !== side) return
        view.targets[from] = state.board.flatMap((other, to) =>
          other?.side === side &&
          from !== to &&
          canPlaceJunqi(piece, to) &&
          canPlaceJunqi(other, from)
            ? [to]
            : [],
        )
      })
    if (privateView && status === 'playing' && turn === seat)
      state.board.forEach((piece, from) => {
        if (piece?.side !== side) return
        // Only public reachability is sent; combat ranks never leave the server.
        view.targets[from] = state.board.flatMap((_, to) => (canMove(state, from, to) ? [to] : []))
      })
  } else {
    const state = game.position as GridState | GoState
    view.columns = game.kind === 'gomoku' ? 15 : 9
    view.board = state.board.map((piece) =>
      piece
        ? {
            side: game.kind === 'xiangqi' ? Math.sign(piece) : piece,
            label: game.kind === 'xiangqi' ? chessName(piece) : piece === 1 ? '黑棋' : '白棋',
          }
        : null,
    )
    if (game.kind === 'xiangqi' && privateView && turn === seat && status === 'playing')
      for (const move of legalChessMoves(state.board, side))
        (view.targets[move.from] ??= []).push(move.to)
    if (game.kind === 'go') {
      if (status === 'scoring' || status === 'finished')
        view.score = scoreGo(state.board, game.dead)
      if (privateView && turn === seat && status === 'playing')
        view.targets[-1] = state.board.flatMap((stone, to) =>
          !stone && !('error' in playGo(state as GoState, to)) ? [to] : [],
        )
    } else if (game.kind === 'gomoku')
      view.targets[-1] = state.board.flatMap((stone, to) => (!stone ? [to] : []))
  }
  return view
}
