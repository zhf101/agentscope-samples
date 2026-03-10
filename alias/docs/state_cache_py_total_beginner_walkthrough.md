# `cache/state_cache.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/cache/state_cache.py`

这个文件是 `State` 的专用缓存类。

---

## 1) 第 1-8 行：导入

- `State` 模型
- `BaseCache` 父类

---

## 2) 第 10-13 行：类配置

```python
class StateCache(BaseCache[State]):
    _model_cls = State
    _cache_prefix = "state"
    _cache_expire = 60
```

解释：
- 缓存对象类型：`State`
- 键前缀：`state`
- 过期：60 秒

---

## 3) 关键理解

`state_cache.py` 和 `plan_cache.py` 基本是同一模式。  
这就是“配置式复用”：复用父类逻辑，只改少量参数。

