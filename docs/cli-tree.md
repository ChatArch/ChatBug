# CLI 树

以下命令树来自 ChatBug 0.1.0 的真实 Click 注册面。安装后请优先运行 `chatbug --tree` 回读当前版本；文档只描述已实现命令。

## 真实命令树

```text
chatbug
├── --help  # Show this message and exit.
├── --version  # Show the version and exit.
├── --tree  # Print the registered CLI tree and exit.
├── --tree-brief  # Print the registered CLI tree without parameter signatures and exit.
└── php2shell  # PHP2Shell web checks and data-free lab proof.
    ├── lab  # Disposable, data-free lab workflows.
    │   ├── docker-list [--ssh-host SSH-HOST] [--fpm-image FPM-IMAGE] [--proof PROOF] [--keep]  # Prove list/cat inside a data-free PHP-FPM lab with an intentional include sink.
    │   └── local-list  # Run a complete positive/negative example in an in-process local lab.
    └── web  # Checks for an ordinary owned website URL.
        └── check <URL> [--skip-multipart] [--skip-gadget-scan]  # Check version exposure, parser reachability, and common include gadgets.
```

## `chatbug php2shell web check <URL>` {#chatbug-php2shell-web-check-url}

仅对自己拥有或已获明确授权的网站运行。它会输出 JSON，不发送 OOM/UAF/崩溃 payload，也不调用目标上的系统命令。

| 运行方式 | 实际请求 | 结论边界 |
| --- | --- | --- |
| `web check <URL> --skip-multipart` | 仅 HEAD/版本头 | 只有 HTTP/版本可见性 |
| `web check <URL> --skip-gadget-scan` | HEAD + 普通 multipart | parser 可达性，不做 session include 请求 |
| `web check <URL>` | 上述请求 + 固定 session/include marker 探测 | 受控 PHP `echo` marker 线索，不是 `system()`/RCE 证明 |

默认 marker 探测的细节：请求 filename 中只包含固定 `<?php echo '<随机 marker>'; ?>`，随后用少量固定 `page`、`file`、`include`、`path` 参数形态检查候选 session 路径。它不会请求真实用户文件，不含 `system()`，但若应用确有 LFI gadget，可能在目标 PHP 进程内执行该受控 `echo` 并写入普通请求/session 日志。

因此，无跳过选项的检查应在授权和合适维护窗口内使用；低影响盘点优先选 `--skip-gadget-scan`。

退出码：

- `0`：版本头显示处于受影响范围；
- `3`：检查已完成，但版本未证明受影响或版本头不可见；
- 其他非零：本地参数或请求处理错误。

重要字段：

- `verdict=vulnerable_version_exposed`：版本暴露，非生产 RCE；
- `evidence_tier=tier_2_parser_reachable`：普通 multipart 请求可达；
- `evidence_tier=tier_3_gadget_found`：固定 marker 经候选 include 路径返回；
- `rce_or_file_read_proven=true`：兼容字段名；当前只表示受控 marker 路径成立，不能解读为任意命令、用户数据读取或内存漏洞利用成功。

## `chatbug php2shell lab local-list`

本机 contract lab 用于 CI、文档和回归：

- 在当前进程临时绑定 `127.0.0.1`；
- 模拟 upload-progress/session 和 lab-only include sink 的正向响应；
- 以普通 `hello.php` 作为负向控制；
- 输出合成的 `/tmp`、`chatbug-marker.txt` 与随机 marker；
- 退出时关闭 socket、线程并清空内存状态。

它不启动 PHP、Docker 或系统 shell，因此不能作为真实 PHP 命令执行的证据。真实 PHP-FPM 命令验收应使用下一节的 Docker lab。

## `chatbug php2shell lab docker-list` {#chatbug-php2shell-lab-docker-list}

该命令必须提供 `--ssh-host`，且只用于自有 Docker 主机。它创建唯一 Compose project、internal Docker network 和临时合成 webroot；不发布主机端口、不挂载生产数据库/邮件/附件/用户目录/凭据/日志。

```bash
chatbug php2shell lab docker-list \
  --ssh-host <owned-docker-host> \
  --fpm-image <exact-runtime-image-or-digest> \
  --proof list-and-marker
```

- 默认镜像是 `php:8.1.34-fpm-alpine`，方便验证工作流；
- 要验证与被评估服务一致的 PHP-FPM runtime，请传入其精确镜像 digest；
- `--keep` 会保留临时 lab 供 SSH 人工检查；默认自动清理容器、网络和远端临时目录。

`--proof` 是固定 allowlist，不接受任意命令：

| proof | lab 内固定动作 | 正向验收 |
| --- | --- | --- |
| `list-tmp` | `ls -la /tmp` | 输出含合成 `chatbug-marker.txt` 的临时目录列表 |
| `cat-marker` | `cat /tmp/chatbug-marker.txt` | 输出本次随机 marker |
| `list-and-marker` | `ls -la /tmp; echo MARKER; cat /tmp/chatbug-marker.txt` | 同时输出目录列表、`MARKER` 和随机 marker |

`docker-list` 返回 `accepted=true` 的前提是正/负向 HTTP 状态均为 200、选择 proof 的正向证据出现、负向 `hello.php` 不出现 marker，并且默认清理完成。它证明的是“指定 PHP-FPM 运行时 + 故意加入的 lab include gadget”可到达固定命令输出，不代表真实业务应用或 PHP2Shell 内存漏洞已被利用。

## 选择命令

| 需求 | 推荐命令 |
| --- | --- |
| 只确认版本暴露 | `web check <URL> --skip-multipart` |
| 确认普通 multipart 入口 | `web check <URL> --skip-gadget-scan` |
| 在授权范围内检查固定 marker/include 线索 | `web check <URL>` |
| 运行无 Docker 的稳定回归用例 | `lab local-list` |
| 验收 PHP-FPM lab 中的固定 `ls/cat` | `lab docker-list --ssh-host ... --proof list-and-marker` |
