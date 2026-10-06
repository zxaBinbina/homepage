import { onBeforeUnmount, ref } from 'vue'
import ComputerWorker from './computer.worker?worker&inline'

/** A worker belongs to one turn; undo/restart/navigation terminate stale searches. */
export function useComputer<T, State = number[]>(
  kind: 'gomoku' | 'xiangqi' | 'chess' | 'go',
  accept: (move: T | null) => void,
) {
  const thinking = ref(false),
    error = ref('')
  let worker: Worker | undefined, watchdog: ReturnType<typeof setTimeout> | undefined
  function cancel() {
    if (watchdog) clearTimeout(watchdog)
    worker?.terminate()
    worker = undefined
    thinking.value = false
  }
  function run(board: State, difficulty: number, side: number) {
    cancel()
    error.value = ''
    thinking.value = true
    const fail = () => {
      cancel()
      error.value = '电脑暂时没能完成思考，请重试或悔棋。'
    }
    try {
      const current = new ComputerWorker()
      worker = current
      current.onmessage = (event: MessageEvent<T | null>) => {
        if (worker !== current) return
        cancel()
        accept(event.data)
      }
      current.onerror = (event) => {
        event.preventDefault()
        if (worker === current) fail()
      }
      current.onmessageerror = () => {
        if (worker === current) fail()
      }
      watchdog = setTimeout(fail, 8000)
      // Vue state may contain proxies; send a detached, serializable turn snapshot.
      current.postMessage({ kind, board: JSON.parse(JSON.stringify(board)), difficulty, side })
    } catch {
      fail()
    }
  }
  onBeforeUnmount(cancel)
  return { thinking, error, run, cancel }
}
