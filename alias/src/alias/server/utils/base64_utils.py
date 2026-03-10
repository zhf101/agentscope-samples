# -*- coding: utf-8 -*-
"""
Base64 图片校验工具（中文教学注释版）。

检查字符串是否是合法的 base64 图片，并限制大小。
参考 docs/utils_base64_utils_py_total_beginner_walkthrough.md。
"""

import base64
import re


def is_valid_base64_image(base64_string: str) -> bool:
    """
    校验 base64 图片字符串是否合法。

    规则：
    1) 必须以 data:image/(jpeg|png|gif);base64, 开头
    2) base64 解码后大小 <= 2MB
    """
    try:
        # 检查前缀格式
        if not re.match(r"^data:image\/(jpeg|png|gif);base64,", base64_string):
            return False

        # 取逗号后面的 base64 内容
        image_data = base64_string.split(",")[1]
        decoded_data = base64.b64decode(image_data)
        # 限制大小 2MB
        if len(decoded_data) > 2 * 1024 * 1024:
            return False

        return True
    except Exception:
        # 任意异常视为不合法
        return False
