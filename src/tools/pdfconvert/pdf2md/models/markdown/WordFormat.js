// Adapted from opendocsg/pdf2md (MIT), converted to ES modules. See third_party/pdf-convert/.
import { Enum } from '../../util/Enum.js'

// The format of a word element
class WordFormat extends Enum {

}

export default WordFormat

WordFormat.initEnum({
  BOLD: {
    startSymbol: '**',
    endSymbol: '**',
  },
  OBLIQUE: {
    startSymbol: '_',
    endSymbol: '_',
  },
  BOLD_OBLIQUE: {
    startSymbol: '**_',
    endSymbol: '_**',
  },
})
