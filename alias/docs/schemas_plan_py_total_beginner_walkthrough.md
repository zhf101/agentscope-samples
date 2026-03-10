# `schemas/plan.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/schemas/plan.py`

这个文件很短，作用是定义“路线图（Roadmap）查询响应”。

---

## 1) 第 1-9 行：导入

- `Roadmap`：计划领域模型（来自 `models/plan.py`）
- `ResponseBase`：统一响应外壳

---

## 2) 第 12-16 行：`GetRoadmapResponse`

```python
class GetRoadmapResponse(ResponseBase):
    payload: Roadmap
```

小白解释：
- 响应外层仍然有 `status / message / payload`
- 这里把 `payload` 明确成 `Roadmap` 类型

这样前后端都知道：这个接口返回的主体就是路线图数据。

---

## 3) 为什么这种写法好

1. 统一：所有接口都继承 `ResponseBase`
2. 明确：每个接口把 `payload` 精确到具体类型
3. 易维护：接口变更时类型提示更清晰

---

## 4) 一句话总结

`schemas/plan.py` 就是给“获取计划路线图”接口定义返回数据壳和 payload 类型。
