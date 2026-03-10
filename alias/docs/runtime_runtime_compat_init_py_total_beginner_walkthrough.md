# `runtime/runtime_compat/__init__.py` 小白讲解

对应文件：`src/alias/runtime/runtime_compat/__init__.py`

这个文件是 runtime 兼容层的总说明入口。

---

## 兼容层目标

把 Alias 既有后端事件流适配到 AgentScope Runtime 协议。

子模块分工：
- `runner`：处理请求生命周期与服务调用
- `adapter`：处理消息事件格式转换

---

## 一句话总结

这是 Alias 接入 AgentScope Runtime 的协议桥接入口文档。
