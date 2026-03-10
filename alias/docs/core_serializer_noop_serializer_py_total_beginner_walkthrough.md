# `core/serializer/noop_serializer.py` 完全小白逐行讲解

对应文件：`src/alias/server/core/serializer/noop_serializer.py`

No-Op 序列化器就是“什么都不做”。

---

## 行为

1. `serialize(obj)`：原样返回 `obj`
2. `deserialize(data, cls=None)`：原样返回 `data`

---

## 适用场景

- 数据本来就是目标格式，不需要转换
- 调试场景，临时关闭序列化变换

---

## 一句话总结

`NoOpSerializer` 是一个“透传实现”，用于不需要序列化处理的场景。
