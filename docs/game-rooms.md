# 联机房间与 Workers 部署

中国象棋、五子棋、国际象棋、围棋、斗地主和双人军旗提供「单机对战 / 朋友联机」。游戏地址保持不变，界面复用本站主题、棋盘、牌面、胶囊控件和网页全屏。

## 房间规则

- 填写昵称并完成 Turnstile 验证后创建或加入房间。创建者得到唯一的 6 位数字房间号，朋友输入号码加入；免登录，不公开房间列表，不提供观战。
- 双人游戏需要两位真人；斗地主支持 1～3 位真人，开局时空位由电脑补足。所有真人准备后由房主开局，修改设置会清除准备状态。
- 房主设置每步「不限时 / 30 / 60 / 120 秒」。超时后电脑代操作一步，再交还真人；电脑只使用该玩家可见的信息。
- 悔棋设置「启用 / 询问 / 禁用」：直接撤回、需对手同意或不允许。撤回自己最近一手及对手应手；斗地主与暗棋军旗始终禁用。
- 军旗可选明棋、暗棋，双方布阵确认后开始。暗棋身份由服务端隐藏与裁决。围棋双方停一手后共同标记死子、确认结算，更改标记会取消双方确认；有争议可继续对局。
- 中途重开需其他真人全部同意，通过后回到准备阶段。申请 60 秒未答复会过期，新操作会结束旧申请。对局中锁定席位，新玩家只能在本局结束后加入；原玩家可以重连。
- 掉线或刷新时暂停，保留席位 3 分钟；回来后恢复原局面和剩余计时。超时后双人游戏判掉线方负，斗地主由电脑接管。开局前或结束后的过期离线席位释放。
- 主动退出时立即离开，双人对局判离开方负，斗地主由电脑接管。房主身份转交给其他真人。所有真人主动退出立即解散；全部掉线则等待 3 分钟，无人重连再解散。电脑不阻止清理。
- 自然结束后保留房间号与聊天，重新准备可再开一局。聊天只保留最近 30 条，每条最多 200 个可见字符，按纯文字展示；解散时清空对局、聊天、凭据和号码索引。

昵称为 1～16 个可见字符，同房不能重名。重连凭据只放在当前标签页的 `sessionStorage`，不写入网址；存储失败会提示。单机模式保持原来的页面内状态和本地电脑对战，联机对局不写入单机棋类经验库。

## 文件与免费服务

`worker/index.ts` 分发 API；`worker/rooms.ts` 管理 SQLite Durable Objects 房间与号码索引；`worker/turnstile.ts` 验证 Siteverify。界面、规则适配和玩家可见局面在 `src/games/multiplayer/`；歌词与原有经验接口分别在 `server/lyrics.ts`、`server/gameExperience.ts`。

服务端检查轮次、合法操作和局面版本。斗地主只发送自己的手牌、公开底牌与剩余张数；暗棋不发送对方完整身份。空闲 WebSocket 使用休眠，计时与清理使用服务端 Alarm，没有持续轮询。

仅需要 Workers Free、SQLite Durable Objects、原有 KV 和免费 Turnstile。无需 R2、D1、银行卡或付费服务；免费额度超限会限制操作，不会自动升级套餐。静态资源直接由 Assets 托管，`/api/*` 调用 Worker；Office 的预压缩 `x2t.wasm.br` 也经过 Worker，以原始 Brotli 编码流式传回，避免 Assets 再次压缩。该文件仍存于 Assets，无需额外存储服务。

## 本地开发与检查

```bash
npm ci
cp .dev.vars.example .dev.vars
npm run build
npm run dev:worker
```

Workers 预览为 `http://127.0.0.1:8788`，启动命令通过 `--infer-origin-from-routes=false` 保留本地来源，避免把请求地址替换成正式域名。需要 Vite 热更新时另运行 `npm run dev`，房间 HTTP / WebSocket 代理到 8788，与私人网页浏览器后端的 8787 分开。

