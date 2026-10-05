import { nextTick, type Ref } from 'vue'

/** Roving tabindex keeps a board to one Tab stop without global key listeners. */
export function useBoardKeyboard(
  element: Ref<HTMLElement | undefined>,
  selected: Ref<number>,
  columns: number,
  count: number,
) {
  return async (event: KeyboardEvent) => {
    if (event.altKey || event.ctrlKey || event.metaKey) return
    let next = selected.value
    const row = Math.floor(next / columns),
      col = next % columns
    if (event.key === 'ArrowLeft') next -= col > 0 ? 1 : 0
    else if (event.key === 'ArrowRight') next += col < columns - 1 ? 1 : 0
    else if (event.key === 'ArrowUp') next = Math.max(col, next - columns)
    else if (event.key === 'ArrowDown') next = Math.min(count - columns + col, next + columns)
    else if (event.key === 'Home') next = row * columns
    else if (event.key === 'End') next = row * columns + columns - 1
    else return
    event.preventDefault()
    selected.value = next
    await nextTick()
    element.value
      ?.querySelectorAll<HTMLButtonElement>('.board-cell')
      [next]?.focus({ preventScroll: true })
  }
}
