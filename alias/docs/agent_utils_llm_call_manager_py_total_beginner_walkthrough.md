# `agent/utils/llm_call_manager.py` 完全小白导读

对应文件：`src/alias/agent/utils/llm_call_manager.py`

这个文件封装了“带重试的模型调用”。

---

## 1) `model_call_with_retry`

使用 `tenacity` 装饰器：
- 最多重试 `MODEL_MAX_RETRIES`
- 每次间隔 5 秒
- 失败继续抛异常

并处理两种响应模式：
- 流式 `model.stream=True`
- 非流式一次性返回

---

## 2) `LLMCallManager`

维护模型名 -> `(model, formatter)` 的映射。  
调用时通过 `__call__` 统一发起推理并返回文本结果。

---

## 3) 一句话总结

`llm_call_manager.py` 让多模型调用变成统一入口，并内置稳健重试机制。
