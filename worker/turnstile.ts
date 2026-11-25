import type { Env } from './env'
export const localRequest = (request: Request) =>
  ['127.0.0.1', 'localhost', '[::1]'].includes(new URL(request.url).hostname)
export function turnstileSiteKey(request: Request, env: Env) {
  return env.TURNSTILE_SITE_KEY || (localRequest(request) ? '1x00000000000000000000AA' : null)
}
export async function verifyTurnstile(request: Request, env: Env, token: unknown, action: string) {
  const local = localRequest(request)
  const secret = env.TURNSTILE_SECRET_KEY || (local ? '1x0000000000000000000000000000000AA' : null)
  if (!secret || !turnstileSiteKey(request, env)) throw new Error('联机验证尚未配置，请稍后再试。')
  if (typeof token !== 'string' || !token || token.length > 2048)
    throw new Error('请先完成下方的安全验证。')
  const controller = new AbortController(),
    timeout = setTimeout(() => controller.abort(), 10000)
  try {
    const response = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        secret,
        response: token,
        remoteip: request.headers.get('CF-Connecting-IP') ?? undefined,
        idempotency_key: crypto.randomUUID(),
      }),
      signal: controller.signal,
    })
    const result = (await response.json()) as {
      success?: boolean
      hostname?: string
      action?: string
    }
    const allowedHostnames = [
      new URL(request.url).hostname,
      ...(env.SITE_ORIGIN ? [new URL(env.SITE_ORIGIN).hostname] : []),
    ]
    if (
      !response.ok ||
      !result.success ||
      (!local &&
        (result.action !== action ||
          !result.hostname ||
          !allowedHostnames.includes(result.hostname)))
    )
      throw new Error('安全验证未通过或已过期，请重新验证。')
  } catch (error) {
    if (error instanceof Error && error.message === '安全验证未通过或已过期，请重新验证。')
      throw error
    throw new Error('安全验证服务暂时不可用，请稍后重试。')
  } finally {
    clearTimeout(timeout)
  }
}
