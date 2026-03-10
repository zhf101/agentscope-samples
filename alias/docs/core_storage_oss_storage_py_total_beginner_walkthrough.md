# `core/storage/oss_storage.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/core/storage/oss_storage.py`

这个文件实现阿里云 OSS 存储。

---

## 1) 第 12-24 行：初始化 OSS 客户端

输入配置：
- `access_key_id`
- `access_key_secret`
- `endpoint`
- `bucket_name`

初始化后得到 `self.bucket` 用于对象操作。

---

## 2) 第 25-44 行：`get_size`

通过 `get_object_meta` 取 `Content-Length`。

异常处理：
- `NoSuchKey` -> 文件不存在
- `ServerError/RequestError` -> 记录日志并抛出

---

## 3) 第 45-69 行：保存/读取/下载

- `save_file` -> `put_object`
- `load_file` -> `get_object().read()`
- `download_file` -> `get_object_to_file`

---

## 4) 第 70-98 行：复制/删除/存在性

- `copy_file`：先 load 再 save
- `delete_file`：删除对象
- `exists`：`object_exists`

---

## 5) 第 99-128 行：目录模拟

OSS 本质是对象存储，没有真实目录。  
这里用“前缀 + `/`”模拟目录：
- `list_files(prefix)`
- `create_directory`（创建空对象）
- `delete_directory`（删前缀下所有对象）

---

## 6) 第 129-130 行：路径规范

`_normalize_path`：去掉前导 `/`，转成 OSS key。

