# `memory_service/memory_base/userinfo_pool.py` 完全小白讲解

对应文件：`src/alias/memory_service/memory_base/userinfo_pool.py`

这个类负责抽取“用户信息类记忆”。

---

## 主流程

1. 预处理内容
2. 组装用户提示词
3. 调用 LLM 抽取
4. 把输出文本解析成 `list[str]`

---

## 关键点

`_format_llm_output_to_list` 使用正则 + `ast.literal_eval`，
把类似 `["a","b"]` 的文本结果转为 Python 列表。

---

## 一句话总结

`userinfo_pool.py` 是“用户事实信息抽取器”。
