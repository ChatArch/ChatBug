# ChatBug 文档

ChatBug 是 ChatArch 系列的授权网站漏洞验证包。它将 PHP2Shell 风险拆成可审计的证据层级：Web 运行时版本/入口暴露、受控 session/include marker，以及只在无生产数据 lab 中完成的固定 `ls/cat` 验收。

站点入口：<https://arch.gh.wzhecnu.cn/ChatBug/>

## 按场景选择文档

| 场景 | 从这里开始 |
| --- | --- |
| 只想确认运行时暴露，不做 gadget 请求 | [CLI 树：`web check` 低影响模式](cli-tree.md#chatbug-php2shell-web-check-url) |
| 需要理解 marker 探测的影响和证据边界 | [能力地图](capability-map.md) |
| 需要本机可运行的回归示例 | [PHP2Shell 隔离复现实验：本机 contract lab](php2shell-lab.md#本机-contract-lab) |
| 需要相同 PHP-FPM 运行时中的 `ls/cat` 验收 | [PHP2Shell 隔离复现实验：Docker lab](php2shell-lab.md#docker-运行时-lab) |
| 从 Python 调用检查或 lab 生命周期 | [Python 接口树](interface-tree.md) |

## 推荐路径

<div class="grid cards" markdown>

- **先做低影响检查**

    对自有或已授权 URL 先运行 `web check --skip-gadget-scan`。它只给出版本和 multipart parser 可达性，不宣称命令执行。

    [查看检查边界](cli-tree.md#chatbug-php2shell-web-check-url)

- **再理解 marker 结果**

    默认 `web check` 会增加固定 session/include marker 探测。marker 返回是受控 PHP `echo` 线索，不是系统命令 RCE 结论。

    [查看证据层级](capability-map.md#capability-status)

- **用本机 contract lab 回归**

    `local-list` 不启动 PHP、Docker 或 shell；它锁定请求/响应与正负向控制契约。

    [运行本机例子](php2shell-lab.md#本机-contract-lab)

- **只在隔离 Docker lab 验收命令输出**

    `docker-list` 使用内部网络、合成 marker、固定 proof allowlist 和自动清理。它是唯一提供 `ls/cat` 输出的路径。

    [运行 Docker lab](php2shell-lab.md#docker-运行时-lab)

</div>

## 当前结论

- 版本头或 parser 可达性是修补优先级证据，不是生产 RCE。
- session/include marker 返回需要结合目标应用、日志和授权范围复核；它不表示任意系统命令已经执行。
- `docker-list` 可以在同运行时、故意加入的 lab-only include gadget 中证明固定命令输出，但不能替代对真实应用 gadget 的审计。
- ChatBug 不发送 OOM/UAF/崩溃 payload，不读取生产用户数据，也不自动进行生产内存漏洞利用。

## 本地开发预览

```bash
python -m pip install -e ".[dev,docs]"
python -m pytest -q
mkdocs build --strict
mkdocs serve
```

英文入口：<https://arch.gh.wzhecnu.cn/ChatBug/en/>。每个核心页面都有英文镜像；语言切换器可在页面顶部切换。