// Adapted from opendocsg/pdf2md (MIT), converted to ES modules. See third_party/pdf-convert/.
export default class Word {
  constructor (options) {
    this.string = options.string
    this.type = options.type // WordType
    this.format = options.format // WordFormat
  }
}
