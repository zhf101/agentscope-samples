# `core/cache/__init__.py` 完全小白讲解

对应文件：`src/alias/server/core/cache/__init__.py`

这是核心缓存导出入口。

---

## 作用

1. 把 `RedisCache` 以别名 `Cache` 导出
2. 上层代码可写成：

```python
from alias.server.core.cache import Cache
```

这样后续切换缓存实现时，上层改动更小。

---

## 一句话总结

这个文件通过别名导出降低了调用层与具体缓存实现的耦合。
