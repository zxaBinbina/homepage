# 斗地主界面说明

`/games/doudizhu` 的牌桌、选牌与回合显示维护在 `src/games/DoudizhuGame.vue`，规则及电脑策略仍由 `src/games/doudizhu.ts` 提供；样式集中在 `src/style.css` 的 `.dd-*` 范围，视觉参数见 [DESIGN.md](../DESIGN.md#欢乐斗地主)。

## GitHub 参考

2026-11-21 通过 GitHub 检索并查看了以下项目的界面源码；前两个项目另核对了 README 中的实际牌局截图。

| 项目                                                                                | 查看内容                                                                      | 采用的布局与行为                                                       |
| ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| [laivv/doudizhu](https://github.com/laivv/doudizhu)                                 | `static/index.html`、`static/css/style.css`、`static/images/game.jpg`         | 三方座位、顶部底牌、底部重叠手牌、选中牌抬起、座位各自显示出牌与不出   |
| [VYuLinLin/doudizhu-stand-alone](https://github.com/VYuLinLin/doudizhu-stand-alone) | `assets/scripts/gameScene/gameingUI.js`、`gameScene.js`、`image/landlord.png` | 左右电脑身份和余牌、手牌上方操作、提示后确认、移除已出牌后重新排布手牌 |
| [WangQingye/Doudizhu-client](https://github.com/WangQingye/Doudizhu-client)         | `doudizhu/src/client/Douzizhu.ts`                                             | 当前回合标记、按座位展示牌面、两家不出后清桌、合法选牌才启用出牌       |

本站用 Vue、原生 CSS、Lucide 和既有扑克牌组件重新实现，配色、字体、胶囊按钮与明暗行为遵循本站设置。参考仓库的源码、图片与音效未迁入本项目；laivv 的 README 特别说明图片不属于其 MIT 许可范围。本站仍采用原有三人叫分和本地电脑，不增加联网房间、聊天、计时强制出牌或额外存储。

## 验证

构建后启动预览，再执行专项浏览器回归：

```sh
npm run build
npm run preview -- --port 4173
HOMEPAGE_TEST_URL=http://127.0.0.1:4173 python3 scripts/check-games-doudizhu.py
```

专项检查覆盖叫分和揭底、完整牌局、花色、全量手牌可见、四套主题、320px 窄屏、鼠标与触摸划选、取消、键盘、重新发牌和全屏状态保留；截图位于 `artifacts/doudizhu/`。共享游戏和全屏组件修改后还应按 [AGENTS.md](../AGENTS.md#验证方式) 执行公共回归。
