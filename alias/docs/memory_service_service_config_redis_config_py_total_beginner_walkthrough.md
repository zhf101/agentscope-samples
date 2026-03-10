# `memory_service/service/config/redis_config.py` 完全小白讲解

对应文件：`src/alias/memory_service/service/config/redis_config.py`

这个文件定义了 memory-service 的 Redis 配置对象。

---

## 1) 配置内容

- 连接参数：`REDIS_HOST/PORT/DB/PASSWORD`
- 任务过期配置：`TASK_EXPIRY_HOURS`、`CLEANUP_MAX_AGE_HOURS`
- key 前缀：`KEY_PREFIX`

均支持环境变量覆盖。

---

## 2) 工具方法

1. `get_redis_url()`
- 生成 `redis://` 连接串

2. `get_task_expiry_seconds()`
- 把小时换算为秒

---

## 3) 一句话总结

`redis_config.py` 是后台任务状态存储的 Redis 参数来源。
