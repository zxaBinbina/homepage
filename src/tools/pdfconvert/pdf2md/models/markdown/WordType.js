// Adapted from opendocsg/pdf2md (MIT), converted to ES modules. See third_party/pdf-convert/.
import { Enum } from '../../util/Enum.js'

// An Markdown word element
class WordType extends Enum {

}

export default WordType

WordType.initEnum({
  LINK: {
    toText (string) {
      return `[${string}](${string})`
    },
  },
  FOOTNOTE_LINK: {
    attachWithoutWhitespace: true,
    plainTextFormat: true,
    toText (string) {
      return `^${string}`
    // return `<sup>[${string}](#${string})</sup>`
    },
  },
  FOOTNOTE: {
    toText (string) {
      return `(^${string})`
    },
  },
})
