export type ConvertId = 'pdf-to-word' | 'pdf-to-excel' | 'pdf-to-powerpoint' | 'pdf-to-markdown'
export type Target = 'word' | 'excel' | 'powerpoint' | 'markdown'
export interface TextBox {
  x: number
  y: number
  width: number
  height: number
  text: string
  font: string
}
export interface PdfPageData {
  index: number
  width: number
  height: number
  items: TextBox[]
  fonts: Record<string, { name: string }>
  image?: string
}
export interface ConvertOptions {
  target: Target
  mode: 'text' | 'image'
  pageBreaks: boolean
  excelScope: 'tables' | 'all'
  excelSheets: 'pages' | 'single'
  numbers: boolean
}
export interface ConvertStats {
  pages: number
  textPages: number
  tables: number
}
export interface ConvertOutput {
  bytes: Uint8Array
  preview: string
  extension: string
  mime: string
  stats: ConvertStats
}
