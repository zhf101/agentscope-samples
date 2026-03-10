# `models/field.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/models/field.py`

这个文件提供“字段工厂函数”，让模型里复用一致的字段定义。

---

## 1) 第 1-5 行：导入

- `datetime/timezone`：生成 UTC 时间
- `Field`：SQLModel 字段构造器

---

## 2) 第 7-19 行：账号相关字段工厂

函数：
- `email_field()`：唯一 + 索引 + 长度限制
- `username_field()`：用户名长度限制
- `password_field()`：密码长度限制

这些函数返回 `Field(...)`，在模型里直接调用复用。

---

## 3) 第 22-31 行：时间字段工厂

### `utc_datetime_field()`
- 默认值是 `datetime.now(timezone.utc)`（datetime 对象）

### `formatted_datetime_field()`
- 默认值是 `datetime.now(timezone.utc).isoformat()`（字符串）

---

## 4) 第 34-36 行：验证码字段

`verification_code_field()`：
- 固定长度 6 位

---

## 5) 本文件关键语法

1. 工厂函数返回 `Field(...)`
2. `default_factory=lambda: ...` 动态默认值
3. UTC 时间与 ISO 字符串格式

