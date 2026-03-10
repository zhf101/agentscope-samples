# `services/conversation_service.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/services/conversation_service.py`

这个文件负责“会话（conversation）”的业务操作。  
比如：创建会话、列会话、删会话、更新 roadmap、收藏/分享/置顶。

---

## 1) 第 1-31 行：导入

重点对象：

1. `ConversationDao`（第 11 行）
- 会话数据访问层

2. `ConversationNotFoundError` / `AccessDeniedError`（第 12-15 行）
- 资源不存在、权限不足异常

3. `MessageService` / `PlanService` / `StateService`（第 24-26 行）
- 删除会话时要联动清理消息、计划、状态

4. `AliasSandbox`（第 30 行）
- 会话和沙盒关联，创建会话会创建沙盒

---

## 2) 第 33-46 行：类定义和初始化

```python
class ConversationService(BaseService[Conversation]):
```

含义：
- 会话服务继承通用 CRUD 服务。
- 初始化时顺带创建 message/plan/state 子服务对象。

---

## 3) 第 47-70 行：存在性校验

三个方法：
- `_validate_exists`
- `_validate_update`
- `_validate_delete`

逻辑相同：
- `await self.get(instance_id)` 查会话
- 查不到抛 `ConversationNotFoundError`

---

## 4) 第 72-99 行：`create_conversation(...)`

这是创建新会话的核心。

流程：
1. 构造 `AliasSandbox(...)`
2. 调 `sandbox.__enter__()` 创建/启动沙盒
3. 构造 `Conversation(...)` 数据
4. `await self.create(conversation_data)` 写库

关键细节（第 90-93 行）：
- 把 `sandbox.desktop_url` 里的 `localhost` 替换为 `settings.SANDBOX_PUBLIC_HOST`
- 让前端能用外部可访问地址

---

## 5) 第 100-112 行：`get_sandbox(...)`

作用：
- 根据 `conversation_id` 取回沙盒对象。

流程：
1. 查会话
2. 不存在抛错
3. 用会话里的 `sandbox_id` 构造 `AliasSandbox` 返回

---

## 6) 第 113-124 行：`list_conversations(...)`

作用：
- 按用户列会话（含总数+分页数据）。

返回值：
- `Tuple[int, List[Conversation]]`

---

## 7) 第 126-147 行：`list_conversation_messages(...)`

作用：
- 列某会话下消息。

关键安全校验：
1. 会话必须存在
2. `conversation.user_id` 必须等于当前 `user_id`

通过后：
- 调 `message_service` 分页查询消息

---

## 8) 第 149-179 行：`delete_conversation(...)`

这是“删除会话”的联动清理逻辑。

流程：
1. 校验会话存在
2. 校验用户权限
3. 删除消息、状态、计划
4. 清理沙盒 `sandbox._cleanup()`
5. 删除会话本身

注意：
- `sandbox._cleanup()` 是调用私有方法（前导下划线），项目里显式允许。

---

## 9) 第 181-209 行：roadmap 读写

### `get_roadmap(...)`
- 直接调用 `plan_service.get_roadmap(...)`

### `update_roadmap(...)`
流程：
1. 先取旧 roadmap
2. 记录“编辑 roadmap”埋点
3. 真正更新 roadmap 并返回

---

## 10) 第 210-220 行：`update_conversation(...)`

作用：
- 传入若干 `kwargs` 更新会话字段。

逻辑：
- 遍历 `kwargs.items()`
- 用 `hasattr` 检查字段是否存在
- `setattr` 动态赋值
- 更新 `update_time`

---

## 11) 第 222-243 行：`collect_conversation(...)`

作用：
- 收藏/取消收藏会话。

流程：
1. 查会话
2. 记录埋点
3. 更新 `conversation.collected`

---

## 12) 第 244-260 行：`share_conversation(...)`

作用：
- 设置会话是否共享。

安全校验：
- 会话存在
- 必须是会话拥有者（`conversation.user_id == user_id`）

---

## 13) 第 262-279 行：`pin_conversation(...)`

作用：
- 设置是否置顶会话。

同样有存在性和权限校验。

---

## 14) 第 281-290 行：`get_conversation(...)`

作用：
- 按 ID 取会话，不存在抛错。
- 这是其他方法常用的基础读取封装。

---

## 15) 本文件必须掌握的语法点

1. 服务层类继承
2. `Optional[T]` + 默认值
3. `kwargs` 动态字段更新
4. `hasattr` / `setattr`
5. 异步链式调用（服务间协作）
6. 先校验再执行的安全模式

