# `runtime/alias_sandbox/box/routers/workspace.py` 小白导读

对应文件：`src/alias/runtime/alias_sandbox/box/routers/workspace.py`

这个文件提供沙箱 `/workspace` 文件系统 API。

---

## 1) 安全核心

`ensure_within_workspace(path)`：
- 把输入路径规范化为绝对路径
- 强制必须在 `/workspace` 根目录内
- 阻断路径穿越攻击

---

## 2) 主要接口

- 文件下载/上传/创建/删除
- 目录创建/删除
- 列表、移动、复制等操作

---

## 一句话总结

`workspace.py` 是沙箱文件系统操作网关，重点是“功能丰富 + 路径安全约束”。
