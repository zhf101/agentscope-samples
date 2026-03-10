# `services/message_service.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/services/message_service.py`

这个文件是“消息业务服务层”。  
它做的事很直白：创建消息、查消息、反馈消息、收藏工具消息、删除消息。

---

## 1) 第 1-26 行：导入

重点看这几个：

1. `MessageDao`（第 8 行）
- 数据访问层（DAO），负责和数据库交互。

2. `Message` / `BaseMessage` / `UserMessage`（第 14-21 行）
- 消息模型。

3. `ActionService`（第 23 行）
- 记录行为埋点（反馈、收藏等）。

4. `FileService`（第 25 行）
- 处理文件上传到沙盒相关逻辑。

---

## 2) 第 28-39 行：类定义和初始化

```python
class MessageService(BaseService[Message]):
```

小白解释：
- 这是继承 `BaseService` 的子类。
- 泛型 `[Message]` 表示这个服务主要操作 `Message` 模型。

第 29-30 行：
- `_model_cls = Message`
- `_dao_cls = MessageDao`

意思：告诉父类“我操作哪个模型、用哪个 DAO”。

---

## 3) 第 40-61 行：三种校验方法

方法：
- `_validate_exists`
- `_validate_update`
- `_validate_delete`

共同逻辑：
1. 先 `await self.get(instance_id)` 查消息
2. 查不到就抛 `MessageNotFoundError`

这 3 个方法是父类 CRUD 流程里常用的钩子校验。

---

## 4) 第 62-101 行：`create_user_message(...)`

这是创建“用户消息”的快捷方法。

流程：

1. 第 71-74 行：准备 `message_id`、`files`、`file_items`
2. 第 75-89 行：遍历传入文件 ID
   - 上传到沙盒
   - 组装 `FileItem`
3. 第 90-94 行：构造 `UserMessage`
4. 第 96-101 行：调用 `create_message(...)` 持久化

关键语法：
- `files = files or []`：若 `files` 为 `None`，给默认空列表。
- `await`：文件上传和数据库写入都是异步操作。

---

## 5) 第 103-122 行：`create_message(...)`

作用：
- 把 `BaseMessage`（业务消息对象）封装成数据库 `Message` 行对象并写库。

关键语句：

```python
message=message.model_dump()
```

解释：
- `model_dump()` 把 Pydantic/SQLModel 对象转成普通 `dict`，便于存入 JSON 字段。

---

## 6) 第 123-135 行：`list_messages(...)`

流程：
1. 按 `conversation_id` 过滤
2. 查总数 `total`
3. 分页查 `messages`
4. 返回 `(total, messages)` 元组

---

## 7) 第 136-157 行：`feedback_message(...)`

作用：
- 用户对消息点“赞/踩”等反馈。

流程：
1. 查消息，不存在抛错
2. 用 `ActionService.record_feedback(...)` 记录埋点
3. 修改 `message.feedback`
4. 调 `update(...)` 持久化

---

## 8) 第 158-185 行：`collect_tool_message(...)`

作用：
- 收藏或取消收藏“工具消息”。

关键检查（第 168-173 行）：
- 只有 `MessageType.THOUGHT` 才允许作为“工具消息”收藏。
- 否则抛 `InvalidToolMessageError`。

流程和反馈类似：
1. 校验消息存在
2. 校验消息类型
3. 记录埋点
4. 更新 `collected`

---

## 9) 第 186-190 行：`delete_messages(...)`

一句话：
- 根据 `conversation_id` 批量删除消息。

调用：

```python
await self.delete_all_by_field("conversation_id", conversation_id)
```

---

## 10) 本文件必须掌握的语法点

1. 类继承 + 泛型 `BaseService[Message]`
2. 异步函数 `async def` + `await`
3. `or` 默认值技巧（`x = x or []`）
4. 抛异常 `raise XxxError(...)`
5. 返回元组 `Tuple[int, List[Message]]`

