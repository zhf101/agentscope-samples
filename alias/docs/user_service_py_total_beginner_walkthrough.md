# `services/user_service.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/services/user_service.py`

这个文件负责用户管理业务：创建、更新、删除、查询、列表、登录信息更新。

---

## 1) 第 1-22 行：导入

重点：
- `UserDao`：用户 DAO
- 用户异常类（邮箱重复、密码错误、用户不存在等）
- 安全工具：`get_password_hash` / `verify_password`
- `is_valid_base64_image`：头像格式校验

---

## 2) 第 24-27 行：类绑定

```python
class UserService(BaseService[User]):
    _model_cls = User
    _dao_cls = UserDao
```

---

## 3) 第 29-41 行：`delete_user(...)`

流程：
1. 查用户是否存在
2. 如果传了 `parent_id`，还要校验归属
3. 调 `delete(...)`

---

## 4) 第 42-75 行：`update_user(...)`

功能：
- 改用户名
- 改密码
- 改头像

关键校验：
1. 用户存在
2. 若要改密码，先校验旧密码
3. 若传头像，必须是合法 base64 图片

最后：
- 更新 `update_time`
- 调 `update(...)` 写库

---

## 5) 第 77-103 行：`create_user(...)`

流程：
1. 邮箱查重
2. 密码哈希（如果有）
3. 构造 `User` 对象并写库

---

## 6) 第 105-116 行：`get_user(...)`

按 `user_id` 获取用户，可选校验 `parent_id` 归属。

---

## 7) 第 118-130 行：`list_users(...)`

按 `parent_id` 分页列用户，返回 `(total, users)`。

---

## 8) 第 132-135 行：`get_user_by_email(...)`

一句话：
- 按邮箱查用户。

---

## 9) 第 137-141 行：`update_last_login_info(...)`

调用 DAO 层方法更新：
- 最后登录时间
- 最后登录 IP

