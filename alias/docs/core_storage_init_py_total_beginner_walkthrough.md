# `core/storage/__init__.py` 完全小白讲解

对应文件：`src/alias/server/core/storage/__init__.py`

这是存储子模块导出入口。

---

## 作用

1. 导出 `StorageFactory`
2. 通过 `__all__` 控制对外暴露名称

`StorageFactory` 的职责是按配置选择实际存储实现（本地或 OSS）。

---

## 一句话总结

这个文件让外部统一从一个入口拿到存储工厂类。
