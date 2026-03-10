# `core/storage/base_storage.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/core/storage/base_storage.py`

这个文件定义存储接口抽象（协议），具体实现由 local_storage/oss_storage 完成。

---

## 1) 第 7-11 行：`StorageType` 枚举

可选存储类型：
- `local`
- `oss`
- `sandbox`

---

## 2) 第 13-57 行：`BaseStorage` 抽象类

语法重点：
- `ABC` + `@abstractmethod` 表示抽象基类
- 子类必须实现抽象方法

抽象方法包括：
- `get_size`
- `save_file`
- `load_file`
- `download_file`
- `copy_file`
- `exists`
- `list_files`
- `delete_file`
- `delete_directory`

非抽象默认实现：
- `create_directory` 默认直接返回目录字符串（子类可重写）

