# `agent/tools/improved_tools/multimodal_to_text.py` 小白导读

对应文件：`src/alias/agent/tools/improved_tools/multimodal_to_text.py`

这个文件提供 DashScope 多模态转文本工具。

---

## 1) 主要方法

1. `dashscope_audio_to_text(...)`
- 音频 -> 文本

2. `dashscope_image_to_text(...)`
- 图片 -> 文本描述

---

## 2) 输入来源

两种都支持：
- 公网 URL
- 沙箱工作区文件（base64 读取后转临时文件）

---

## 3) 一句话总结

`multimodal_to_text.py` 让 agent 可以把音频/图片内容转成可继续推理的文本。
