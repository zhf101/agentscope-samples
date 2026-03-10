# `core/serializer/pikcle_serializer.py` 完全小白逐行讲解

对应文件：`src/alias/server/core/serializer/pikcle_serializer.py`

这个类实现 Pickle 二进制序列化。

---

## 1) `serialize(obj)`

用：

```python
pickle.dumps(obj, protocol=self.protocol)
```

得到 `bytes`。失败抛 `SerializationError`。

---

## 2) `deserialize(data, cls=None)`

1. `pickle.loads(data)` 还原对象
2. 若传了 `cls`，额外做 `isinstance` 校验
3. 不符合则抛 `DeserializationError`

---

## 3) 注意点

Pickle 反序列化有安全风险，不应加载不可信来源数据。

---

## 4) 一句话总结

`PickleSerializer` 适合 Python 内部对象的高保真序列化，但要注意安全边界。
