# `utils/redis.py` 完全小白逐行讲解

对应文件：`src/alias/server/utils/redis.py`

这个文件负责 Redis 连接字符串和异步客户端初始化。

---

## 1) `get_redis_url(...)`

功能：
1. 参数优先，未传则读取 `settings`
2. 校验 host/port/db
3. 拼接 `redis://` URL
4. 用户名密码用 `quote_plus` 做 URL 编码

---

## 2) `init_aio_redis(...)`

1. 先调用 `get_redis_url` 得到连接串
2. 再 `aioredis.from_url(redis_url)` 创建客户端

---

## 3) `redis_client`

模块底部创建了全局客户端：

```python
redis_client = init_aio_redis()
```

其它模块可直接导入复用。

---

## 4) 一句话总结

`utils/redis.py` 是项目 Redis 连接与客户端创建的统一入口。
