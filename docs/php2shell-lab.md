# PHP2Shell 隔离复现实验

本文说明如何用 ChatBug 安全复现“PHP 运行时风险 + 应用 LFI gadget”最终走到 `ls/cat` 输出的完整链路。例子使用普通网站模型，不为某一个具体业务系统保留专用 CLI。

## 结论边界

PHP2Shell 相关风险至少要分成两层：

1. **运行时暴露**：HTTP SAPI 使用未修复 PHP 版本，或 multipart/upload-progress 前置路径可达。这说明需要升级和排查，不等于已经能执行命令。
2. **端到端 gadget**：应用还存在攻击者可控制的 `include`/文件包含入口，能包含 session 文件并执行其中 PHP 代码。隔离 lab 中的 `ls/cat` 证明的是这一层。

ChatBug 不发送 CVE-2026-109618/109619 的 OOM/UAF/崩溃 payload。远端 lab 复现的是确定性的传统 PHP session upload-progress + LFI 链，并使用与被评估服务相同摘要固定的 PHP-FPM 运行时。

## 攻击链概览

```text
未认证 multipart POST
  └─ PHP_SESSION_UPLOAD_PROGRESS 让 PHP 把请求元数据写入 session 文件
      └─ filename 字段中夹带 <?php ... system(固定命令) ... ?>
          └─ 应用存在 include($user_controlled_path)
              └─ include /tmp/sess_<PHPSESSID>
                  └─ lab 返回 ls/cat 的定界输出
```

缺少任意一个条件都不能得到同样结论：

- 没有应用 LFI sink，只能证明运行时/解析入口暴露；
- 只有 `docker exec ... php` 是管理面执行，不是未授权利用；
- 普通 PHP 页面能读文件，也不能证明远程攻击者能执行命令。

## 1. 本机最小可运行例子

```bash
python -m pip install ChatBug
chatbug php2shell lab local-list
```

该命令：

- 在当前进程启动一个绑定 `127.0.0.1` 临时端口的 HTTP lab；
- 发送 upload-progress multipart 请求；
- 访问合成的 include sink；
- 同时访问普通 `hello.php` 负向入口；
- 退出时关闭 socket、线程并清空内存状态。

成功结果示例：

```json
{
  "accepted": true,
  "positive_status": 200,
  "negative_status": 200,
  "positive_output": "/tmp\nchatbug-marker.txt\nCHATBUG_MARKER_EXAMPLE",
  "negative_body": "Hello World\n"
}
```

验收条件：

- `accepted=true`；
- 正向输出包含 `/tmp`、`chatbug-marker.txt` 和随机 marker；
- 负向输出只有 `Hello World`。

本机 lab 不启动系统 shell，也不启动真实 PHP；它是包内确定性的教学/回归测试。CI 可直接运行：

```bash
python -m pytest -q tests/test_php2shell.py
```

## 2. 完整 PHP-FPM/Nginx 隔离 lab

在自有 Docker 主机上运行：

```bash
chatbug php2shell lab docker-list \
  --ssh-host <owned-docker-host> \
  [--fpm-image <digest-pinned-php-fpm-image>] \
  --proof list-and-marker
```

ChatBug 会在远端 `$HOME/.chatarch/chatbug/labs/` 下创建唯一临时目录，并生成：

- exact/digest-pinned PHP-FPM 镜像；
- Nginx 反代到 PHP-FPM；
- `hello.php`，只输出 `Hello World`；
- `vuln.php`，仅存在于 lab 中，包含 `include($_GET['page'])`；
- upload-progress/session 配置；
- internal-only Docker network；
- 一次性 Python client 容器。

不会挂载：生产数据库、邮箱数据、附件、用户目录、凭据、日志或真实 session 目录；也不会发布主机端口。

## 3. 固定 proof 模式

`--proof` 不接受任意 shell 命令，只允许：

```text
list-tmp         -> ls -la /tmp
cat-marker       -> cat /tmp/chatbug-marker.txt
list-and-marker  -> ls -la /tmp; echo MARKER; cat /tmp/chatbug-marker.txt
```

默认 `list-and-marker` 同时给出目录列举和唯一文件内容，便于区分：

- 命令确实在 lab 容器内执行；
- 读到的是服务端 `/tmp/chatbug-marker.txt`，而不是请求反射。

## 4. 正/负向验收

成功时，JSON 的 `result.positive_output` 会包含类似内容：

```text
___START___
total 24
drwxrwxrwt 1 root root 4096 ... .
...
-rw-r--r-- 1 root root 32 ... chatbug-marker.txt
-rw------- 1 www-data www-data ... sess_lab...
MARKER
CHATBUG_MARKER_...
___END___
```

`result.negative_output` 必须是：

```text
Hello World
```

只有同时满足以下条件才标记 `accepted=true`：

- POST 返回 200；
- 正向 include sink 返回 200；
- 负向普通页面返回 200；
- 正向输出包含本次随机 marker；
- 负向输出不包含 marker；
- Compose 项目和远端临时目录最终成功清理。

## 5. 普通生产网站检查

对真实服务，只运行安全检查：

```bash
chatbug php2shell web check https://owned-service.example/
```

结果解释：

| 字段 | 含义 |
| --- | --- |
| `verdict=vulnerable_version_exposed` | 版本头显示受影响，需要升级/进一步确认实际 SAPI |
| `evidence_tier=tier_2_parser_reachable` | 普通 multipart 请求能到达解析路径 |
| `evidence_tier=tier_3_gadget_found` | 固定探测返回独立 marker，发现文件包含 gadget 证据 |
| `rce_or_file_read_proven=false` | 尚未证明文件读取或 RCE |

该命令不会在生产上执行 `ls/cat`，也不会发送内存破坏 payload。

## 6. 复现后的处置建议

1. 盘点所有实际对外服务 HTTP 请求的 PHP SAPI：FPM、mod_php、FrankenPHP、LiteSpeed 等；CLI 版本不能作为 Web 运行时结论。
2. 升级到官方修复版本，并用新版本 header、包版本或容器 digest 回读。
3. 搜索并移除应用中的未授权文件包含/路径拼接 sink。
4. 收紧上传、session 保存路径、临时目录权限和错误暴露。
5. 升级后重新运行 `web check`，在同一数据-free lab 中重跑正/负向验收。
6. 若怀疑已被利用，另行检查访问日志、异常 session、WebShell、子进程和出站连接，不用漏洞验证命令替代取证。
