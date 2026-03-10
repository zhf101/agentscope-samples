# `core/serializer/__init__.py` 完全小白讲解

对应文件：`src/alias/server/core/serializer/__init__.py`

这是序列化模块导出入口。

---

## 导出的内容

- `BaseSerializer`：抽象基类
- `JsonSerializer`：JSON 序列化实现
- `NoOpSerializer`：不做变换的实现
- `PickleSerializer`：Pickle 序列化实现

并通过 `__all__` 控制导出集合。

---

## 一句话总结

这个文件把多个序列化实现统一组织成一个对外入口。
