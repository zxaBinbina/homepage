// Adapted from opendocsg/pdf2md (MIT), converted to ES modules. See third_party/pdf-convert/.
export default class ParsedElements {
  constructor (options) {
    this.footnoteLinks = options.footnoteLinks || []
    this.footnotes = options.footnotes || []
    this.containLinks = options.containLinks
    this.formattedWords = options.formattedWords
  }

  add (parsedElements) {
    this.footnoteLinks = this.footnoteLinks.concat(parsedElements.footnoteLinks)
    this.footnotes = this.footnotes.concat(parsedElements.footnotes)
    this.containLinks = this.containLinks || parsedElements.containLinks
    this.formattedWords += parsedElements.formattedWords
  }
}
