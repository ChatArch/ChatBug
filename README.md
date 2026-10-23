# ChatBug

ChatBug 是 ChatArch 系列的授权网站漏洞验证包。首个能力聚焦 **PHP2Shell**：先对自己拥有的普通网站做无破坏性版本/入口检查，再用一次性、无真实数据的隔离实验环境复现“运行时 + LFI include gadget → session upload-progress 注入 → `ls/cat` 输出”的完整测试链。

它不是通用攻击框架：不发送 OOM/UAF 崩溃 payload，不对生产执行命令，不提供反弹 shell，也不接受任意远程命令参数。

文档入口：<https://arch.gh.wzhecnu.cn/ChatBug/>

## 适用场景

- 判断自有 PHP 网站是否暴露在受影响版本范围。
- 用普通 multipart 请求确认上传解析入口是否可达。
- 用固定、小规模的常见 include 参数形态做**标记文件读取**探测。
- 在本地进程实验或远端一次性 Docker 实验中，跑通可重复的 `ls -la /tmp` / `cat /tmp/chatbug-marker.txt` 验收。
- 向团队输出可审计 JSON，区分“版本暴露”“解析器可达”“隔离链复现成功”和“生产利用未证明”。

## 安全边界

| 命令 | 作用对象 | 是否执行命令 | 是否接触生产数据 |
| --- | --- | --- | --- |
| `chatbug php2shell web check <URL>` | 自有普通网站 URL | 否 | 否；只发 HEAD、普通 multipart 和固定 gadget 探测 |
| `chatbug php2shell lab local-list` | 本机临时 HTTP lab | 否；不启动系统 shell | 否；进程内合成数据 |
| `chatbug php2shell lab docker-list` | 远端一次性内部 Docker lab | 仅 lab 固定 allowlist 命令 | 否；无生产卷、无发布端口、合成 marker |

`docker-list` 复现的是传统、确定性的 PHP `include` 文件包含链：`PHP_SESSION_UPLOAD_PROGRESS` 写入 session 文件，lab-only 的 `include($_GET['page'])` 再包含该文件。它证明“受影响 PHP-FPM 运行时 + 应用存在 LFI gadget”时可以走到 `ls/cat`，**不单独证明 CVE-2026-109618/109619 的内存破坏 RCE**。

## 安装

```bash
python -m pip install ChatBug
chatbug --version
chatbug --tree
```

开发环境：

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

## 快速复现：本机可运行 test case

无需 Docker、无需 root、无需网络：

```bash
chatbug php2shell lab local-list
```

成功时输出 JSON，关键字段包括：

- `accepted: true`
- `positive_status: 200`
- `negative_status: 200`
- `positive_output` 包含 `/tmp`、`chatbug-marker.txt` 和随机 marker
- `negative_body` 只有 `Hello World`，证明普通安全入口不会把 session 文件当 PHP 执行

这个命令也由测试覆盖：

```bash
python -m pytest -q tests/test_php2shell.py
```

## 完整隔离复现：PHP-FPM + Nginx

需要一个可通过 SSH 使用 Docker 的自有主机。该命令会：

1. 拉取固定 digest 的 PHP/PHP-FPM 镜像作为运行时；
2. 生成只含 `Hello World` 和 lab-only `include` sink 的临时 webroot；
3. 创建 internal Docker network，不发布主机端口；
4. 在 lab 容器的 `/tmp/chatbug-marker.txt` 写入随机合成 marker；
5. 从同一内部网络的一次性 client 容器发送 session upload-progress 请求；
6. 正向请求通过 lab-only LFI sink 返回 `ls/cat` 输出；
7. 负向请求访问普通 `hello.php`，只返回 `Hello World`；
8. 删除容器、网络和远端临时目录。

```bash
chatbug php2shell lab docker-list \
  --ssh-host <your-ssh-host> \
  [--fpm-image <digest-pinned-php-fpm-image>] \
  --proof list-and-marker
```

`--proof` 只允许三个固定模式：

- `list-tmp`：执行 lab 内 `ls -la /tmp`；
- `cat-marker`：读取 lab 内合成 marker 文件；
- `list-and-marker`：同时列目录并读取 marker（默认）。

真实验收输出会在 `positive_output` 中包含 lab 的 `/tmp` 列表、`sess_<id>` 文件、`MARKER` 和随机 marker；负向输出必须保持 `Hello World`。

## 检查自有普通网站

```bash
chatbug php2shell web check https://example-owned-site.example/
```

输出字段解释：

- `verdict=vulnerable_version_exposed`：版本头显示在受影响范围，只代表暴露，不代表 RCE；
- `evidence_tier=tier_2_parser_reachable`：普通 multipart 解析入口可达；
- `evidence_tier=tier_3_gadget_found`：固定探测中发现服务端返回了独立 marker；
- `rce_or_file_read_proven=true`：只有在标记不能由请求反射解释、确实从服务端 session 文件包含返回时才成立。

可跳过较重的探测：

```bash
chatbug php2shell web check https://example-owned-site.example/ --skip-gadget-scan
```

## 证据层级

ChatBug 不把弱证据升级成强结论：

1. 版本/配置暴露；
2. 解析器或前置条件可达；
3. 一次性隔离环境中完成 marker/命令输出验收；
4. 经单独风险授权后的生产验证；
5. 第三方真实入侵指标。

对邮件、文档等含真实用户数据的生产服务，不应发送内存破坏、OOM、崩溃或重复利用流量；先用同镜像、无数据 lab 完成验收。

## 文档

- [CLI 树](docs/cli-tree.md)
- [能力地图](docs/capability-map.md)
- [Python 接口树](docs/interface-tree.md)
- [PHP2Shell 复现实验](docs/php2shell-lab.md)

## 开发说明

扩展能力前先阅读 `DEVELOP.md` 和 `AGENTS.md`。新增生产检查必须保持非破坏性；任何需要固定命令以外的实验能力，应先增加独立、隔离、可清理的 lab，而不是扩展远程任意命令接口。
