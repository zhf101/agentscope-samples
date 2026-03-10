# -*- coding: utf-8 -*-
"""
File DAO（中文教学注释版）。

作用：绑定 File 模型到 BaseDAO。
参考 docs/file_dao_py_total_beginner_walkthrough.md。
"""

from alias.server.dao.base_dao import BaseDAO
from alias.server.models.file import File


class FileDao(BaseDAO[File]):
    # 指定 DAO 对应的数据表模型
    _model_class = File
