// Adapted from opendocsg/pdf2md (MIT), converted to ES modules. See third_party/pdf-convert/.
// A page which holds PageItems displayable via PdfPageView
export default class Page {
  constructor (options) {
    this.index = options.index
    this.items = options.items || [] // PageItem
  }
}
