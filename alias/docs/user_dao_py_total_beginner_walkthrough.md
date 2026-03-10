# `dao/user_dao.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/dao/user_dao.py`

这个文件在 `BaseDAO` 基础上增加了一个用户专用方法：更新最后登录信息。

---

## 1) 第 1-9 行：导入

重点：
- `request_context_var`：当前请求上下文（可取 IP）
- `get_current_time`：当前时间字符串

---

## 2) 第 11-13 行：类绑定

`UserDao(BaseDAO[User])`，模型是 `User`。

---

## 3) 第 14-26 行：`update_last_login_info(...)`

流程：
1. 查用户
2. 从请求上下文取 IP
3. 组装 `update_data` 字典
4. 写入 `last_login_time`，有 IP 则写 `last_login_ip`
5. 调 `update(...)` 更新数据库

---

## 4) 语法关键点

1. `request_context_var.get()` 读取上下文变量
2. 动态字典赋值 `update_data["k"] = v`
3. 复用父类 `update(...)`

