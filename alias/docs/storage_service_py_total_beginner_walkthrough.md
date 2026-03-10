# `services/storage_service.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/services/storage_service.py`

这个文件是“存储门面层（Facade）”，把底层 Local/OSS 差异屏蔽掉。

---

## 1) 第 9-12 行：初始化

```python
self.storage = StorageFactory.get_storage()
```

含义：
- 根据配置返回具体存储实现（本地或 OSS）。

---

## 2) 第 13-15 行：`storage_type` 属性

返回当前底层存储类型（local/oss）。

---

## 3) 第 17-49 行：文件/目录基础操作

这些方法基本是“透传”到底层 storage：
- `get_size`
- `save_file`
- `load_file`
- `download_file`
- `copy_file`
- `delete_file`
- `list_files`
- `exists`
- `create_directory`
- `delete_directory`

---

## 4) 第 50-61 行：上传目录辅助

`create_upload_directory(user_id)`：
1. 生成相对目录 `uploads/{user_id}`
2. 创建目录
3. 可按 `absolute` 返回绝对或相对路径

`get_upload_directory` 只是封装调用。

---

## 5) 第 62-63 行：目录命名规则

`_generate_upload_directory` 返回：
- `uploads/<user_id>`

