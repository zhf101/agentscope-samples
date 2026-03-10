# `api/v1/auth.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/api/v1/auth.py`

这个文件是认证接口路由：登录、注册、刷新 token、登出。

---

## 1) 第 1-18 行：导入和路由器

重点：
- `SessionDep`：数据库会话依赖
- `CurrentUser`：当前用户依赖（用于 logout）
- `AuthService`：鉴权业务服务

`router = APIRouter(tags=["auth"])`  
表示这些接口在文档里归类到 `auth`。

---

## 2) 第 21-41 行：`/login`

流程：
1. 创建 `AuthService`
2. 调 `authenticate(email, password)`
3. 调 `get_jwt_token(user.id)`
4. 返回 `LoginResponse`

---

## 3) 第 43-60 行：`/register`

流程：
1. 调 `auth_service.create_user(...)`
2. 把结果转换为 `UserInfo`
3. 返回 `RegisterResponse`

---

## 4) 第 62-80 行：`/refresh-token`

流程：
1. 接收 refresh_token
2. 调 `auth_service.refresh_token(...)`
3. 返回新的 `LoginResponse`

---

## 5) 第 82-94 行：`/logout`

当前实现：
- 只返回“登出成功”响应
- 没有额外 token 黑名单逻辑

---

## 6) 本文件语法重点

1. 路由装饰器 `@router.post(...)`
2. 依赖注入参数（`SessionDep`、`CurrentUser`）
3. `response_model=...` 响应模型约束

