# `runtime/alias_sandbox/alias_sandbox.py` 小白结构导读

对应文件：`src/alias/runtime/alias_sandbox/alias_sandbox.py`

这个文件是 AliasSandbox 客户端适配器实现。

---

## 1) 关键职责

1. 通过装饰器注册 sandbox 镜像与类型
2. 继承 `BaseSandbox + GUIMixin` 提供标准沙箱能力
3. 封装文件上传/下载 API（`/workspace/*`）

---

## 2) 关键方法

1. `download_file(file_path)`
- 从沙箱工作区下载文件内容

2. `upload_file(file_path, content)`
- 上传二进制文件到沙箱工作区

---

## 3) 一句话总结

`alias_sandbox.py` 把底层沙箱 API 封装成上层易用的客户端类。
