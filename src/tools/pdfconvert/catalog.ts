import type { ConvertId } from './types'

export const pdfConvertCatalog = {
  'pdf-to-word': {
    name: 'PDF 转 Word',
    label: 'PDF TO WORD',
    description: '将 PDF 文字与表格整理为可编辑的 Word，或以整页图片保留版面。',
    category: 'PDF 转换',
    icon: 'docText',
    keywords: 'PDF Word DOCX 办公 文档 可编辑 扫描件',
    path: '/tools/pdf-to-word',
  },
  'pdf-to-excel': {
    name: 'PDF 转 Excel',
    label: 'PDF TO EXCEL',
    description: '识别 PDF 中对齐的表格，导出 Excel，也可逐行导出全部文字。',
    category: 'PDF 转换',
    icon: 'table',
    keywords: 'PDF Excel XLSX 表格 工作簿 办公',
    path: '/tools/pdf-to-excel',
  },
  'pdf-to-powerpoint': {
    name: 'PDF 转 PowerPoint',
    label: 'PDF TO POWERPOINT',
    description: '将每页 PDF 转成幻灯片，选择整页图片或可编辑文字。',
    category: 'PDF 转换',
    icon: 'image',
    keywords: 'PDF PowerPoint PPT PPTX 幻灯片 演示 办公',
    path: '/tools/pdf-to-powerpoint',
  },
  'pdf-to-markdown': {
    name: 'PDF 转 Markdown',
    label: 'PDF TO MARKDOWN',
    description: '提取 PDF 文字，整理标题、列表和表格，预览并下载 Markdown。',
    category: 'PDF 转换',
    icon: 'markdown',
    keywords: 'PDF Markdown MD 文字 文本 标题 列表',
    path: '/tools/pdf-to-markdown',
  },
} as const

export function isPdfConvertId(id: string): id is ConvertId {
  return Object.hasOwn(pdfConvertCatalog, id)
}
