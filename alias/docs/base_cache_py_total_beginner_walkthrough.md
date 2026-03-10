# `cache/base_cache.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/cache/base_cache.py`

这个文件是缓存层父类，封装了“键拼接、写缓存、读缓存、删缓存”。

---

## 1) 第 1-10 行：导入和泛型

重点：
- `timedelta`：缓存过期时间单位
- `ModelType` 泛型：缓存里存放某个 SQLModel 类型

---

## 2) 第 13-22 行：类定义和初始化

类变量：
- `_model_cls`：缓存对象模型类
- `_cache_prefix`：键前缀
- `_cache_expire`：过期时间

初始化逻辑：
1. 如果没传 `redis_cache`，就创建默认 `Cache()`
2. 若没设置前缀，默认使用模型类名小写

---

## 3) 第 23-25 行：`_get_cache_key(...)`

```python
return f"{self._cache_prefix}:" + ":".join(str(arg) for arg in args)
```

作用：
- 统一生成缓存键，例如：`plan:conversation_id`

---

## 4) 第 26-33 行：`set_cache(...)`

流程：
1. 拼接键
2. 调底层 `cache.set(...)`
3. `ex=self._cache_expire` 表示设置过期时间

---

## 5) 第 34-43 行：`get_cache(...)`

流程：
1. 拼键
2. 读缓存原始数据
3. 如果有数据，用 `model_validate` 转回模型对象

---

## 6) 第 44-46 行：`clear_cache(...)`

作用：
- 按键删除缓存。

---

## 7) 必须掌握语法

1. 泛型类 `Generic[ModelType]`
2. f-string
3. 生成器表达式 `str(arg) for arg in args`
4. `model_validate(...)`

