# `utils/timestamp.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/utils/timestamp.py`

这个文件提供一个统一时间函数。

---

## 1) `get_current_time()`

返回：
- 当前 UTC 时间的 ISO 字符串

等价逻辑：
- `datetime.now(timezone.utc).isoformat()`

用途：
- 更新 `update_time`
- 记录登录时间等

