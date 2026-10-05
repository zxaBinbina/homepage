export type Card = { suit: number; rank: number; faceUp: boolean }
export type SolitaireGame = {
  stock: Card[]
  waste: Card[]
  foundations: Card[][]
  tableau: Card[][]
  moves: number
}
export type CardSource =
  | { kind: 'waste' }
  | { kind: 'tableau'; pile: number; index: number }
  | { kind: 'foundation'; pile: number }
export type CardTarget = { kind: 'tableau' | 'foundation'; pile: number }
export const suits = ['♠', '♥', '♣', '♦'] as const
export const suitNames = ['黑桃', '红桃', '梅花', '方块'] as const
export const redCard = (card: Card) => card.suit === 1 || card.suit === 3
export const rankName = (rank: number) =>
  ({ 1: 'A', 11: 'J', 12: 'Q', 13: 'K' })[rank] ?? String(rank)
export const cardName = (card: Card) => `${suitNames[card.suit]} ${rankName(card.rank)}`

export function newSolitaire(random = Math.random): SolitaireGame {
  const deck = Array.from({ length: 52 }, (_, i) => ({
    suit: Math.floor(i / 13),
    rank: (i % 13) + 1,
    faceUp: false,
  }))
  for (let i = deck.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1))
    ;[deck[i], deck[j]] = [deck[j]!, deck[i]!]
  }
  const tableau = Array.from({ length: 7 }, (_, pile) =>
    Array.from({ length: pile + 1 }, (_, i) => ({ ...deck.pop()!, faceUp: i === pile })),
  )
  return { stock: deck, waste: [], foundations: [[], [], [], []], tableau, moves: 0 }
}

function clone(game: SolitaireGame): SolitaireGame {
  const copy = (cards: Card[]) => cards.map((card) => ({ ...card }))
  return {
    stock: copy(game.stock),
    waste: copy(game.waste),
    foundations: game.foundations.map(copy),
    tableau: game.tableau.map(copy),
    moves: game.moves + 1,
  }
}

export function drawCard(game: SolitaireGame): SolitaireGame {
  if (!game.stock.length && !game.waste.length) return game
  const next = clone(game)
  if (next.stock.length) next.waste.push({ ...next.stock.pop()!, faceUp: true })
  else {
    next.stock = next.waste.reverse().map((card) => ({ ...card, faceUp: false }))
    next.waste = []
  }
  return next
}

export function sourceCards(game: SolitaireGame, source: CardSource): Card[] {
  if (source.kind === 'waste') return game.waste.slice(-1)
  if (source.kind === 'foundation') return game.foundations[source.pile]?.slice(-1) ?? []
  return game.tableau[source.pile]?.slice(source.index) ?? []
}

export function moveCard(
  game: SolitaireGame,
  source: CardSource,
  target: CardTarget,
): SolitaireGame | null {
  if (source.kind === target.kind && source.pile === target.pile) return null
  const cards = sourceCards(game, source)
  const first = cards[0]
  if (!first || cards.some((card) => !card.faceUp)) return null
  if (
    cards.some(
      (card, i) =>
        i > 0 && (cards[i - 1]!.rank !== card.rank + 1 || redCard(cards[i - 1]!) === redCard(card)),
    )
  )
    return null
  const destination =
    target.kind === 'foundation' ? game.foundations[target.pile] : game.tableau[target.pile]
  if (!destination) return null
  const top = destination.at(-1)
  if (target.kind === 'foundation') {
    if (cards.length !== 1 || first.suit !== target.pile || first.rank !== (top?.rank ?? 0) + 1)
      return null
  } else if (
    top
      ? !top.faceUp || top.rank !== first.rank + 1 || redCard(top) === redCard(first)
      : first.rank !== 13
  )
    return null
  const next = clone(game)
  if (source.kind === 'waste') next.waste.pop()
  else if (source.kind === 'foundation') next.foundations[source.pile]!.pop()
  else {
    next.tableau[source.pile]!.splice(source.index)
    const exposed = next.tableau[source.pile]!.at(-1)
    if (exposed) exposed.faceUp = true
  }
  const to =
    target.kind === 'foundation' ? next.foundations[target.pile]! : next.tableau[target.pile]!
  to.push(...cards.map((card) => ({ ...card })))
  return next
}

export const solitaireWon = (game: SolitaireGame) =>
  game.foundations.every((pile) => pile.length === 13)

/** Finish only after all hidden and draw-pile cards have been cleared. */
export const canFinish = (game: SolitaireGame) =>
  !solitaireWon(game) &&
  !game.stock.length &&
  !game.waste.length &&
  game.tableau.every((pile) => pile.every((card) => card.faceUp))
export function finishSolitaire(game: SolitaireGame): SolitaireGame {
  if (!canFinish(game)) return game
  let next = game
  for (let pass = 0; pass < 52; pass++) {
    const before = next
    for (let pile = 0; pile < 7; pile++) {
      const card = next.tableau[pile]!.at(-1)
      if (card)
        next =
          moveCard(
            next,
            { kind: 'tableau', pile, index: next.tableau[pile]!.length - 1 },
            { kind: 'foundation', pile: card.suit },
          ) ?? next
    }
    if (next === before) break
  }
  return next
}
