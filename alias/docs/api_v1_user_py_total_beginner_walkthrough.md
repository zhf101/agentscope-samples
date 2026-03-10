# `api/v1/user.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/api/v1/user.py`

这个文件提供用户管理接口：
- 超管添加/列出/获取/删除子用户
- 当前用户查看自己、改名、改密、改头像、注销

---

## 1) 第 1-27 行：导入和路由器

`router = APIRouter(prefix="/users", tags=["users"])`

依赖区分很关键：
- `CurrentSuperUser`：只有超级管理员能访问
- `CurrentUser`：普通登录用户即可访问

---

## 2) 第 30-49 行：新增用户（超管）

`POST /users`

流程：
1. 超管身份校验（依赖）
2. `UserService.create_user(...)`
3. 返回 `AddUserResponse`

---

## 3) 第 51-81 行：列用户（超管）

`GET /users`

流程：
1. 用 query 参数创建 `PaginationParams`
2. 调 `user_service.list_users(parent_id=current_user.id, ...)`
3. 返回分页结构 `PageUserInfo`

---

## 4) 第 83-91 行：获取自己

`GET /users/me`

直接把 `current_user` 转成 `UserInfo` 返回。

---

## 5) 第 94-110 行：改用户名

`POST /users/me/name`

调用：
- `user_service.update_user(user_id=current_user.id, username=...)`

---

## 6) 第 113-130 行：改密码

`POST /users/me/password`

调用：
- `user_service.update_user(..., password=旧密码, new_password=新密码)`

---

## 7) 第 133-149 行：改头像

`POST /users/me/avatar`

调用：
- `user_service.update_user(..., avatar=...)`

---

## 8) 第 152-164 行：注销自己

`DELETE /users/me`

调用：
- `user_service.delete_user(user_id=current_user.id)`

---

## 9) 第 167-183 行：超管查询指定用户

`GET /users/{user_id}`

调用：
- `user_service.get_user(parent_id=current_user.id, user_id=user_id)`

---

## 10) 第 186-199 行：超管删除指定用户

`DELETE /users/{user_id}`

调用：
- `user_service.delete_user(parent_id=current_user.id, user_id=user_id)`

---

## 11) 本文件语法重点

1. 路由依赖权限分层（CurrentUser vs CurrentSuperUser）
2. 分页参数构造
3. 请求模型与响应模型分离

