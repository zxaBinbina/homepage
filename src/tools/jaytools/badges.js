// Adapted from jaywcjlove/tools packages/generate-github-badges (MIT).
import githubShields from './badge-data/github.shields.json'
import githubBadgen from './badge-data/github.badgen.json'
import githubOther from './badge-data/github.other.json'
import npmShields from './badge-data/npm.shields.json'
import npmBadgen from './badge-data/npm.badgen.json'
import dockerShields from './badge-data/docker.shields.json'
import dockerBadgen from './badge-data/docker.badgen.json'
const sources = {
  github: {
    shields: [...githubShields, ...githubOther],
    badgen: [...githubBadgen, ...githubOther],
  },
  npm: { shields: npmShields, badgen: npmBadgen },
  docker: { shields: dockerShields, badgen: dockerBadgen },
}
export function changeStyle(url, type, style) {
  const obj = new URL(url)
  if (type === 'badgen' && obj.hostname.endsWith('badgen.net'))
    obj.hostname = style === 'flat' ? 'flat.badgen.net' : 'badgen.net'
  if (type === 'shields' && obj.hostname.endsWith('shields.io')) {
    if (style) obj.searchParams.set('style', style)
    else obj.searchParams.delete('style')
  }
  return obj.href
}
export function generateBadges(value, category = 'github', type = 'shields', style = '') {
  const parts = value.trim().split('/')
  if (!value.trim()) return []
  if (parts.length > 2 || parts.some((p) => !/^[@\w.-]+$/.test(p)))
    throw new Error('请输入项目名或“账号/项目”，不要包含网址和空格。')
  const [user, repo] = parts.map(encodeURIComponent)
  return sources[category][type].flatMap((item) => {
    let url = item.url
    if (category === 'github') {
      if (!repo && url.includes('{{:repo}}')) return []
      url = url.replaceAll('{{:user}}', user).replaceAll('{{:repo}}', repo || '')
    } else if (category === 'npm')
      url = url.replaceAll('{{:pkg}}', parts.map(encodeURIComponent).join('/'))
    else {
      if (type === 'badgen' && Boolean(repo) !== url.includes('{{:user}}')) return []
      url = url.replaceAll('{{:user}}', repo ? user : '_').replaceAll('{{:library}}', repo || user)
    }
    if (/{{:/.test(url)) return []
    return [{ label: item.label, url: changeStyle(url, type, style) }]
  })
}
export function customBadge({ label, content, color, labelColor, logo, logoColor, style }) {
  const escape = (value) => encodeURIComponent(value.replaceAll('-', '--').replaceAll('_', '__'))
  const url = new URL(
    `https://img.shields.io/badge/${escape(label)}-${escape(content)}-${escape(color.replace(/^#/, ''))}`,
  )
  for (const [key, value] of Object.entries({ labelColor, logo, logoColor, style }))
    if (value) url.searchParams.set(key, value.replace(/^#/, ''))
  return url.href
}
export const badgeMarkdown = (items) =>
  items.map(({ label, url }) => `![${label.replace(/[\[\]\\]/g, '\\$&')}](${url})`).join('\n')
