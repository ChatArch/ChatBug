# 能力地图

ChatBug 当前负责一项窄而可审计的能力：在明确授权范围内评估 PHP 网站的 PHP2Shell 风险。它严格分开运行时暴露、受控 marker 线索、隔离 lab 命令验收和生产内存漏洞利用。

## 一等能力

<div class="grid cards" markdown>

- **普通网站运行时检查**

    `chatbug php2shell web check <URL>` 以普通 Web URL 为入口，而不是按 webmail/CMS 等产品类型拆 CLI。它可读取 PHP 版本、验证 multipart parser，并可选做固定 session/include marker 探测。

- **本机 contract lab**

    `chatbug php2shell lab local-list` 用进程内 HTTP 服务器锁定正/负向协议契约；它不启动 PHP、Docker 或 shell。

- **完整运行时 Docker lab**

    `chatbug php2shell lab docker-list` 在自有 Docker 主机上创建 internal-only、一次性、无生产数据的 PHP-FPM/Nginx 环境。只有这里能运行固定 `ls/cat` proof。

- **可导入 Python API**

    CLI 只做参数和 JSON 输出；版本分类、HTTP 请求、marker 结构、lab 文件和清理生命周期均可独立导入和测试。

</div>

## 能力状态 {#capability-status}

| 能力 | 状态 | 证据边界 |
| --- | --- | --- |
| PHP 版本头解析与修复版本分类 | 已实现并验证 | 证明版本/配置暴露，不证明可利用 |
| 普通 multipart parser 检查 | 已实现并验证 | 证明请求可达上传解析路径，不证明文件包含或命令执行 |
| 固定 session/include marker 探测 | 已实现并验证 | marker 返回说明候选路径需要进一步复核；不证明任意系统命令或用户文件泄露 |
| 本机 LFI/session contract lab | 已实现并验证 | 合成教学/回归链；不运行真实 PHP、shell 或内存破坏 payload |
| 远端 PHP-FPM Docker lab | 已实现并验证 | 只证明指定 runtime + 故意加入 lab-only include gadget 时的固定 `ls/cat` 输出 |
| CVE-2026-109618/109619 内存破坏 RCE | 不提供 | 不发送 OOM/UAF payload；需要单独风险授权和专门研究 |
| 生产服务内存漏洞利用 | 不默认提供 | 含真实数据的生产服务只运行低影响检查；不自动利用 |
| 任意命令框架 / reverse shell | 不提供 | `docker-list` 只接受三个固定 proof 值 |

## 真实服务如何映射到产品

真实 PHP webmail 风险评估仍是两个独立问题：

1. 将服务作为普通 PHP 网站运行 `web check`，确认实际 HTTP SAPI 的版本和入口；业务类型不应导致一个 Mail 专用 CLI；
2. 若需要 `ls/cat` 级验收，在 `--fpm-image` 指定的同运行时、无数据 Docker lab 中运行 `docker-list`；lab 仅挂载合成 webroot 和随机 marker，不连接真实邮箱、数据库、附件或用户目录。

因此“这是 Mail 服务”只影响 lab 镜像选择和风险等级，不改变通用 CLI 模型。

## 安全设计约束

- 所有远程检查都必须针对自有或已授权服务。
- 生产检查不发送 OOM、UAF、崩溃 payload、暴力重复请求或任意系统命令。
- 无 `--skip-gadget-scan` 的 `web check` 可能在存在 LFI 的目标中触发受控 PHP `echo` marker；先确认授权范围和日志/维护窗口。
- Marker 不进入验证 URL、query 或 traversal 字符串，避免输入反射误判。
- Docker lab 使用内部网络、唯一 Compose project、合成数据和自动清理；`--keep` 只供短时人工复查。
- 报告必须明确区分“runtime only”“controlled marker path”和“runtime + lab gadget”。

## 不在当前范围

- 扫描互联网或未授权主机。
- 读取真实用户邮件、会话、附件、密钥或生产临时文件。
- 重启、修补、下架或重新配置生产服务。
- 隐藏版本 banner 后宣称已修复；修复必须由实际 runtime 版本和发布工件验证。
- 将 scanner 结论、`docker exec` 管理面操作、普通 PHP 页面执行或 marker 回显误报为未授权 RCE。
