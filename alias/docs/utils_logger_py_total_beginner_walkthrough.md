# `utils/logger.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/utils/logger.py`

这个文件配置 Loguru 日志系统，并把请求上下文注入日志。

---

## 1) `ensure_log_directory(log_file)`

作用：
- 确保日志目录存在，不存在就创建。

---

## 2) `setup_logger()`

主要步骤：
1. 读取配置（日志路径、格式、级别、轮转、保留）
2. 定义 `request_context_filter(record)`：
   - 从 `request_context_var` 拿请求上下文
   - 注入到日志 `extra`
   - 把额外字段整理到 `context`
3. `logger.remove()` 清空旧 handler
4. `logger.add(sys.stdout, ...)` 添加控制台输出
5. `logger.add(log_file, ...)` 添加文件输出

---

## 3) 关键价值

日志里会自动带：
- request_id
- user_id
- ip 等上下文信息

这样排查问题时可以按请求链路追踪。

