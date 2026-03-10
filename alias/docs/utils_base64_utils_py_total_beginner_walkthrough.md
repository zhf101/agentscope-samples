# `utils/base64_utils.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/utils/base64_utils.py`

这个文件只有一个函数：校验 base64 图片字符串是否合法。

---

## 1) `is_valid_base64_image(base64_string)`

校验步骤：
1. 必须匹配前缀：`data:image/(jpeg|png|gif);base64,`
2. 取逗号后面的 base64 内容并解码
3. 图片大小不能超过 2MB
4. 全部通过返回 `True`，否则 `False`

异常处理：
- 任意异常都返回 `False`

