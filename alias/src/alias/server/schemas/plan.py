# -*- coding: utf-8 -*-
"""
计划（Roadmap）相关 schema（新手教学注释版）

这个文件目前很短：
- 只定义“获取路线图”接口的响应结构。
"""

from alias.server.models.plan import Roadmap

from .response import ResponseBase


class GetRoadmapResponse(ResponseBase):
    """获取路线图的响应模型。"""

    # payload 使用业务模型 Roadmap，里面包含计划树/步骤等信息。
    payload: Roadmap
