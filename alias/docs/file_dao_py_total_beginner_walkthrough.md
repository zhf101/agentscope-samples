# `dao/file_dao.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/dao/file_dao.py`

这是 `File` 模型的 DAO 绑定类。

---

## 1) 第 1-4 行：导入

- `BaseDAO`
- `File`

---

## 2) 第 6-7 行：类定义

```python
class FileDao(BaseDAO[File]):
    _model_class = File
```

作用：
- 复用 BaseDAO 通用 CRUD
- 指明模型是 `File`

