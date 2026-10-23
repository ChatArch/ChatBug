# PHP2Shell 隔离复现实验

本文给出 ChatBug 的完整可运行验收路径，并明确它验证什么、没有验证什么。它使用普通网站模型，不为某一个具体业务系统保留专用 CLI。

> **关键边界**：PHP2Shell CVE 是 PHP 运行时内存安全问题。ChatBug 不向生产或 lab 发送 CVE-2026-109618/109619 的 OOM、UAF 或崩溃 payload。本页的完整 lab 验证的是另一条确定性的传统链：`session upload-progress + 应用 include gadget`。两者都可能影响修补优先级，但不能相互替代或混称为同一个生产 RCE 结论。

## 先选择正确的证据层级

| 目标 | 推荐命令 | 可以得出的结论 | 不能得出的结论 |
| --- | --- | --- | --- |
| 只盘点运行时版本 | `web check <URL> --skip-multipart` | HTTP/版本头暴露 | parser、gadget 或命令执行 |
| 确认普通上传入口 | `web check <URL> --skip-gadget-scan` | multipart parser 可达 | LFI、PHP echo、系统命令 |
| 检查固定 session/include marker | `web check <URL>` | 受控 marker 路径线索 | 任意命令、用户数据读取、内存漏洞利用 |
| 回归请求/响应契约 | `lab local-list` | 本机正/负向协议契约 | 真实 PHP 或 shell 执行 |
| 验收固定命令输出 | `lab docker-list` | runtime + lab-only gadget 可执行固定 `ls/cat` | 真实应用 gadget 或生产 CVE 利用 |

## lab-only 链概览

下面的链只在 `docker-list` 创建的临时环境中生成：

```text
multipart POST
  └─ PHP_SESSION_UPLOAD_PROGRESS 写入 lab session 文件
      └─ filename 只携带固定 allowlist proof 的 PHP 代码
          └─ lab-only include($_GET['page']) 包含 session 文件
              └─ 固定 ls/cat 输出经正向响应返回
```

真实应用缺少其中任一条件时，都不能得到相同结论：

- 没有应用 include/LFI sink，只能报告 runtime/parser 暴露；
- `docker exec ... php` 是管理面执行，不是未认证利用；
- 普通 PHP 页面可以读取文件，也不代表远程攻击者能执行命令。

## 本机 contract lab {#本机-contract-lab}

```bash
python -m pip install ChatBug
chatbug php2shell lab local-list
```

该命令在当前进程中启动绑定 `127.0.0.1:0` 的临时 HTTP 服务，并执行正/负向控制：

- multipart 请求被记录为合成 session 状态；
- 正向 `vuln.php` 返回合成 `/tmp`、`chatbug-marker.txt` 和随机 marker；
- 负向 `hello.php` 只返回 `Hello World`；
- context 退出时关闭 socket、线程并清空内存状态。

成功 JSON 的关键形状：

```json
{
  "accepted": true,
  "positive_status": 200,
  "negative_status": 200,
  "positive_output": "/tmp\nchatbug-marker.txt\nCHATBUG_MARKER_EXAMPLE",
  "negative_body": "Hello World\n"
}
```

这是确定性的 contract/regression 用例，不启动真实 PHP、Docker 或系统 shell。适合 CI：

```bash
python -m pytest -q tests/test_php2shell.py
```

## Docker 运行时 lab {#docker-运行时-lab}

在自有 Docker 主机上运行：

```bash
chatbug php2shell lab docker-list \
  --ssh-host <owned-docker-host> \
  --fpm-image <exact-runtime-image-or-digest> \
  --proof list-and-marker
```

`--ssh-host` 是必填项。默认镜像 `php:8.1.34-fpm-alpine` 用于工作流验证；若要与被评估服务比对，必须将 `--fpm-image` 指向同一 PHP-FPM 运行时的精确 digest。

每次运行会在远端 `<chatarch-home>/chatbug/labs/` 下创建唯一目录，并只生成：

