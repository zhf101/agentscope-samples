# `models/user.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/models/user.py`

这个文件定义用户表结构，包括邮箱、用户名、密码、登录信息、父子账号关系。

---

## 1) 第 1-11 行：导入

重点：
- `EmailStr`：Pydantic 的邮箱类型（自动校验格式）
- `email_field/username_field/formatted_datetime_field`：字段工厂函数

---

## 2) 第 14-26 行：`UserBase`

基础字段：
- `email`（邮箱）
- `username`（用户名）
- `avatar`（头像）
- `is_active` / `is_superuser`
- `create_time` / `update_time`
- `last_login_time` / `last_login_ip`

---

## 3) 第 29-43 行：`User` 表模型

新增字段：
- `id` 主键 UUID
- `password`（可选）
- `oauth_provider/oauth_id`
- `parent_id`（父账号）

关系：
- `conversations`：用户的会话列表
- `parent`：父用户
- `children`：子用户列表

---

## 4) 第 44-47 行：`has_password` 属性

```python
@property
def has_password(self) -> bool:
    return self.password is not None
```

作用：
- 快速判断用户是否设置了密码。

