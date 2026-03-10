# `runtime/alias_sandbox/box/dependencies/__init__.py` 完全小白讲解

对应文件：`src/alias/runtime/alias_sandbox/box/dependencies/__init__.py`

这是 dependencies 导出入口文件。

---

## 作用

导出：
- `verify_secret_token`

让 `app.py` 能简洁导入并统一挂载鉴权依赖。

---

## 一句话总结

它是沙箱依赖函数的包级导出入口。
