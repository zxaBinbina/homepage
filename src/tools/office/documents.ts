export type OfficeFormat = 'docx' | 'xlsx' | 'pptx'
export interface OfficeDocument {
  name: string
  bytes: Uint8Array
  format: OfficeFormat
}
export const officeMime = {
  docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  pptx: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
}
export function officeFormat(name: string): OfficeFormat | undefined {
  const extension = name.split('.').pop()?.toLowerCase()
  return extension === 'docx' || extension === 'xlsx' || extension === 'pptx'
    ? extension
    : undefined
}
export function downloadName(name: string, format: OfficeFormat) {
  const base = name
    .trim()
    .replace(/\.(docx|xlsx|pptx)$/i, '')
    .replace(/[\\/:*?"<>|\u0000-\u001f]/g, '_')
    .trim()
  return `${base || '未命名文档'}.${format}`
}
export async function blankDocument(format: OfficeFormat): Promise<OfficeDocument> {
  let bytes: Uint8Array
  if (format === 'docx') {
    const D = await import('docx')
    const doc = new D.Document({
      styles: { default: { document: { run: { font: 'Microsoft YaHei', size: 24 } } } },
      sections: [{ children: [new D.Paragraph('')] }],
    })
    bytes = new Uint8Array(await (await D.Packer.toBlob(doc)).arrayBuffer())
  } else if (format === 'xlsx') {
    const X = await import('xlsx')
    const workbook = X.utils.book_new()
    X.utils.book_append_sheet(workbook, X.utils.aoa_to_sheet([['']]), '工作表1')
    const { unzipSync, zipSync, strFromU8, strToU8 } = await import('fflate')
    const files = unzipSync(new Uint8Array(X.write(workbook, { type: 'array', bookType: 'xlsx' })))
    files['xl/styles.xml'] = strToU8(
      strFromU8(files['xl/styles.xml']!)
        .replace('<name val="Calibri"/>', '<name val="Microsoft YaHei"/>')
        .replace('<scheme val="minor"/>', ''),
    )
    bytes = zipSync(files)
  } else {
    const { default: PptxGenJS } = await import('pptxgenjs')
    const deck = new PptxGenJS()
    deck.layout = 'LAYOUT_WIDE'
    deck.author = '访客'
    deck.defineSlideMaster({
      title: 'OFFICE_TITLE',
      objects: [
        {
          placeholder: {
            text: '',
            options: {
              name: 'title',
              type: 'title',
              x: 0.8,
              y: 1.4,
              w: 11.7,
              h: 1.2,
              fontFace: 'Microsoft YaHei',
              fontSize: 36,
            },
          },
        },
        {
          placeholder: {
            text: '',
            options: {
              name: 'subtitle',
              type: 'body',
              x: 1.2,
              y: 3.1,
              w: 10.9,
              h: 1.5,
              fontFace: 'Microsoft YaHei',
              fontSize: 24,
            },
          },
        },
      ],
    })
    deck.addSlide('OFFICE_TITLE')
    bytes = new Uint8Array((await deck.write({ outputType: 'arraybuffer' })) as ArrayBuffer)
  }
  return {
    name: `未命名${format === 'docx' ? '文档' : format === 'xlsx' ? '表格' : '演示文稿'}.${format}`,
    bytes,
    format,
  }
}
