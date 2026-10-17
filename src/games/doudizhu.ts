export type DDCard = { rank: number; id: number }
export type Combination = { kind: string; power: number; len: number }
export type DDState = {
  hands: DDCard[][]
  bottom: DDCard[]
  landlord: number
  turn: number
  last: DDCard[]
  lastPlayer: number
  passes: number
  finished: number | null
  bids: number[]
  bidCount: number
  multiplier: number
  plays: number[]
}
export const ranks = ['3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2', '小王', '大王']
export const sortHand = (hand: DDCard[]) => [...hand].sort((a, b) => b.rank - a.rank || a.id - b.id)
export function newDoudizhu(random = Math.random): DDState {
  const deck: DDCard[] = Array.from({ length: 52 }, (_, id) => ({ rank: Math.floor(id / 4), id }))
  deck.push({ rank: 13, id: 52 }, { rank: 14, id: 53 })
  for (let i = deck.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1))
    ;[deck[i], deck[j]] = [deck[j]!, deck[i]!]
  }
  if (new Set(deck.map(card => card.id)).size !== 54 || deck.filter(card => card.rank === 13).length !== 1 || deck.filter(card => card.rank === 14).length !== 1) throw new Error('斗地主牌组构造异常')
  return { hands: [deck.slice(0, 17), deck.slice(17, 34), deck.slice(34, 51)].map(sortHand), bottom: deck.slice(51), landlord: -1, turn: 0, last: [], lastPlayer: -1, passes: 0, finished: null, bids: [-1, -1, -1], bidCount: 0, multiplier: 1, plays: [0, 0, 0] }
}
export function cardText(c: DDCard) { return ranks[c.rank]! }
export function cardLabel(c: DDCard) { return c.rank < 13 ? `${['黑桃', '红桃', '梅花', '方块'][c.id % 4]} ${cardText(c)}` : cardText(c) }
export function bid(game: DDState, score: number): DDState | null {
  if (game.landlord !== -1 || game.finished !== null || !Number.isInteger(score) || score < 0 || score > 3 || (score > 0 && score <= Math.max(...game.bids))) return null
  const bids = [...game.bids]; bids[game.turn] = score
  const next = { ...game, bids, bidCount: game.bidCount + 1, turn: (game.turn + 1) % 3 }
  if (score === 3 || next.bidCount === 3) {
    const high = Math.max(...bids)
    // All passed: leave the deal in bidding phase for the UI to offer a fresh deal.
    if (high === 0) return next
    const landlord = bids.indexOf(high)
    next.landlord = landlord; next.turn = landlord
    next.hands = game.hands.map((h, i) => i === landlord ? sortHand([...h, ...game.bottom]) : h)
  }
  return next
}
export function computerBid(hand: DDCard[], minimum: number) {
  const value = hand.reduce((n, c) => n + (c.rank >= 12 ? c.rank - 10 : c.rank === 11 ? 0.5 : 0), 0)
  const score = value >= 12 ? 3 : value >= 8 ? 2 : value >= 5 ? 1 : 0
  return score > minimum ? score : 0
}
const consecutive = (values: number[]) => values.every((r, i) => i === 0 || r === values[i - 1]! + 1)
export function classify(cards: DDCard[]): Combination | null {
  if (!cards.length || new Set(cards.map(c => c.id)).size !== cards.length) return null
  const counts = new Map<number, number>()
  for (const c of cards) counts.set(c.rank, (counts.get(c.rank) || 0) + 1)
  const keys = [...counts.keys()].sort((a, b) => a - b), amounts = [...counts.values()].sort((a, b) => b - a), n = cards.length
  const result = (kind: string, power: number) => ({ kind, power, len: n })
  if (n === 1) return result('单张', keys[0]!)
  if (n === 2 && counts.has(13) && counts.has(14)) return result('王炸', 99)
  if (keys.length === 1) return n === 2 ? result('对子', keys[0]!) : n === 3 ? result('三张', keys[0]!) : n === 4 ? result('炸弹', keys[0]!) : null
  const triple = keys.find(r => counts.get(r) === 3)
  if (n === 4 && triple !== undefined) return result('三带一', triple)
  if (n === 5 && amounts[0] === 3 && amounts[1] === 2) return result('三带二', triple!)
  if (keys.at(-1)! < 12 && consecutive(keys)) {
    if (n >= 5 && amounts.every(v => v === 1)) return result('顺子', keys.at(-1)!)
    if (keys.length >= 3 && amounts.every(v => v === 2)) return result('连对', keys.at(-1)!)
    if (keys.length >= 2 && amounts.every(v => v === 3)) return result('飞机', keys.at(-1)!)
  }
  // Wings cannot reuse a body rank; single wings may form pairs but cannot include both jokers.
  for (const wing of [1, 2]) {
    const length = n / (3 + wing)
    if (!Number.isInteger(length) || length < 2) continue
    for (let start = 0; start + length <= 12; start++) {
      const body = Array.from({ length }, (_, i) => start + i)
      if (!body.every(r => counts.get(r) === 3)) continue
      const rest = keys.filter(r => !body.includes(r))
      if (wing === 1 && rest.reduce((sum, r) => sum + counts.get(r)!, 0) === length && !(rest.includes(13) && rest.includes(14))) return result('飞机带单', start + length - 1)
      if (wing === 2 && rest.length === length && rest.every(r => counts.get(r) === 2)) return result('飞机带对', start + length - 1)
    }
  }
  const four = keys.find(r => counts.get(r) === 4)
  if (four !== undefined) {
    if (n === 6 && !(counts.has(13) && counts.has(14))) return result('四带二', four)
    if (n === 8 && amounts.length === 3 && amounts[1] === 2 && amounts[2] === 2) return result('四带两对', four)
  }
  return null
}
export function canBeat(cards: DDCard[], last: DDCard[]) {
  const a = classify(cards), b = classify(last)
  if (!a) return false
  if (!b) return true
  if (b.kind === '王炸') return false
  if (a.kind === '王炸') return true
  if (a.kind === '炸弹' && b.kind !== '炸弹') return true
  return a.kind === b.kind && a.len === b.len && a.power > b.power
}
export function playDoudizhu(game: DDState, cards: DDCard[]): DDState | null {
  if (game.landlord < 0 || game.finished !== null) return null
  const hand = game.hands[game.turn]!
  if (cards.some(c => !hand.some(h => h.id === c.id && h.rank === c.rank))) return null
  if (!cards.length) {
    if (!game.last.length || game.lastPlayer === game.turn) return null
    const passes = game.passes + 1
    return { ...game, turn: (game.turn + 1) % 3, passes: passes === 2 ? 0 : passes, last: passes === 2 ? [] : game.last }
  }
  if (!canBeat(cards, game.last)) return null
  const ids = new Set(cards.map(c => c.id)), hands = game.hands.map((h, i) => i === game.turn ? h.filter(c => !ids.has(c.id)) : h)
  const plays = [...game.plays]; plays[game.turn]!++
  const kind = classify(cards)!.kind
  let multiplier = game.multiplier * (kind === '炸弹' || kind === '王炸' ? 2 : 1)
  const finished = hands[game.turn]!.length ? null : game.turn
  if (finished !== null && (finished === game.landlord ? plays.every((n, i) => i === game.landlord || n === 0) : plays[game.landlord] === 1)) multiplier *= 2
  return { ...game, hands, last: sortHand(cards), lastPlayer: game.turn, passes: 0, turn: (game.turn + 1) % 3, finished, multiplier, plays }
}
/** Enumerate rank patterns, rather than all 2^20 physical card subsets. */
export function legalPlays(hand: DDCard[], last: DDCard[]): DDCard[][] {
  const groups = Array.from({ length: 15 }, (_, rank) => hand.filter(c => c.rank === rank))
  const options: DDCard[][] = [], seen = new Set<string>()
  function add(cards: DDCard[]) { const key = cards.map(c => c.id).sort((a,b)=>a-b).join(','); if (!seen.has(key) && canBeat(cards,last)) { seen.add(key); options.push(cards) } }
  for (const g of groups) for (let count = 1; count <= g.length; count++) add(g.slice(0,count))
  if (groups[13]!.length && groups[14]!.length) add([...groups[13]!, ...groups[14]!])
  function wings(body: DDCard[], excluded: number[], count: number, pairs: boolean) {
    const choices = groups.flatMap((g, rank) => excluded.includes(rank) ? [] : pairs ? g.length >= 2 ? [g.slice(0,2)] : [] : g.map(c=>[c]))
    function walk(at: number, picks: DDCard[][]) {
      if (picks.length === count) { add([...body, ...picks.flat()]); return }
      for (let i = at; i <= choices.length - (count - picks.length); i++) walk(i+1,[...picks,choices[i]!])
    }
    walk(0,[])
  }
  for (let rank = 0; rank < 13; rank++) {
    if (groups[rank]!.length >= 3) { wings(groups[rank]!.slice(0,3),[rank],1,false); wings(groups[rank]!.slice(0,3),[rank],1,true) }
    if (groups[rank]!.length === 4) { wings(groups[rank]!,[rank],2,false); wings(groups[rank]!,[rank],2,true) }
  }
  for (const copies of [1,2,3]) for (let start=0;start<12;start++) {
    const body: DDCard[] = [], excluded: number[] = []
    for(let rank=start;rank<12 && groups[rank]!.length>=copies;rank++) {
      body.push(...groups[rank]!.slice(0,copies)); excluded.push(rank)
      const length=rank-start+1
      if(length < (copies===1?5:copies===2?3:2)) continue
      add([...body])
      if(copies===3) { wings(body,excluded,length,false); wings(body,excluded,length,true) }
    }
  }
  return options
}
export function chooseComputer(game: DDState): DDCard[] {
  const options=legalPlays(game.hands[game.turn]!,game.last)
  const finish=options.find(c=>c.length===game.hands[game.turn]!.length)
  if(finish)return finish
  if(game.last.length && game.turn!==game.landlord && game.lastPlayer!==game.landlord) return []
  options.sort((a,b)=>{
    const score=(c:DDCard[])=>{const p=classify(c)!;return c.length*6-p.power-(p.kind==='炸弹'||p.kind==='王炸'?35:0)}
    return score(b)-score(a)
  })
  return options[0] ?? []
}
