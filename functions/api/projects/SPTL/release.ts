import { sptlReleaseResponse } from '../../../../server/sptlRelease'

export function onRequest(context: { request: Request }) {
  return sptlReleaseResponse(context.request)
}
