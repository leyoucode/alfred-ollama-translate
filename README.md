# Ollama 翻译 — Alfred Workflow

基于 Ollama 本地大模型的中英互译 Alfred Workflow。翻译完全在本机运行，无需联网，保护隐私。

## 使用方法

| 关键词 | 功能 | 示例 |
|--------|------|------|
| `ten` | 中文 → 英文 | `ten 你好世界` |
| `tcn` | 英文 → 中文 | `tcn hello world` |

输入后稍等片刻，翻译结果会显示在 Alfred 中。按回车即可复制到剪贴板。

## 前置要求

1. [Alfred](https://www.alfredapp.com/) + Powerpack
2. [Ollama](https://ollama.ai/) 已安装并运行
3. 拉取翻译模型：

```bash
ollama pull qwen2:7b
```

## 安装

下载本仓库，双击 `.alfredworkflow` 文件导入，或将整个目录放到 Alfred 的 workflows 目录下。

## 配置

如需更换模型，编辑 `translate.py` 顶部的常量：

```python
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2:7b"
```

## 常见问题

**提示「无法连接 Ollama」**
确认 Ollama 已启动：`ollama serve`，默认监听 `localhost:11434`。

**提示「翻译超时」**
默认超时 30 秒。首次调用模型可能需要加载，请重试一次。也可考虑换用更小的模型以加快响应。

## License

MIT
