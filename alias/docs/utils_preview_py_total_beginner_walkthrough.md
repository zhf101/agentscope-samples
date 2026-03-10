# `utils/preview.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/utils/preview.py`

这个文件负责把文件内容转换成“可预览格式”。

---

## 1) `preview_file(file_path, file_ext, raw_data)`

输入：
- 文件路径
- 扩展名
- 原始字节数据

流程：
1. 猜测 MIME 类型
2. 用 chardet 猜编码并解码文本
3. 根据扩展名选择预览处理器
4. 返回 `(BytesIO流, media_type)`

---

## 2) 支持类型

内置处理：
- html
- md
- txt
- json
- csv
- xml
- yaml/yml
- log

不在支持列表：
- 直接返回原始字节 + 原媒体类型

