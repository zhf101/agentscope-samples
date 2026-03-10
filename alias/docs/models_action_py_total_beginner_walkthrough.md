# `models/action.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/models/action.py`

这个文件定义“行为类型枚举”，用于埋点事件分类。

---

## 1) 第 5-22 行：`ActionType`

包含行为种类，例如：
- 点赞/取消点赞
- 点踩/取消点踩
- 收藏会话、收藏工具
- 开始聊天、追问聊天、中断聊天
- 编辑 roadmap
- 执行 shell / 浏览器操作
- 任务停止

这些值通常会被 `schemas/action.py` 的 Action 对象引用。

---

## 2) 第 24-27 行：`FeedbackType`

- `like`
- `dislike`

用于消息反馈。

---

## 3) 第 29-31 行：`CollectType`

- `collect`
- `uncollect`

用于收藏类动作。

