# 军旗界面说明

军旗路径为 `/games/junqi`。页面与交互在 `src/games/JunqiGame.vue`，规则、随机布阵与交换校验在 `src/games/junqi.ts`，样式位于 `src/style.css` 的 `.junqi-*` 范围；具体参数见 [DESIGN.md](../DESIGN.md#军旗)。

## GitHub 参考

2026-11-21 检索并查看了以下三个军棋项目的说明与界面实现：

| 项目                                                                    | 查看内容                                                                                      | 采用的布局与行为                                                                      |
| ----------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| [samuelyuan/online-junqi](https://github.com/samuelyuan/online-junqi)   | README、`images/game.png`、`public/js/lib/BoardRenderer.js`、`GameUIManager.js`               | 棋盘上下的玩家信息、矩形兵站与椭圆行营、交换布阵、可移动 / 可攻击标记、最近一步起终点 |
| [chengxg/junqi-client-vue](https://github.com/chengxg/junqi-client-vue) | README、`src/pages/localplay/Chessboard.vue`、`OptionLayer.vue`、`src/pages/common/Chess.vue` | 中文长条棋子、选中抬起、棋盘与操作分层、当前阵营提示                                  |
| [821869798/junqiRpg](https://github.com/821869798/junqiRpg)             | README、`junqiRpg/Assets/Script/BoardManage.cs`                                               | 布阵与对局分阶段，交换军旗 / 地雷 / 炸弹前校验落位，准备后开局                        |

本站以 Vue、原生 CSS、Lucide 与既有主题重新实现，未迁入参考仓库的源码、图片或音效。chengxg 的「工兵扛军旗」包含组合棋子等变体；本站采用双人明棋夺旗玩法和本地电脑，没有接入这些变体或联网房间。

## 本次核对的行为

棋盘图形与规则共用铁路节点和跨山通路，三处桥梁连接两方。工兵、炸弹分别登记，避免工兵被标为炸弹；同级和炸弹碰撞后双方移除，攻击失败只移除攻击者。行营内棋子免受攻击，但可出去攻击；棋子进入大本营后不能移动。对方无合法行棋时结算，避免电脑停在无棋可走的状态。

布阵不保存到浏览器。开始前可交换两枚己方棋子，军旗限大本营、地雷限后两排、炸弹不能在最前排。悔棋恢复玩家行棋前的局面与记录，同时取消电脑计时与装饰动画；重开或离开页面清理未完成任务。电脑采用本地启发式选择，适合休闲练习。

## 验证

```sh
node scripts/check-games-junqi.mjs
npm run build
npm run preview -- --port 4173
HOMEPAGE_TEST_URL=http://127.0.0.1:4173 python3 scripts/check-games-junqi.py
```

规则检查覆盖每方棋子清单、布阵限制、铁路与三处桥梁、行营和大本营、工兵排雷、同归于尽与终局。浏览器检查覆盖布阵、合法位置、实际行棋与吃子、整轮悔棋、取消清理、键盘、四套主题、320px 窄屏、横竖屏全屏及减少动态效果。截图位于 `artifacts/junqi/`；共享游戏组件仍按 [AGENTS.md](../AGENTS.md#验证方式) 执行公共检查。
