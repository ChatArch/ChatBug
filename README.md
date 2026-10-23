# ChatBug

ChatBug 是 ChatArch 系列的授权网站漏洞验证包。当前能力聚焦 PHP2Shell 风险评估：先区分 Web 运行时版本暴露、普通 multipart 解析入口和应用文件包含 gadget，再在一次性、无生产数据的 PHP-FPM lab 中完成固定 `ls/cat` 验收。

它不是通用攻击框架：不发送 OOM/UAF/崩溃 payload，不读取生产邮件/附件/会话，不提供反弹 shell，也不接受任意远程命令。

文档入口：<https://arch.gh.wzhecnu.cn/ChatBug/>

## 最快开始

先对自己拥有或已获明确授权的网站做低影响运行时检查：

```bash
python -m pip install ChatBug
chatbug php2shell web check https://owned-site.example/ --skip-gadget-scan
```

然后跑不依赖 Docker 的本机协议/回归用例：

```bash
chatbug php2shell lab local-list
```

若需要真正的 PHP-FPM `ls/cat` 验收，使用自有 SSH Docker 主机创建内部一次性 lab：

```bash
chatbug php2shell lab docker-list \
  --ssh-host <owned-docker-host> \
  --fpm-image <exact-runtime-image-or-digest> \
  --proof list-and-marker
```

默认 `--fpm-image` 是方便复现的 `php:8.1.34-fpm-alpine`。要验证与某服务相同的运行时，传入该服务对应的固定镜像 digest；不要挂载或复制生产卷。

## 能力与边界

| 命令 | 目标 | 请求/执行范围 | 结论边界 |
| --- | --- | --- | --- |
| `web check <URL> --skip-gadget-scan` | 自有网站 | HEAD 与普通 multipart parser 请求 | 版本/入口暴露，不是 RCE |
| `web check <URL>` | 自有网站 | 额外固定 session/include marker 探测 | 受控 PHP `echo` marker 线索；不是系统命令证明 |
| `lab local-list` | 本机进程内 HTTP lab | 合成正/负向响应 | HTTP/payload 合约回归，不运行 PHP 或 shell |
| `lab docker-list` | 自有 Docker 主机 | 内部网络的 PHP-FPM/Nginx 一次性 lab | runtime + lab-only include gadget 下固定 `ls/cat` 成功 |

`docker-list` 复现的是传统、确定性的 PHP `session upload-progress + include` 链：lab 将请求元数据写入 session 文件，lab-only 的 `include($_GET['page'])` 再包含该文件。它说明**同一 PHP-FPM 运行时加上明确存在的应用 gadget**能够走到固定命令输出；它不单独证明 CVE-2026-109618/109619 的内存破坏 RCE，也不说明真实业务应用存在同一 gadget。

## 生产检查安全说明

`web check` 只适用于自己拥有或已获书面授权的目标。三个选项的影响不同：

- `--skip-multipart`：只读取 HTTP/版本头，不发送 multipart 请求；
- `--skip-gadget-scan`：保留普通 multipart parser 检查，但不请求常见 session-file include 形态；
- 无跳过选项：会发送一个固定、无系统命令的 PHP `echo` marker filename，并在固定小范围内检查 marker 是否经候选 session include 路径返回。

最后一种探测不使用 `system()`、不发送 OOM/UAF payload，也不会读取生产 marker/用户数据；但若目标确实存在 LFI gadget，它可能导致该**受控 `echo`** 在目标 PHP 进程中执行并产生普通请求/session 日志。因此应在授权范围和维护窗口内运行，不应把它称为“无副作用扫描”。

输出中的 `rce_or_file_read_proven=true` 是兼容字段名。在当前安全检查中，它只表示独立 marker 通过一个固定的 session/include 候选路径返回；它**不等于**任意系统命令 RCE、真实用户文件泄露或 PHP2Shell 内存漏洞已在生产复现。命令输出级验收只在隔离 `docker-list` lab 中提供。

## 证据层级

ChatBug 不会把弱证据升级成强结论：

1. **版本/配置暴露**：运行时版本头或配置前置条件；
2. **解析器可达**：普通 multipart 请求到达请求处理路径；
3. **受控 marker**：固定 session/include 探测返回独立 marker；
4. **隔离链成功**：无数据 lab 内返回固定 `ls/cat` 输出；
5. **生产内存漏洞利用**：不由 ChatBug 自动执行，需单独风险授权与专门研究。

对邮件、文档等含真实用户数据的生产服务，不应发送内存破坏、OOM、崩溃或重复利用流量。先用同镜像、无数据 lab 完成验证，再独立安排修复与取证。

## 安装与验证

```bash
python -m pip install ChatBug
chatbug --version
chatbug --tree
chatbug --tree-brief
chatbug php2shell lab local-list
```

开发环境：

```bash
python -m pip install -e ".[dev,docs]"
python -m pytest -q
mkdocs build --strict
```

## 文档

- [CLI 树](docs/cli-tree.md)
- [能力地图](docs/capability-map.md)
- [Python 接口树](docs/interface-tree.md)
- [PHP2Shell 隔离复现实验](docs/php2shell-lab.md)

## 开发说明

扩展能力前先阅读 `DEVELOP.md` 和 `AGENTS.md`。任何超过固定 lab proof 的实验能力，都必须首先设计成独立、隔离、可清理且含正/负向验收的 lab；不要扩展为任意远程命令接口。