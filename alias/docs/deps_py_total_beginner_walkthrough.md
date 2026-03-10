# `api/deps.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/api/deps.py`

这个文件是 FastAPI 的“依赖工厂”。  
你可以理解成：提前定义好“怎么拿用户、怎么拿数据库会话、怎么做权限检查”。

---

## 1) 第 1-15 行：文件头说明

- 文档写得很清楚：这里放可复用依赖，避免每个路由重复写鉴权代码。

---

## 2) 第 17-28 行：导入

重点导入：

1. `Depends`（第 19 行）
- FastAPI 依赖注入核心工具

2. `OAuth2PasswordBearer`（第 20 行）
- 从请求头里读取 Bearer Token

3. `AuthService`（第 28 行）
- 根据 token 查用户

---

## 3) 第 32-34 行：`reusable_oauth2`

```python
reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="...")
```

含义：
- 定义一个“可复用 token 提取器”
- 路由执行时，它会去找 `Authorization: Bearer xxx`

---

## 4) 第 38 行：`SessionDep`

```python
SessionDep = Annotated[AsyncSession, Depends(get_session)]
```

小白翻译：
- 这是一个“参数模板”
- 谁声明参数类型为 `SessionDep`，FastAPI 就自动给它一个数据库会话

---

## 5) 第 41 行：`TokenDep`

```python
TokenDep = Annotated[str, Depends(reusable_oauth2)]
```

小白翻译：
- 谁用 `TokenDep`，就自动拿到 token 字符串

---

## 6) 第 44-52 行：`get_current_user(...)`

函数签名：

```python
async def get_current_user(session: SessionDep, token: TokenDep) -> User:
```

流程：
1. 拿到数据库会话
2. 拿到 token
3. 交给 `AuthService.get_user_by_token` 查用户
4. 返回 `User` 对象

---

## 7) 第 55 行：`CurrentUser`

```python
CurrentUser = Annotated[User, Depends(get_current_user)]
```

小白翻译：
- 这是“当前用户依赖”的快捷写法
- 在路由里写 `current_user: CurrentUser` 就能直接拿用户对象

---

## 8) 第 58-69 行：超级管理员依赖

### `get_current_active_superuser`（第 58-66 行）
- 检查 `current_user.is_superuser`
- 不是就抛 `PermissionDeniedError`

### `CurrentSuperUser`（第 69 行）
- 路由可直接声明超级管理员依赖

---

## 9) 第 72-89 行：内部 API Key 校验

函数：

```python
async def verify_inner_api_key(api_key: Optional[str] = Header(...)) -> bool:
```

关键语法：
- `Header(None, alias="X-Inner-Api-Key")`
  - 从请求头读取这个字段
  - 若没传，默认是 `None`

逻辑：
1. 如果系统没配置 `INNER_API_KEY`，放行（开发模式常见）
2. 配置了就必须匹配
3. 不匹配抛 `AccessDeniedError`

---

## 10) 第 93 行：`InnerAPIAuth`

```python
InnerAPIAuth = Depends(verify_inner_api_key)
```

小白翻译：
- 给路由加上这个依赖后，请求会先过 API Key 检查。

---

## 11) 本文件必须掌握的语法

1. `Annotated[...]`
2. `Depends(...)`
3. `Header(...)`
4. `Optional[...]`
5. `raise` 抛异常

---

## 12) 路由里如何使用（最小示例）

```python
@router.get("/me")
async def me(current_user: CurrentUser):
    return {"id": str(current_user.id)}
```

你不用手动写查用户逻辑，因为 `deps.py` 已经封装好了。

