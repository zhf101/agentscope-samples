# `api/v1/file.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/api/v1/file.py`

这个文件是文件接口路由：上传、获取、分享、删除、预览。

---

## 1) 第 1-20 行：导入和路由器

路由前缀：
- `/files`

关键类型：
- `UploadFile`：FastAPI 上传文件对象
- `StreamingResponse`：流式响应（用于预览）

---

## 2) 第 23-37 行：上传文件

`POST /files/upload`

流程：
1. 从表单拿 `UploadFile`
2. 调 `file_service.upload_file(...)`
3. 返回 `UploadFileResponse`

---

## 3) 第 39-54 行：获取文件信息

`GET /files/{file_id}`

返回文件元数据（不是下载文件内容）。

---

## 4) 第 56-76 行：设置分享状态

`POST /files/{file_id}/share`

流程：
1. 校验用户
2. 调 `share_file(user_id, file_id, share)`
3. 返回更新后的 FileInfo

---

## 5) 第 78-96 行：删除文件

`DELETE /files/{file_id}`

调用：
- `file_service.delete_file(...)`

---

## 6) 第 98-120 行：文件预览

`GET /files/{file_id}/preview`

流程：
1. 调 `file_service.preview_file(...)`
2. 返回 `StreamingResponse(file_stream, media_type=...)`

异常：
- 捕获后转成 `HTTPException(500)`。

