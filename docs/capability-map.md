# 能力地图

ChatBug 当前聚焦一个窄而可验收的安全能力：在明确授权范围内验证 PHP 网站的 PHP2Shell 风险。它把“版本暴露”和“端到端命令/文件读取证明”分开处理。

## 一等能力

<div class="grid cards" markdown>

- **普通网站安全检查**

    `chatbug php2shell web check <URL>` 面向普通自有网站，不为 Mail 单独设计 CLI 入口。检查 PHP 版本暴露、multipart parser 可达性和固定常见 LFI 参数形态。

- **本机可重复实验**

    `chatbug php2shell lab local-list` 在进程内启动临时 HTTP lab，无 Docker、无 root、无系统 shell，用正/负向测试展示 session upload-progress + include gadget 链。

- **完整运行时隔离实验**

    `chatbug php2shell lab docker-list` 在自有 Docker 主机上创建 internal-only、一次性、无生产数据的 PHP-FPM/Nginx lab，并用固定 `ls/cat` allowlist 验收。

- **可导入 Python API**

    CLI 保持薄入口；版本分类、HTTP 检查、payload 构造、lab 生命周期都可从 Python 模块导入和测试。

</div>

## 能力状态

| 能力 | 状态 | 证据边界 |
| --- | --- | --- |
| PHP 版本头解析和修复版本分类 | 已实现并验证 | 只证明版本/配置暴露，不证明可利用 |
| 普通 multipart parser reachability 检查 | 已实现并验证 | 只证明请求能到达上传进度解析路径 |
| 固定常见 LFI marker 探测 | 已实现并验证 | 只有独立 marker 从服务端返回才证明文件读取 |
| 本机 LFI/session 注入 lab | 已实现并验证 | 确定性教学链；不运行真实 shell，不模拟内存破坏 |
| 远端同运行时 Docker lab | 已实现并验证 | 证明“运行时 + 故意加入的应用 LFI gadget”可走到固定 `ls/cat` |
| CVE-2026-109618/109619 内存破坏 RCE 利用 | 未实现 | 不发送 OOM/UAF payload；需要另行授权和专门内存利用研究 |
| 生产服务利用测试 | 不默认提供 | 生产含真实数据，默认只做安全检查；内存破坏利用不在包内自动执行 |
| 任意命令执行框架 / reverse shell | 不提供 | `docker-list` 仅接受三个固定 proof 值 |

## 实战例子如何映射到产品

一次真实 PHP webmail 风险评估可以拆成两层：

1. 把它视为普通 PHP 网站运行 `web check`：确认实际 HTTP SAPI 暴露的 PHP 版本和 multipart 入口，而不是因为服务类型另建一个 mail 专用命令；
2. 若需要 `ls/cat` 级验收，在 `--fpm-image` 指定的相同 PHP-FPM 运行时镜像上运行 `docker-list`：lab 挂载合成 webroot 和随机 marker，不连接真实邮箱、数据库或附件卷。

因此，“这是 Mail 服务”只影响选择相相同 PHP-FPM 运行时镜像，不改变通用 CLI 模型。

## 安全设计约束

- 所有远程检查必须针对自有或已授权目标。
- 生产检查默认无 OOM、无 UAF、无崩溃、无暴力重复、无任意命令。
- Marker 不放进用于读取验证的 URL、query 或 traversal 字符串，避免输入反射误判。
- 正向和负向结果必须同时成立：有 include sink 时返回 marker；普通安全入口只返回 `Hello World`。
- Docker lab 使用内部网络、唯一 Compose project、合成数据和自动清理；`--keep` 只供短时人工复查。
- 报告必须明确写出“runtime only”与“runtime + gadget”的区别。

## 不在当前范围

- 不扫描互联网或未授权主机。
- 不读取真实用户邮件、会话、附件、密钥或生产临时文件。
- 不重启、修补、下架或重新配置生产服务。
- 不隐藏版本 banner 后宣称已修复；修复仍应以运行时版本和实际发布工件为准。
- 不把 scanner 结论、`docker exec` 管理面执行、普通 PHP 页面执行误报为未授权 RCE。
