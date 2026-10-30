/** Shared by the Vue pages, router and generated error documents. */
export const errorCatalog = {
  error400: {
    code: 400,
    label: 'BAD REQUEST',
    title: '这个请求有点不对劲',
    description: '暂时无法理解这次请求。请检查网址是否完整，或回到首页重新出发。',
    retry: false,
  },
  error401: {
    code: 401,
    label: 'UNAUTHORIZED',
    title: '先确认一下你的身份',
    description: '这个页面需要身份验证。请从原来的入口完成登录或认证后，再来访问。',
    retry: false,
  },
  error403: {
    code: 403,
    label: 'FORBIDDEN',
    title: '这片区域暂未开放',
    description: '你暂时没有访问这里的权限。如果觉得走错了门，可以联系我确认一下。',
    retry: false,
  },
  error404: {
    code: 404,
    label: 'NOT FOUND',
    title: '这块世界，还没有生成',
    description: '没有找到你想去的页面。也许地址写错了，也许它已经搬家，回到熟悉的地方继续逛逛吧。',
    retry: false,
  },
  error408: {
    code: 408,
    label: 'REQUEST TIMEOUT',
    title: '这次等待有点久',
    description: '请求没能及时完成。检查一下网络，稍后再试一次吧。',
    retry: true,
  },
  error429: {
    code: 429,
    label: 'TOO MANY REQUESTS',
    title: '慢一点，风景还在',
    description: '这段时间的请求有点多。请稍作休息，过一会儿再来访问。',
    retry: false,
  },
  error500: {
    code: 500,
    label: 'INTERNAL SERVER ERROR',
    title: '方块之间，出了点小差错',
    description: '服务器暂时没能完成这次请求。稍后再试试，如果问题持续，也欢迎告诉我。',
    retry: true,
  },
  error502: {
    code: 502,
    label: 'BAD GATEWAY',
    title: '通往这里的桥暂时断了',
    description: '连接上游服务时遇到了一点问题。请稍后重试，或先去其他地方看看。',
    retry: true,
  },
  error503: {
    code: 503,
    label: 'SERVICE UNAVAILABLE',
    title: '世界正在稍作休息',
    description: '服务暂时不可用，可能正在维护或忙碌中。等一会儿，再回来看看吧。',
    retry: true,
  },
  error504: {
    code: 504,
    label: 'GATEWAY TIMEOUT',
    title: '远方的回应，还没到达',
    description: '等待上游服务的时间太久了。请稍后再试，感谢你的耐心。',
    retry: true,
  },
} as const

export type ErrorPageName = keyof typeof errorCatalog

export function isErrorPage(page: unknown): page is ErrorPageName {
  return typeof page === 'string' && Object.hasOwn(errorCatalog, page)
}

export const errorPaths = Object.fromEntries(
  Object.entries(errorCatalog).map(([name, error]) => [name, `/${error.code}`]),
) as Record<ErrorPageName, string>
