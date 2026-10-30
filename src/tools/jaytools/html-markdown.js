// Adapted from jaywcjlove/tools packages/html-to-markdown/src/utils.ts (MIT).
import { unified } from 'unified'
import rehypeParse from 'rehype-parse'
import rehypeRemark from 'rehype-remark'
import remarkStringify from 'remark-stringify'
import remarkGfm from 'remark-gfm'
// Parse a syntax tree without mounting HTML or fetching its resources.
export const transform = (input) =>
  String(
    unified()
      .use(rehypeParse, { fragment: true })
      .use(rehypeRemark)
      .use(remarkGfm)
      .use(remarkStringify)
      .processSync(input),
  )
