# `cache/plan_cache.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/cache/plan_cache.py`

这个文件是 `Plan` 的专用缓存类。

---

## 1) 第 1-8 行：导入

- `Plan` 模型
- `BaseCache` 父类

---

## 2) 第 10-13 行：类配置

```python
class PlanCache(BaseCache[Plan]):
    _model_cls = Plan
    _cache_prefix = "plan"
    _cache_expire = 60
```

解释：
- 缓存对象类型：`Plan`
- 键前缀：`plan`
- 过期：60 秒

---

## 3) 为什么这么短？

因为通用逻辑都在 `BaseCache`。  
这里仅做“模型 + 前缀 + 过期时间”的配置。

