请作为 Linux 部署助手，协助我从源码部署 RDP Access Auth。

项目仓库：https://github.com/zxaBinbina/rdp-access-auth
部署文档：https://zxabinbina.cc.cd/projects/rdp-access-auth/wiki#deployment
上游说明：https://github.com/zxaBinbina/rdp-access-auth/blob/main/readme.md

## 我的环境（请先让我补齐未填写项）

- 部署主机与连接方式：<本机，或我授权使用的 SSH 主机>
- Linux 发行版：<发行版及版本，或通过只读检查确认>
- 认证域名：<例如 auth.example.com，需托管到 Cloudflare>
- 原 RDP 地址：<例如 desktop.example.com:26869>
- SakuraFrp TCP 隧道 ID：<隧道 ID>
- Cloudflare Tunnel：<新建专用 Tunnel，或说明可复用的 Tunnel>
- 可选 Turnstile：<不启用 / 启用，允许主机名为认证域名>
- 现有安装情况：<首次安装 / 已有部署，注明目录>

不要让我把访问密码、API Token、Tunnel 凭据或 Turnstile Secret 粘贴到聊天里。需要凭据时，使用项目初始化工具的隐藏输入，或让我在服务器终端安全填写；不能交互时停在该步骤，给出我需要在本机执行的命令。

## 部署原则

1. 先阅读当前仓库 README、部署模板、依赖清单与配置工具，确认实际步骤。官网说明与上游不一致时，以当前源码和模板为依据，并说明差异。此项目可直接源码部署，不需要先创建发行版。
2. 只在我指定的主机上操作。先做只读检查：系统与 Python 版本、systemd、cloudflared、端口占用、已有服务与目录、现有 RDP 和 SakuraFrp TCP 隧道是否正常。不要输出凭据文件内容。
3. 汇报实际部署计划与即将变更的服务、路径、DNS 和隧道。变更前确认授权范围；已明确授权的常规步骤连续完成，遇到提权、覆盖现有安装或中断远程连接等超出授权的操作时再确认。
4. 保留现有 RDP 服务。认证服务只监听 127.0.0.1:18089，不把该端口直接开放到公网。使用独立认证子域名；原 RDP 域名保持“仅 DNS”。官网的 /projects/rdp-access-auth 路径不是认证服务地址。
5. 首次安装使用 tools/init_config.py 生成配置，不能直接部署示例配置。已有安装先私密备份配置和 SQLite 状态，不重新初始化、不更换 session_key、不覆盖已有密码哈希或通行密钥。备份数据库时停止写入或使用 SQLite 在线备份。

## 按顺序实施

1. 克隆仓库并记录实际提交；准备 Python 虚拟环境、安装项目依赖，用 tools/build_wordlist.py 构建词库。下载快照不匹配时说明原因，不直接使用 --refresh-sources 绕过检查。
2. 使用认证域名、原 RDP 地址和隧道 ID 生成私密配置；由我安全输入固定访问密码与 SakuraFrp API Token。固定密码应满足项目复杂度要求。
3. 按 deployment/rdp-access-auth.service 安装认证服务：应用在 /opt/rdp-access-auth，配置在 /etc/rdp-access-auth，状态在 /var/lib/rdp-access-auth。保留模板的 DynamicUser、LoadCredential 与权限设置；私密配置保持 0600。检查 cloudflared 实际路径与 SELinux 标签。
4. 创建或配置已授权使用的 Cloudflare Tunnel，配置 DNS 与 HTTPS 入口，确保 hostname、httpHostHeader 和认证服务配置一致。按项目提供的 cloudflared 配置与 systemd 单元运行，不展示 Tunnel 私密 JSON。
5. 在修改 SakuraFrp 隧道前保留现有配置，确认有可用的恢复路径；设置 auth_mode = server、auth_time = 6h，并按授权范围重启隧道或 frpc。若这可能中断当前管理连接，先说明并确认恢复方案。
6. 若启用 Turnstile，通过私密配置提供完整 Site key / Secret key，允许主机名必须包含认证域名；不启用则两项都留空，不填写占位密钥。
7. 使用健康检查验证 loopback 服务，检查两个 systemd 服务、Cloudflare Tunnel 与公网 HTTPS。引导我在实际客户端网络下完成首次登录、绑定通行密钥，再使用系统账户连接原 RDP 地址。

## 验收与交付

- 核对浏览器授权的公网 IPv4 与 RDP 客户端出口一致；使用代理时检查认证域名、RDP 域名及 IPv4 检测服务的路由。
- 分别记录已实测与待人工验证的项目：健康检查、HTTPS、密码认证、通行密钥、未授权 IP 准入、已授权 IP 的 RDP 连接，以及可选 Turnstile。不要把单元测试或模拟响应当成真实部署验收。
- 明确说明：该服务按公网 IP 放行，同一公网出口共享准入；系统登录仍然必需；6 小时到期限制新连接，不保证断开已有会话；重启 frpc 会清除授权缓存。
- 遇到 403、502、IP 出口不一致或通行密钥失败，按日志与上游排错说明定位，不通过关闭 CSRF、来源检查或认证规则来“修好”。分享日志前移除敏感信息。
- 最后给出认证地址、原 RDP 地址、服务名、配置与状态路径、实际源码提交、脱敏的验收结果、备份位置及回滚方法。说明未完成事项与原因；禁止输出私密凭据。
