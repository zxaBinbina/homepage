// Adapted from opendocsg/pdf2md (MIT), converted to ES modules. See third_party/pdf-convert/.
import CalculateGlobalStats from '../models/transformations/text-item/CalculateGlobalStats.js'

import CompactLines from '../models/transformations/line-item/CompactLines.js'
import VerticalToHorizontal from '../models/transformations/line-item/VerticalToHorizontal.js'
import DetectTOC from '../models/transformations/line-item/DetectTOC.js'
import DetectListItems from '../models/transformations/line-item/DetectListItems.js'
import DetectHeaders from '../models/transformations/line-item/DetectHeaders.js'

import GatherBlocks from '../models/transformations/line-item-block/GatherBlocks.js'
import DetectListLevels from '../models/transformations/line-item-block/DetectListLevels.js'

import ParseResult from '../models/ParseResult.js'

export const makeTransformations = (fontMap) => [
  new CalculateGlobalStats(fontMap),
  new CompactLines(),
  new VerticalToHorizontal(),
  new DetectTOC(),
  new DetectListItems(),
  new DetectHeaders(),

  new GatherBlocks(),
  new DetectListLevels(),
]

export const transform = (pages, transformations) => {
  var parseResult = new ParseResult({ pages })
  let lastTransformation
  transformations.forEach((transformation) => {
    if (lastTransformation) {
      parseResult = lastTransformation.completeTransform(parseResult)
    }
    parseResult = transformation.transform(parseResult)
    lastTransformation = transformation
  })
  return lastTransformation ? lastTransformation.completeTransform(parseResult) : parseResult
}
