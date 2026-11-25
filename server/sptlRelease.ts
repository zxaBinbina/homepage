import type { SptlRelease } from '../src/sptl/release'

const repository = 'https://github.com/zxaBinbina/SplayerPlasmaTaskbarLyrics'
const endpoint =
  'https://api.github.com/repos/zxaBinbina/SplayerPlasmaTaskbarLyrics/releases/latest'

function versionFromTag(tag: string) {
  const match = /^v?(\d+\.\d+\.\d+)$/.exec(tag)
  if (!match) throw new Error('Invalid release tag')
  return match[1]!
}

function asset(name: string, url: string, tag: string, size = 0) {
  if (!/^[\w.-]+$/.test(name) || url !== `${repository}/releases/download/${tag}/${name}`)
    throw new Error('Invalid release asset')
  return { name, url, size }
}

async function github(url: string) {
  const response = await fetch(url, {
    headers: { Accept: 'application/vnd.github+json', 'User-Agent': 'SPTL-homepage' },
    signal: AbortSignal.timeout(8000),
    redirect: 'follow',
  })
  if (!response.ok) throw new Error(`GitHub returned ${response.status}`)
  return response
}

async function latest(): Promise<SptlRelease> {
  try {
    const data = (await (await github(endpoint)).json()) as {
      tag_name: string
      html_url: string
      published_at: string | null
      body: string | null
      draft: boolean
      prerelease: boolean
      assets: { name: string; browser_download_url: string; size: number }[]
    }
    const version = versionFromTag(data.tag_name)
    if (
      data.draft ||
      data.prerelease ||
      data.html_url !== `${repository}/releases/tag/${data.tag_name}`
    )
      throw new Error('Invalid public release')
    return {
      version,
      url: data.html_url,
      publishedAt: data.published_at,
      body: data.body?.slice(0, 12000) || null,
      assets: data.assets.map((item) =>
        asset(item.name, item.browser_download_url, data.tag_name, item.size),
      ),
    }
  } catch {
    // Anonymous GitHub API requests can be rate limited; follow the same latest release on the website.
    const response = await github(`${repository}/releases/latest`)
    const prefix = `${repository}/releases/tag/`
    if (!response.url.startsWith(prefix)) throw new Error('Invalid latest release URL')
    const tag = response.url.slice(prefix.length)
    const version = versionFromTag(tag)
    const html = await (await github(`${repository}/releases/expanded_assets/${tag}`)).text()
    const urls = [...html.matchAll(/href="([^"\s]+\/releases\/download\/[^"\s]+)"/g)].map(
      (match) => new URL(match[1]!, repository).href,
    )
    const assets = [...new Set(urls)].map((url) =>
      asset(url.slice(url.lastIndexOf('/') + 1), url, tag),
    )
    if (!assets.length) throw new Error('Missing release assets')
    return { version, url: response.url, publishedAt: null, body: null, assets }
  }
}

export async function sptlReleaseResponse(request: Request): Promise<Response> {
  if (request.method !== 'GET')
    return new Response(null, { status: 405, headers: { Allow: 'GET' } })
  const edgeCache = (
    globalThis as unknown as { caches?: { default?: Pick<Cache, 'match' | 'put'> } }
  ).caches?.default
  const cacheKey = new Request(new URL('/api/projects/SPTL/release', request.url))
  const cached = await edgeCache?.match(cacheKey).catch(() => undefined)
  if (cached) return cached
  try {
    const response = Response.json(await latest(), {
      headers: { 'Cache-Control': 'public, max-age=60, s-maxage=300' },
    })
    await edgeCache?.put(cacheKey, response.clone()).catch(() => undefined)
    return response
  } catch {
    return Response.json(
      { error: '暂时无法读取 GitHub 最新正式版。' },
      {
        status: 503,
        headers: { 'Cache-Control': 'no-store' },
      },
    )
  }
}
