# `models/file.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/models/file.py`

这个文件定义文件记录表结构（元数据，不是文件二进制本体）。

---

## 1) 第 1-9 行：导入

重点：
- `formatted_datetime_field` 用于时间字符串默认值

---

## 2) 第 11-35 行：`FileBase`

关键字段：
- `filename`：原文件名
- `mime_type`：MIME 类型
- `extension`：扩展名
- `size`：大小
- `storage_path`：存储路径
- `storage_type`：存储类型（local/sandbox 等）
- `shared`：是否共享
- `user_id`：所属用户
- `conversation_id`：关联会话（沙盒文件常用）

---

## 3) 第 37-38 行：`File` 表模型

`table=True`，新增主键：
- `id: uuid.UUID`

