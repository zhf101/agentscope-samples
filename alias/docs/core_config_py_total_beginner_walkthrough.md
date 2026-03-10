# `core/config.py` 完全小白语法级拆解

对应文件：`src/alias/server/core/config.py`

这个文件是项目“配置中心”。

---

## 1) 先理解它解决的问题

后端有大量配置：
- 数据库地址
- Redis 参数
- Token 密钥
- 日志配置
- 沙箱地址

如果散落在代码里会很难维护。  
`config.py` 的目标是：集中定义、自动读取、自动校验。

---

## 2) 关键技术：`BaseSettings`

大多数配置类都继承 `BaseSettings`。  
它会自动按优先级取值：
1. 环境变量
2. `.env` 文件
3. 代码默认值

所以你经常看到：

```python
DB_PORT: int = Field(default=5432)
```

含义：
- 没有环境变量时用 5432
- 有环境变量会自动覆盖并转成 `int`

---

## 3) 语法级重点

1. `Field(default=..., description=...)`
- 给字段默认值和描述

2. `Literal["a", "b"]`
- 限制字段只能取几个固定字符串

3. `Optional[T]`
- 字段可为空（`None`）

4. `@computed_field + @property`
- 把方法变成“计算出来的配置字段”
- 比如 `SQLALCHEMY_DATABASE_URI` 根据多个 DB 字段拼出来

5. 多重继承（Mixin）
- `Settings` 同时继承多个配置类（Application/Database/Redis...）
- 最终聚合成一个总配置对象 `settings`

---

## 4) 两个辅助函数做什么

### `find_env_file(...)`
- 在当前目录和上级目录查找 `.env` 或 `.env.example`
- 找不到就抛异常

### `parse_cors(v)`
- 把 CORS 配置统一成可用格式
- 支持字符串和列表输入

---

## 5) 最重要的计算逻辑

1. `SQLALCHEMY_DATABASE_URI`
- `USE_POSTGRESQL=True` 时拼 PostgreSQL URI
- 否则用 SQLite 文件 `alias-{ENVIRONMENT}.db`

2. `DB_CONNECTION_ARGS`
- 把连接池配置整理成字典
- 给 SQLAlchemy 创建引擎时使用

3. `model_post_init`
- 对象初始化完成后执行
- 如果没显式设置 `SANDBOX_URL`，就根据 host+port 自动拼接

---

## 6) 最终怎么被全项目使用

文件底部创建了：

```python
settings = Settings()
```

其它模块直接：

```python
from alias.server.core.config import settings
```

然后访问：
- `settings.API_V1_STR`
- `settings.SECRET_KEY`
- `settings.SQLALCHEMY_DATABASE_URI`

---

## 7) 一句话总结

`core/config.py` 是项目的“统一配置引擎”，负责读取环境变量、做类型校验、组装计算配置，并对外暴露全局 `settings`。
