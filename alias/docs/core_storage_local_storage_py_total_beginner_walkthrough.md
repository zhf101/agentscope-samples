# `core/storage/local_storage.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/core/storage/local_storage.py`

这个文件实现本地文件系统存储。

---

## 1) 第 10-15 行：初始化

`root` 作用：
- 作为相对路径的根目录
- 若为空则直接按当前环境解析

---

## 2) 第 16-42 行：读写与下载

- `get_size`：文件大小
- `save_file`：写 bytes
- `load_file`：读 bytes
- `download_file`：复制到目标文件名

都先 `_normalize_path`，确保路径一致。

---

## 3) 第 43-78 行：`copy_file`

支持复制文件或目录：
- 目录：`shutil.copytree`
- 文件：`shutil.copy2`

失败会抛 `IOError`。

---

## 4) 第 79-117 行：删除/列目录

- `delete_file`
- `list_files`
- `exists`
- `create_directory`
- `delete_directory`

都会做路径存在性和类型检查。

---

## 5) 第 118-125 行：`_normalize_path`

规则：
1. 先展开 `~`
2. 绝对路径直接 resolve
3. 相对路径拼到 root（若有）
4. 最终 resolve

