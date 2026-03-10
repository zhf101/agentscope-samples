# `core/cache/redis_cache.py` 完全小白逐行讲解

对应文件：`src/alias/server/core/cache/redis_cache.py`

这是 Redis 缓存的异步封装类。

---

## 1) 核心设计

1. 统一使用 `JsonSerializer` 序列化值
2. 提供常见缓存 API：`set/get/delete/exists/expire/ttl`
3. 发生异常时记录日志并返回安全默认值

---

## 2) 重点方法

1. `set(key, value, ex)`
- 支持 `ex` 为秒数或 `timedelta`

2. `get(key)`
- 读 Redis 后反序列化成 Python 对象

3. `expire/ttl`
- 设置过期时间 / 查询剩余 TTL

---

## 3) 上下文管理器

实现了 `__aenter__` / `__aexit__`，可用：

```python
async with RedisCache() as cache:
    ...
```

---

## 4) 一句话总结

`RedisCache` 是面向业务层的“易用缓存包装器”，隐藏了序列化和异常处理细节。
