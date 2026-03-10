# `core/storage/storage_factory.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/core/storage/storage_factory.py`

这是存储工厂：根据配置返回 LocalStorage 或 OSSStorage。

---

## 1) 第 8-43 行：`StorageFactory.get_storage(...)`

流程：
1. 如果没传 `storage_type`，从 `settings.STORAGE_TYPE` 读取
2. 若是 `local`，创建 `LocalStorage(settings.LOCAL_STORAGE_DIR)`
3. 若是 `oss`，校验 OSS 配置齐全后创建 `OSSStorage(...)`
4. 其他类型抛 `ValueError`

---

## 2) 关键设计点

1. 工厂模式：调用方不关心具体类
2. 延迟导入：在分支里导入实现类，减少启动时依赖负担
3. 配置校验：避免 OSS 缺配置导致运行时更深层报错

