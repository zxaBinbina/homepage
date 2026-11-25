export type SptlRelease = {
  version: string
  url: string
  publishedAt: string | null
  body: string | null
  assets: { name: string; url: string; size: number }[]
}
