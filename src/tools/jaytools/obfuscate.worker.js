import './obfuscator-environment'
import obfuscator from 'javascript-obfuscator/dist/index.browser.js'
self.onmessage = ({ data }) => {
  try {
    const result = obfuscator.obfuscate(data.input, data.options)
    self.postMessage({ result: result.getObfuscatedCode(), map: result.getSourceMap() })
  } catch (error) {
    self.postMessage({ error: error.message })
  }
}
