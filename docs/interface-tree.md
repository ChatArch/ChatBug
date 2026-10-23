# Python 接口树

ChatBug CLI 是薄入口；HTTP 证据分层、marker 结构与 lab 生命周期都位于可导入、可测试的 Python 模块中。

## 包入口

```python
from chatbug import __version__
```

## 模块树

```text
chatbug
├── cli.py              # Click 参数、JSON 输出与退出码
├── php2shell.py        # Web 版本/marker 检查、固定 lab payload
├── local_lab.py        # 进程内合成 HTTP contract lab
└── lab.py              # 远端一次性 Docker Compose lab 生命周期
```

## `chatbug.php2shell`

```python
from chatbug.php2shell import (
    build_lab_session_payload,
    build_safe_multipart_probe,
    classify_version,
    extract_command_output,
    http_request,
    parse_php_version,
    random_marker,
    safe_url_check,
    scan_common_lfi,
)
```

| 接口 | 用途 | 安全/证据边界 |
| --- | --- | --- |
| `http_request(...)` | 无第三方依赖 HTTP 原语 | 不跟随跳转，最大读取 64 KiB |
| `parse_php_version(headers)` | 解析 `Server` / `X-Powered-By` PHP 版本 | 只读取响应头 |
| `classify_version(version)` | 分类 vulnerable/fixed/unknown | 不从隐藏版本推断已修补 |
| `random_marker()` | 生成随机、非敏感 marker | marker 不进入验证 URL/query/traversal |
| `build_safe_multipart_probe(marker)` | 构造 upload-progress multipart 请求 | 无 OOM/UAF/系统命令；filename 含固定 PHP `echo` marker，只有经 LFI include 才会执行 |
| `scan_common_lfi(url, sid, marker)` | 少量固定 session/include 形态 | 无任意路径输入；marker 返回只是候选 gadget 线索 |
| `safe_url_check(url, ...)` | 聚合版本、parser 与 marker 证据 | 不把版本或 marker 路径称为系统命令 RCE |
| `build_lab_session_payload(sid, proof)` | 为隔离 lab 构造固定 proof payload | `proof` 只允许三个 allowlist 模式 |
| `extract_command_output(body)` | 提取 lab 定界后的命令输出 | 只解析合成 lab 定界符 |

典型低影响网站检查：

```python
from chatbug.php2shell import safe_url_check

result = safe_url_check(
    "https://owned-site.example/",
    include_multipart=True,
    include_gadgets=False,
)
assert result["schema"] == "chatbug.php2shell.web_check/v1"
assert result["evidence_tier"] == "tier_2_parser_reachable"
```

启用 `include_gadgets=True` 前应确认目标授权和维护窗口。`rce_or_file_read_proven` 是兼容字段；在当前实现中，`True` 只表示受控 marker 经候选 session/include 路径返回，不表示任意系统命令或真实用户文件读取。

## `chatbug.local_lab`

```python
from chatbug.local_lab import serve_local_lab
```

`serve_local_lab()` 是 context manager，临时启动 `127.0.0.1:0` HTTP 服务：

- `hello.php` 固定返回 `Hello World`；
- `vuln.php` 是仅存在于进程内的 include-sink 模拟；
- context 退出时关闭 socket、线程并清空内存 session。

它不启动 PHP、Docker 或系统 shell，适合单元测试和文档中的最小 contract 用例。

## `chatbug.lab`

```python
from chatbug.lab import LabSpec, logs, run_lfi_proof, seed_marker, start, stop
```

| 接口 | 用途 |
| --- | --- |
| `LabSpec(ssh_host=..., fpm_image=...)` | 描述自有 Docker 主机与精确 PHP-FPM runtime |
| `start(spec)` | 写入合成 Compose/webroot 并启动 internal lab |
| `seed_marker(spec, remote_dir, marker)` | 在 lab `/tmp` 写入随机合成 marker |
| `run_lfi_proof(spec, remote_dir, sid, proof)` | 由内部一次性 client 执行固定正/负向验收 |
| `logs(spec, remote_dir)` | 读取有界 lab 日志用于失败诊断 |
| `stop(spec, remote_dir)` | 删除 Compose project、network 和远端临时目录 |

这些接口只生成合成文件，不接受生产路径、生产卷或任意远程命令。CLI 的 `docker-list` 在 `finally` 中调用清理；只有显式 `--keep` 才短时保留。

## 输出契约

### 网站检查

```text
chatbug.php2shell.web_check/v1
```

关键字段：`verdict`、`evidence_tier`、`rce_or_file_read_proven`、`findings`、`multipart`、`gadget_scan`。其中 `rce_or_file_read_proven` 需按上文兼容语义解释。

### 本机 contract lab

```text
chatbug.php2shell.local_lab/v1
```

关键字段：`accepted`、`post_status`、`positive_status`、`negative_status`、`positive_output`、`negative_body`。

### Docker runtime lab

```text
chatbug.php2shell.docker_lab/v1
```

关键字段：`accepted`、`fpm_image`、`proof`、`marker`、`seed`、`result.positive_output`、`result.negative_output`、`cleanup`。
