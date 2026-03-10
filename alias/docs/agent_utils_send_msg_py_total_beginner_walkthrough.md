# `agent/utils/send_msg.py` 小白结构导读

对应文件：`src/alias/agent/utils/send_msg.py`

这个文件是 agent 输出消息到后端会话的关键适配层。

---

## 1) 核心函数

1. `_determine_message_type(...)`
- 根据内容块判断是 RESPONSE / TOOL_USE / TOOL_RESULT 等

2. `_create_assistant_message(...)`
- 按类型构造具体消息模型对象

3. `send_as_msg(...)`
- 把消息写入 `SessionService`
- 支持新建消息或续写已有 `db_msg_id`

---

## 2) 为什么重要

它把 AgentScope 的 `Msg` 结构映射到项目自己的 `MessageType + BaseMessage` 体系，是两套消息协议的桥。

---

## 3) 一句话总结

`send_msg.py` 负责“识别消息类型 -> 构造后端消息模型 -> 入库发送”的完整链路。
