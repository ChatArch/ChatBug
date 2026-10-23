# ChatBug 文档

ChatBug 是 ChatArch 系列的授权网站漏洞验证包。当前首个能力聚焦 PHP2Shell：对自有普通网站做安全暴露检查，并在无真实数据的一次性 lab 中复现“运行时 + LFI gadget → session upload-progress 注入 → `ls/cat` 输出”的完整验收链。

站点入口：<https://arch.gh.wzhecnu.cn/ChatBug/>

## 按场景选择文档

| 场景 | 文档 |
| --- | --- |
| 查看完整命令、选项和退出码 | [CLI 树](cli-tree.md) |
| 理解能力状态、证据层级和安全边界 | [能力地图](capability-map.md) |
| 从 Python 代码调用检查或 lab API | [Python 接口树](interface-tree.md) |
| 跑通本机或 PHP-FPM/Nginx 隔离复现实验 | [PHP2Shell 复现实验](php2shell-lab.md) |

## 最快开始

```bash
python -m pip install ChatBug
chatbug --tree
chatbug php2shell lab local-list
```

`local-list` 不需要 Docker、root、网络或真实 shell；它用进程内 HTTP lab 同时验证正向 include sink 和负向普通入口。

## 核心结论

- `web check <URL>` 是非破坏性自有网站检查：版本暴露、multipart 可达性和固定 gadget 探测必须分层报告。
- `lab local-list` 是确定性的本机教学/CI 用例。
- `lab docker-list --ssh-host <host>` 在 internal-only Docker lab 中用 exact/digest-pinned PHP-FPM 运行时证明固定 `ls/cat`，不挂生产数据，不发布端口。
- ChatBug 不发送 OOM/UAF/崩溃 payload，不提供任意命令或 reverse shell，不把版本暴露直接宣称为 RCE。

## 文档状态约定

- **已实现**：代码、测试和 CLI 路径已经存在。
- **已验证**：已经通过本地测试、CI 或一次性隔离 lab 验证。
- **不提供**：明确属于安全边界外，例如生产内存破坏利用或任意命令框架。

## 本地开发预览

```bash
python -m pip install -e ".[dev,docs]"
python -m pytest -q
mkdocs serve
```

英文入口：<https://arch.gh.wzhecnu.cn/ChatBug/en/>。缺少英文翻译的专题页会通过 i18n fallback 回退到默认语言。
