# `services/file_service.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/services/file_service.py`

这个文件是文件业务主服务，负责：
- 上传到存储
- 访问控制
- 预览
- 上传到沙盒/从沙盒回读

---

## 1) 第 1-27 行：初始化

`FileService` 继承 `BaseService[File]`，并额外创建 `StorageService`。

---

## 2) 第 28-62 行：`upload_file(...)`

流程：
1. 读取上传文件内容
2. 计算大小和扩展名
3. 生成 `file_id`
4. 创建上传目录
5. 生成存储路径
6. 先保存二进制内容到存储
7. 再写 `File` 记录到数据库

---

## 3) 第 63-81 行：`download_file(...)`

流程：
1. 查文件是否存在
2. 校验当前用户是否有权限
3. 调 `storage_service.download_file(...)`

---

## 4) 第 82-97 行：`copy_file(...)`

和下载类似，但目标是复制到指定文件名。

---

## 5) 第 98-116 行：`delete_file(...)`

流程：
1. 查文件 + 权限校验
2. 先删存储中的物理文件
3. 再删数据库记录

---

## 6) 第 117-146 行：`load_file(...)`

作用：读取文件内容 bytes。

分支：
1. 普通存储（local/oss）：`storage_service.load_file`
2. 沙盒存储（`storage_type == "sandbox"`）：通过 `ConversationService.get_sandbox` 下载

---

## 7) 第 147-163 行：`share_file(...)`

作用：更新 `shared` 字段。

---

## 8) 第 164-184 行：`preview_file(...)`

流程：
1. 查文件
2. 读取原始字节
3. 调 `preview_file(file_path, file_ext, raw_data)` 转成可预览流

---

## 9) 第 185-221 行：`upload_to_sandbox(...)`

作用：
- 把已上传文件同步到某个会话对应沙盒。

流程：
1. 查文件 + 权限校验
2. 获取会话沙盒
3. 读取原文件内容并上传到沙盒 `/workspace`
4. 创建一条 `storage_type="sandbox"` 的文件记录

---

## 10) 第 222-264 行：`load_sandbox_file(...)`

作用：
- 根据文件名从沙盒读取文件，并同步/创建本地文件记录。

流程：
1. 先按条件查是否已有 sandbox 文件记录
2. 从沙盒下载内容和 mime
3. 若记录存在：更新 size
4. 若不存在：新建记录

