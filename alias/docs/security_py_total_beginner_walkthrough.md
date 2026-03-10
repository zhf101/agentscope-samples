# `utils/security.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/utils/security.py`

这个文件非常基础：密码哈希和密码校验。

---

## 1) 第 1-5 行：导入和初始化

```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

含义：
- 使用 `bcrypt` 方案进行密码哈希。

---

## 2) 第 8-9 行：`verify_password(...)`

作用：
- 校验“明文密码”是否匹配“哈希密码”。

---

## 3) 第 12-13 行：`get_password_hash(...)`

作用：
- 把明文密码哈希后存储到数据库。

---

## 4) 小白必懂安全原则

1. 数据库不存明文密码
2. 登录时用“明文 vs 哈希校验”
3. 哈希算法应使用专门密码算法（如 bcrypt）

