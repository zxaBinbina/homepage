import { onBeforeUnmount } from 'vue'
// A new worker per run makes cancellation real, including CPU-bound parsing.
export function useToolWorker(factory, timeout = 15000) {
  let current
  function cancel() {
    current?.()
    current = undefined
  }
  function run(input, options) {
    cancel()
    return new Promise((resolve, reject) => {
      const worker = factory()
      let timer
      const end = () => {
        clearTimeout(timer)
        worker.terminate()
        current = undefined
      }
      current = () => {
        end()
        reject(new Error('任务已取消。'))
      }
      timer = setTimeout(() => {
        end()
        reject(new Error('处理超时，请缩短输入或降低处理强度。'))
      }, timeout)
      worker.onmessage = ({ data }) => {
        end()
        data.error ? reject(new Error(data.error)) : resolve(data)
      }
      worker.onerror = () => {
        end()
        reject(new Error('处理程序加载失败，请重新加载后重试。'))
      }
      try {
        worker.postMessage(JSON.parse(JSON.stringify({ input, options })))
      } catch (error) {
        end()
        reject(error)
      }
    })
  }
  onBeforeUnmount(cancel)
  return { run, cancel }
}
