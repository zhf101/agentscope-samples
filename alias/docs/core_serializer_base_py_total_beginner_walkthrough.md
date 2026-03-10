# `core/serializer/base.py` 完全小白逐行讲解

对应文件：`src/alias/server/core/serializer/base.py`

这是序列化器的抽象接口定义文件。

---

## 1) 为什么要有抽象基类

统一规范所有序列化器都必须实现两个方法：
1. `serialize(obj)`
2. `deserialize(data, cls=None)`

这样上层代码可以“面向接口编程”，不依赖具体实现。

---

## 2) 关键语法

1. `ABC`：抽象基类
2. `@abstractmethod`：子类必须实现
3. `TypeVar("T")`：泛型类型变量

---

## 3) 一句话总结

`BaseSerializer` 是序列化体系的统一契约。
