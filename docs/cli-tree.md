# CLI 树

`ChatBug` 的命令行是授权漏洞验证入口。以下命令树来自真实 Click 注册面；发布前用 `chatbug --tree` 回读，不手写未实现命令。

## 真实命令树

```text
chatbug
├── --help                                                                 # Show this message and exit.
├── --version                                                              # Show the version and exit.
├── --tree                                                                 # Print the registered CLI tree and exit.
├── --tree-brief                                                           # Print the registered CLI tree without parameter signatures and exit.
└── php2shell                                                              # PHP2Shell web checks and data-free lab proof.
    ├── lab                                                                # Disposable, data-free lab workflows.
    │   ├── docker-list --ssh-host TEXT --fpm-image TEXT --proof [list-tmp|cat-marker|list-and-marker] [--keep]  # Prove list/cat inside a data-free PHP-FPM lab with an intentional include sink.
    │   └── local-list                                                     # Run a complete positive/negative example in an in-process local lab.
    └── web                                                                # Checks for an ordinary owned website URL.
        └── check <URL> [--skip-multipart] [--skip-gadget-scan]            # Check version exposure, parser reachability, and common include gadgets.
```

## 命令说明

### `chatbug php2shell web check <URL>`

对一个**自己拥有或已获授权**的普通网站 URL 做非破坏性检查：

1. 读取 `Server` / `X-Powered-By` 中的 PHP 版本并按修复版本分类；
2. 发送一个普通 multipart POST，仅证明上传解析入口可达；
3. 用固定、小规模的常见 `page/file/include/path` 参数形态检查服务端是否能返回独立 marker；
4. 输出 JSON，不发送 OOM/UAF/崩溃 payload，不在目标上执行系统命令。

退出码：

- `0`：版本头显示处于受影响范围；
- `3`：检查完成但版本未证明受影响或版本头不可见；
- 非 `0/3`：请求或本地执行错误。

常用选项：

- `--skip-multipart`：只做版本/HTTP 检查；
- `--skip-gadget-scan`：跳过常见 include gadget 探测，只保留版本和 parser reachability。

### `chatbug php2shell lab local-list`

在当前进程内启动一个临时 HTTP lab，完整跑正/负向用例：

- 正向：合成的 LFI include sink 读取 session upload-progress 内容，并返回 `/tmp`、`chatbug-marker.txt` 和随机 marker；
- 负向：普通 `hello.php` 即使带相同路径参数也只返回 `Hello World`；
- 不需要 Docker、root、网络或真实 shell，适合 CI、文档示例和首轮教学复现。

### `chatbug php2shell lab docker-list --ssh-host <host> [--fpm-image <image>]`

在自有 SSH Docker 主机上创建一次性完整运行时 lab：

- 可配置的精确 PHP-FPM 镜像（默认 `php:8.1.34-fpm-alpine`，也可传生产同版本 digest-pinned 镜像）+ Nginx；
- internal Docker network，不发布主机端口；
- 临时 webroot 只包含 `Hello World` 和 lab-only `include($_GET['page'])`；
- 只挂载合成文件，不挂生产数据库、邮件、用户目录、凭据、日志或附件；
- 结束时自动删除 Compose 项目、网络和远端临时目录。

`--proof` 是固定 allowlist，不接受任意命令：

| proof | lab 内固定动作 | 验收 |
| --- | --- | --- |
| `list-tmp` | `ls -la /tmp` | 返回 lab 临时目录列表 |
| `cat-marker` | `cat /tmp/chatbug-marker.txt` | 返回随机合成 marker |
| `list-and-marker` | `ls -la /tmp; echo MARKER; cat /tmp/chatbug-marker.txt` | 同时返回目录列表、`MARKER` 和随机 marker |

`--keep` 仅用于手动复查；默认必须清理。保留中的 lab 仍没有公网/主机发布端口。

## 证据解释

- 版本暴露只说明修补优先级，不等于 RCE；
- multipart 200 只说明 parser reachability；
- `local-list` 证明包内确定性的 LFI/session 注入教学链可运行；
- `docker-list` 在同一 PHP-FPM 运行时和故意加入的 lab gadget 上证明文件包含可走到固定 `ls/cat`；
- 没有单独应用 LFI gadget 时，不应把内存破坏 CVE 宣称为“生产 RCE 已复现”。
