# `utils/style.py` 完全小白逐行讲解

对应文件：`src/alias/server/utils/style.py`

这个文件负责“内容预览页面”的样式和渲染辅助。

---

## 1) 提供了什么

1. `COMMON_CSS`
- 一套通用页面样式（标题、代码块、表格等）

2. `get_pygments_css(style)`
- 获取语法高亮 CSS

3. `highlight_code(content, lexer_name, style)`
- 对代码做高亮，失败时回退 `<pre>`

4. `create_html_preview(title, content, extra_css)`
- 组装完整 HTML 页面

5. `render_markdown(md_content)`
- markdown -> HTML

6. `render_csv_to_html(csv_content)`
- CSV 文本 -> HTML 表格

7. `sanitize_html(html_content)`
- 当前仅占位，尚未真正做安全净化

---

## 2) 风险点

`sanitize_html` 目前没有真正防 XSS，后续应补安全过滤。

---

## 3) 一句话总结

`utils/style.py` 是内容可视化预览的渲染工具集合。
