# -*- coding: utf-8 -*-
"""
消息相关 schema（新手教学注释版）

这个文件定义：
1) 消息信息结构
2) 消息分页返回结构
3) 消息更新请求结构（点赞/点踩/收藏）
"""

import uuid
from typing import List, Optional

from fastapi.encoders import jsonable_encoder
from sqlmodel import Field, SQLModel

from alias.server.models.action import FeedbackType
from alias.server.models.message import DetailedMessageBase

from .response import ResponseBase


class MessageInfo(DetailedMessageBase):
    """返回给前端的消息详情模型。"""

    id: uuid.UUID

    def model_dump(self) -> dict:
        # 先按 Pydantic/SQLModel 规则导出为 Python 字典。
        data = super().model_dump()
        # 再做一次 JSON 兼容转换（如 UUID、时间类型等）。
        data = jsonable_encoder(data)
        return data


class GetMessageResponse(ResponseBase):
    """单条消息查询响应。"""

    payload: MessageInfo


class PageMessageInfo(SQLModel):
    """消息分页数据结构：总数 + 列表。"""

    total: int
    items: List[MessageInfo]


class ListMessagesResponse(ResponseBase):
    """消息列表查询响应。"""

    payload: PageMessageInfo


class UpdateMessageRequest(SQLModel):
    """更新消息附加状态（反馈/收藏）的请求体。"""

    # 反馈类型：like / dislike / None
    feedback: Optional[FeedbackType] = Field(
        default=None,
        description="Feedback can be 'like', 'dislike', or None",
    )
    # 是否收藏，默认 False。
    collect: Optional[bool] = False


class UpdateMessageResponse(ResponseBase):
    """更新消息后的响应。"""

    payload: MessageInfo
