# `clients/base_client.py` 完全小白逐行讲解

对应文件：`src/alias/server/clients/base_client.py`

这是所有 HTTP 客户端的基类。

---

## 1) 核心职责

1. 组装完整 URL（`base_url + path`）
2. 序列化请求体（支持 `str`/`dict`/`BaseModel`）
3. 统一发送请求
4. 把网络异常转换成 `ServiceError`

---

## 2) `_prepare_data` 规则

- `None` -> `None`
- `str` -> 原样返回
- `BaseModel` -> `.json()`
- `dict` -> `json.dumps`

其它类型会抛 `ValueError`。

---

## 3) `_request` 异常处理

1. `httpx.TimeoutException`：请求超时
2. `httpx.RequestError`：网络请求失败
3. 其它异常：统一包成 `ServiceError`

这样上层代码不用关心底层网络异常细节。

---

## 4) 一句话总结

`BaseClient` 是“发 HTTP 请求的公共底座”，让业务 client 只关心路径和参数。
