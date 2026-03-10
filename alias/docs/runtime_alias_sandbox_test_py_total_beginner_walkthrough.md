# `runtime/alias_sandbox/test.py` 完全小白讲解

对应文件：`src/alias/runtime/alias_sandbox/test.py`

这是一个手动烟雾测试脚本。

---

## 运行后会做什么

1. `with AliasSandbox()` 创建并进入沙箱
2. 打印 `sandbox_id`
3. 在沙箱里执行一段 IPython 代码
4. 等待你按回车后退出

---

## 一句话总结

`test.py` 用于本地快速验证 alias 沙箱是否可正常创建和执行代码。
