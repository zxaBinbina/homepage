import { lyricsResponse } from '../../../server/lyrics'

export function onRequestGet(context: { request: Request }) {
  return lyricsResponse(new URL(context.request.url))
}
