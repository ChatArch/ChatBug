# Python 接口树

ChatBug CLI 是薄入口；PHP2Shell 的 HTTP 判断、payload 构造和实验环境生命周期都放在可导入、可测试的 Python 模块中。

## 包入口

```python
from chatbug import __version__
```

## 模块树

```text
chatbug
├── cli.py              # Click 命令、参数解析、JSON 退出码；不保存远程状态
├── php2shell.py        # 普通网站安全检查、版本分类、固定 lab payload
├── local_lab.py        # 进程内确定性 HTTP lab，供测试和文档复现
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

| 接口 | 用途 | 安全边界 |
| --- | --- | --- |
| `http_request(url, method=..., headers=..., data=...)` | 小型无第三方依赖 HTTP 原语 | 不跟随跳转，限制响应读取大小 |
| `parse_php_version(headers)` | 从 `Server` / `X-Powered-By` 解析 PHP 版本 | 只读响应头 |
| `classify_version(version)` | 按首个修复版本分类 vulnerable/fixed/unknown | 不推断隐藏版本后的状态 |
| `random_marker()` | 生成随机非敏感验收 marker | marker 不进入读取验证 URL |
| `build_safe_multipart_probe(marker)` | 构造普通 upload-progress multipart 请求 | 不含 OOM/UAF/崩溃 payload |
| `scan_common_lfi(url, sid, marker)` | 扫描固定常见 include 参数形态 | 小规模、固定路径、无任意 traversal 输入 |
| `safe_url_check(url, ...)` | 聚合网站版本/parser/gadget 证据 | 返回证据层级，不声称已 RCE |
| `build_lab_session_payload(sid, proof)` | 构造隔离 lab 的固定 session payload | `proof` 只允许三个 allowlist 模式 |
| `extract_command_output(body)` | 提取 lab 正/负向响应中的定界输出 | 只解析本次合成定界符 |

典型网站检查：

```python
from chatbug.php2shell import safe_url_check

result = safe_url_check("https://owned-site.example/")
assert result["schema"] == "chatbug.php2shell.web_check/v1"
assert result["rce_or_file_read_proven"] in {True, False}
```

## `chatbug.local_lab`

```python
from chatbug.local_lab import serve_local_lab
```

`serve_local_lab()` 是 context manager，启动绑定 `127.0.0.1:0` 的临时 HTTP 服务：

- `hello.php` 固定返回 `Hello World`；
- `vuln.php` 是仅存在于进程内 lab 的 include sink 模拟；
- 退出 context 后关闭 socket、线程并清空内存 session。

它不启动 PHP、Docker 或系统 shell，适合单元测试和文档中的最小可运行例子。

## `chatbug.lab`

```python
from chatbug.lab import LabSpec, logs, run_lfi_proof, seed_marker, start, stop
```

| 接口 | 用途 |
| --- | --- |
| `LabSpec(ssh_host=...)` | 描述自有 Docker 主机和一次性 lab 配置 |
| `start(spec)` | 写入合成 Compose/webroot 文件并启动 internal lab |
| `seed_marker(spec, remote_dir, marker)` | 在 lab 容器 `/tmp` 写入随机合成 marker |
| `run_lfi_proof(spec, remote_dir, sid, proof)` | 从内部一次性 client 跑固定正/负向验收 |
| `logs(spec, remote_dir)` | 读取有界日志，用于失败诊断 |
| `stop(spec, remote_dir)` | 删除 Compose 项目和远端临时目录 |

这些接口只生成合成文件，不接受生产路径或任意远程命令。CLI 的 `docker-list` 在 `finally` 中调用清理；只有显式 `--keep` 才短时保留。

## 输出契约

### 网站检查

```text
chatbug.php2shell.web_check/v1
```

关键字段：`verdict`、`evidence_tier`、`rce_or_file_read_proven`、`findings`、`multipart`、`gadget_scan`。

### 本机 lab

```text
chatbug.php2shell.local_lab/v1
```

关键字段：`accepted`、`post_status`、`positive_status`、`negative_status`、`positive_output`、`negative_body`。

### Docker lab

```text
chatbug.php2shell.docker_lab/v1
```

关键字段：`accepted`、`marker`、`seed`、`result.positive_output`、`result.negative_output`、`cleanup`。
