export type ImportPlatform = 'windows' | 'macos' | 'linux'

interface PlatformInfo {
  userAgent?: string
  platform?: string
  maxTouchPoints?: number
  userAgentData?: { platform?: string; mobile?: boolean }
}

export function detectImportPlatform(
  device: PlatformInfo | undefined = typeof navigator === 'undefined' ? undefined : navigator,
): ImportPlatform {
  if (!device) return 'windows'
  const hint = device.userAgentData?.platform ?? ''
  const agent = device.userAgent ?? ''
  const platform = device.platform ?? ''
  const identity = `${hint} ${agent} ${platform}`

  // Android reports Linux; iPad desktop mode can report Macintosh/MacIntel.
  // These devices have no matching local Codex tutorial, so use the default.
  if (
    device.userAgentData?.mobile ||
    /android|iphone|ipad|ipod|cros|chrome\s?os/i.test(identity) ||
    (/mac/i.test(identity) && (device.maxTouchPoints ?? 0) > 1)
  )
    return 'windows'

  // Prefer UA Client Hints where available; no permissions or extra requests.
  for (const value of [hint, agent, platform]) {
    if (/windows|\bwin(?:32|64)\b/i.test(value)) return 'windows'
    if (/macintosh|mac\s?os|macintel|macppc/i.test(value)) return 'macos'
    if (/linux/i.test(value)) return 'linux'
  }
  return 'windows'
}
