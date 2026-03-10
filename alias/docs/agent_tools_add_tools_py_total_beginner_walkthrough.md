# `agent/tools/add_tools.py` 小白导读

对应文件：`src/alias/agent/tools/add_tools.py`

这个文件用于给通用模式注册额外工具。

---

## 主要接入

1. 多模态工具
- 音频转文本
- 图片转文本

2. Tavily MCP
- `tavily_search`
- `tavily_extract`

3. 金融 MCP 工具组
- 股票数据
- 金融资讯分析

---

## 一句话总结

`add_tools.py` 是通用工具扩展入口，负责把外部 MCP 能力挂到 toolkit。
