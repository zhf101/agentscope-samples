# `memory_service/memory_base/userprofiling_pool.py` 完全小白讲解

对应文件：`src/alias/memory_service/memory_base/userprofiling_pool.py`

这个类是“用户画像池”实现。

---

## 1) 主要增强点

1. 重写 `_prepare_metadata_for_add`
- 把 `is_confirmed` 标准化成 0/1

2. 提供两类抽取接口
- `get_user_info_memory`
- `get_user_event_memory`

---

## 2) 抽取方式

两者都走：
1. 预处理输入
2. 调 LLM（不同系统提示词）
3. 解析为字符串列表

---

## 3) 一句话总结

`userprofiling_pool.py` 负责把用户相关信息与事件转成可入库画像记忆。
