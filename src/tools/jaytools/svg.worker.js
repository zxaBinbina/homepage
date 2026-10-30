import { compress } from './svg'
self.onmessage = ({ data }) => {
  try {
    self.postMessage({ result: compress(data.input, data.options) })
  } catch (error) {
    self.postMessage({ error: error.message })
  }
}
