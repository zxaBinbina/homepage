import { toast } from './useToast'

export async function copyText(text, label = '已复制到剪贴板') {
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
  } catch {
    toast('复制失败，请选中结果后手动复制。', { type: 'warning', timeout: 4000 })
    return false
  }
  toast(label, { type: 'success' })
  return true
}

export async function readClipboard() {
  try {
    return await navigator.clipboard.readText()
  } catch {
    toast('无法读取剪贴板，请在输入框中按 Ctrl / ⌘ V 粘贴。', { type: 'warning', timeout: 4000 })
    return null
  }
}

export function downloadText(text, filename, type = 'text/plain') {
  const url = URL.createObjectURL(new Blob([text], { type }))
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export function readFileAsText(file) {
  if (file.size > 5 * 1024 * 1024) {
    toast('文本文件请控制在 5 MB 以内。', { type: 'warning' })
    return Promise.reject(new Error('文件过大'))
  }
  return new Promise((resolve, reject) => {
    const r = new FileReader()
    r.onload = () => resolve(r.result)
    r.onerror = () => reject(r.error)
    r.readAsText(file)
  })
}