本地 `.dev.vars` 使用 Cloudflare 官方测试密钥对，覆盖正式 Site Key，避免正式小组件的域名限制阻止本机开发；该文件被 Git 忽略，且不会随 Workers 部署发布。没有配置密钥时，只有本机地址 `localhost` / `127.0.0.1` 可以自动使用官方测试密钥。正式域名未配置真实密钥时拒绝建房和入房，不使用测试密钥放行。已有席位的刷新与重连通过原凭据处理，无需再次 Turnstile。

```bash
npm run check:rooms
node scripts/check-game-rooms.mjs --serve
# 另一终端；8796 fixture 模拟 Siteverify，不部署。
python3 scripts/check-game-rooms-browser.py
```

服务回归使用真实 Workers / SQLite / WebSocket 运行时，覆盖规则、并发房间、席位、超时、隐藏信息、同意流程、重连和清理。浏览器回归覆盖独立玩家会话、四套主题、320～1440px 和全屏；fixture 的 Turnstile 脚本与 Siteverify 为模拟，不能作为正式域名验证成功的证据。原有游戏、歌词、导航、分享、SEO 和 Office 回归仍按改动范围执行。

运行 `python3 scripts/check-turnstile-browser.py` 可在 8788 预览中验证真实 Cloudflare 测试组件与 Siteverify，需要网络；测试密钥不代表正式域名已经配置。`python3 scripts/check-workers-browser.py` 汇总迁移回归，默认 Workers 地址为 8788、Vite 地址为 5283，可用 `HOMEPAGE_WORKER_TEST_URL` / `HOMEPAGE_DEV_TEST_URL` 指定已有预览；可传入脚本文件名只运行指定检查。

## 正式配置与迁移

1. 创建免费 Turnstile 小组件，允许 `zxabinbina.cc.cd`；如需从默认 Workers 地址联机，也加入 `homepage.zxabinbina.workers.dev`。
2. 将公开 Site Key 放入 `wrangler.toml` 的 `[vars]`，变量名 `TURNSTILE_SITE_KEY`。Secret Key 通过 Cloudflare Worker Secrets 或本地隐藏输入配置，不写入仓库：

   ```bash
   npx wrangler secret put TURNSTILE_SECRET_KEY
   ```

3. 配置已保留 `GAME_EXPERIENCE` KV，并登记两个 SQLite Durable Object 类；部署时自动创建房间 namespace。不要改为付费限定的旧式 KV Durable Objects。
4. 本站现有 DNS 记录受 Pages 管理，Cloudflare 不允许直接覆盖为 Workers 自定义域名，因此使用 `zxabinbina.cc.cd/*` Workers 路由接管所有站内请求。保留现有代理 DNS 和原 Pages 项目作为回退；代码、静态资源和 API 均由 `homepage` Worker 提供。部署时由 `wrangler.toml` 维护该路由：

   ```bash
   npm run deploy
   ```

5. 在 Workers Builds 连接 Git 仓库默认分支，构建命令 `npm run build`、部署命令 `npx wrangler deploy`。歌单同步提交会触发该集成。

主站域名不变。Office 引擎在同一 Workers 项目的独立来源 `homepage.zxabinbina.workers.dev` 中运行；保留 `workers_dev = true`，或指定另一个托管本构建的独立来源。`_headers`、`_redirects` 与 `404.html` 随资源发布；已注册页面保持无末尾斜线，Office 目录的 `index.html` 使用自然末尾斜线。

首次上线需检查真实 Turnstile、正式建房 / 入房、两台设备对局和重连。正式密钥尚未提供时，代码与本地测试完成不表示生产域名已经切换。

可用 `HOMEPAGE_TEST_URL=https://zxabinbina.cc.cd python3 scripts/check-live-game-rooms.py` 验证真实 Turnstile、双玩家同步、悔棋、聊天与重连；该检查不会模拟安全验证。若受自动化浏览器检测影响，可在有桌面会话时使用 `HOMEPAGE_NATIVE_BROWSER=1` 启动独立的常规 Chrome，再由测试连接本地调试端口，测试后关闭并清理临时浏览器资料。
