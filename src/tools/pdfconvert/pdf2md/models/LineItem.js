// Adapted from opendocsg/pdf2md (MIT), converted to ES modules. See third_party/pdf-convert/.
import PageItem from './PageItem.js'
import Word from './Word.js'

// A line within a page
export default class LineItem extends PageItem {
  constructor (options) {
    super(options)
    this.x = options.x
    this.y = options.y
    this.width = options.width
    this.height = options.height
    this.words = options.words || []
    if (options.text && !options.words) {
      this.words = options.text.split(' ')
        .filter(string => string.trim().length > 0)
        .map(wordAsString => new Word({
          string: wordAsString,
        }))
    }
  }

  text () {
    return this.wordStrings().join(' ')
  }

  wordStrings () {
    return this.words.map(word => word.string)
  }
}
