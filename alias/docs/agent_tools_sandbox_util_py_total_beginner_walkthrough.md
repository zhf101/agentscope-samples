# `agent/tools/sandbox_util.py` 小白导读

对应文件：`src/alias/agent/tools/sandbox_util.py`

这是 sandbox 工作区文件操作工具集。

---

## 1) 主要能力

1. 目录/文件列表读取
2. 文件读取（base64）
3. 创建/编辑/删除文件与目录
4. 下载 OSS 文件到工作区
5. 导出整个工作区文件

---

## 2) 安全边界

`_valid_workspace_path` 强制路径必须在 `/workspace` 下，
避免误操作容器其他路径。

---

## 3) 一句话总结

`sandbox_util.py` 是 sandbox 文件系统操作的安全封装层。
