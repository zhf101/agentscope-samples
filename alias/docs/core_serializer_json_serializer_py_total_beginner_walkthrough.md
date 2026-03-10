# `core/serializer/json_serializer.py` 完全小白逐行讲解

对应文件：`src/alias/server/core/serializer/json_serializer.py`

这个类实现 JSON 序列化/反序列化。

---

## 1) `serialize(obj)`

处理顺序：
1. `None` -> `"null"`
2. 有 `model_dump_json` -> 直接调用
3. 有 `model_dump` -> 先转 dict 再 `json.dumps`
4. 其它对象 -> `json.dumps(obj)`

失败时抛 `SerializationError`。

---

## 2) `deserialize(data, cls=None)`

1. `json.loads(data)` 得到 Python 对象
2. 如果传了 `cls` 且它支持 `model_validate`，再转成模型对象
3. 否则返回原始解析结果

失败时抛 `DeserializationError`。

---

## 3) 一句话总结

`JsonSerializer` 是“通用文本 JSON”序列化器，适合接口传输和可读存储。