- 指定 PHP-FPM 镜像、Nginx 和一次性 Python client；
- `hello.php`，固定输出 `Hello World`；
- `vuln.php`，只存在于 lab，含 `include($_GET['page'])`；
- upload-progress/session 配置；
- internal-only Docker network；
- `/tmp/chatbug-marker.txt` 中的随机合成 marker。

它不会挂载生产数据库、邮件、附件、用户目录、凭据、日志或真实 session 目录，也不会发布主机端口。默认会删除 Compose 项目、网络和远端临时目录；`--keep` 仅用于短时 SSH 人工排查。

## 固定 proof 模式

`--proof` 没有任意 shell 参数，只允许：

| proof | 固定 lab 内动作 | 正向验收 |
| --- | --- | --- |
| `list-tmp` | `ls -la /tmp` | 列表包含合成 `chatbug-marker.txt` |
| `cat-marker` | `cat /tmp/chatbug-marker.txt` | 输出本次随机 marker |
| `list-and-marker` | `ls -la /tmp; echo MARKER; cat /tmp/chatbug-marker.txt` | 同时输出列表、`MARKER` 与随机 marker |

默认的 `list-and-marker` 是最完整、最容易审计的验收模式。

## 正向与负向验收

`list-and-marker` 成功时，`result.positive_output` 的形式如下；ChatBug 会去掉内部定界符，只保留命令输出：

```text
total 24
...
-rw-r--r-- ... chatbug-marker.txt
-rw------- ... sess_lab...
MARKER
CHATBUG_MARKER_...
```

`result.negative_output` 必须为：

```text
Hello World
```

`accepted=true` 的条件因 proof 而异，但始终要求：

- multipart POST、正向 include 和负向普通页面均返回 200；
- 正向输出出现对应的固定证据（`list-tmp` 是 marker 文件名；另两种 proof 是随机 marker）；
- 负向输出不含随机 marker；
- 未指定 `--keep` 时，Compose 项目和远端临时目录完成清理。

这个结果应表述为“**指定 runtime + lab-only include gadget 已在隔离环境中证明**”，而不是“生产 PHP2Shell RCE 已复现”。

## 真实网站检查

### 低影响版本/入口检查

```bash
chatbug php2shell web check https://owned-service.example/ --skip-gadget-scan
```

这会执行版本头读取和普通 multipart parser 检查。它不发送 session include 请求，适合作为生产初始盘点。

### 授权范围内的 marker 探测

```bash
chatbug php2shell web check https://owned-service.example/
```

这个模式额外发送固定 `<?php echo '<marker>'; ?>` filename，并探测固定少量 session/include 形态。它不会执行系统命令或读取真实用户文件，但 LFI 存在时可导致该受控 `echo` 在目标 PHP 进程中执行。只在明确授权、日志/维护窗口合适的情况下使用。

| 字段 | 正确解释 |
| --- | --- |
| `verdict=vulnerable_version_exposed` | 版本头在受影响范围；需要确认真实 HTTP SAPI 并安排修补 |
| `evidence_tier=tier_2_parser_reachable` | 普通 multipart 请求已到达 parser 路径 |
| `evidence_tier=tier_3_gadget_found` | 固定 marker 经候选 session/include 路径返回，需要人工复核应用 gadget |
| `rce_or_file_read_proven=true` | 兼容字段；表示受控 marker 路径，而非任意系统命令、真实文件读取或 CVE 内存利用成功 |

## 复现后的处置

1. 盘点真正服务 HTTP 请求的 PHP SAPI：FPM、mod_php、FrankenPHP、LiteSpeed 等；CLI 版本不是 Web 运行时结论。
2. 升级到官方修复版本，并以运行中容器 digest、包版本或 HTTP SAPI 版本回读验证。
3. 审计并移除不受信任的文件包含/路径拼接 sink。
4. 收紧上传、session 保存路径、临时目录权限和错误暴露。
5. 修补后先重跑低影响 `web check --skip-gadget-scan`，再在同镜像 data-free lab 重跑正/负向验收。
6. 如怀疑已被利用，单独进行访问日志、异常 session、WebShell、子进程和出站连接取证；漏洞验证不能替代取证。
