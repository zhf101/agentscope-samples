"""Alias Runtime Compatibility Layer.

该目录是“协议兼容层”，目标是把 Alias 既有后端能力接入 AgentScope Runtime。

子模块分工：
- runner: 负责请求生命周期、会话上下文、调用 Alias ChatService。
- adapter: 负责把 Alias 原始流式事件转换成 Runtime 标准消息事件。

核心流程：

1. AliasRunner.stream_query 接收 Runtime 的 AgentRequest。
2. 调 Alias 的 ChatService 获取原始流式事件。
3. adapt_alias_message_stream 把 thought/tool_call/tool_result 等事件映射成 Runtime 标准 Message/Content。
4. 单例工厂 get_alias_runner() 保证全进程只初始化一个 Runner，避免重复启动资源。
"""
