# -*- coding: utf-8 -*-
"""
State（会话状态）服务（中文教学注释版）。

State 用来保存“对话过程中的中间状态”，例如：
- Agent 当前执行到哪一步；
- 一些可恢复的上下文数据。
"""

import uuid
from typing import List, Optional, Tuple, Union, Dict, Any

from loguru import logger

from alias.server.cache.state_cache import StateCache
from alias.server.dao.state_dao import StateDao
from alias.server.exceptions.service import StateNotFoundError
from alias.server.models.state import State
from alias.server.schemas.common import PaginationParams
from alias.server.services.base_service import BaseService
from alias.server.utils.timestamp import get_current_time


class StateService(BaseService[State]):
    _model_cls = State
    _dao_cls = StateDao
    _cache_cls = StateCache

    async def _validate_exists(self, instance_id: uuid.UUID) -> None:
        # 校验 state 是否存在
        state = await self.get(instance_id)
        if not state:
            raise StateNotFoundError(extra_info={"state_id": instance_id})

    async def _validate_update(
        self,
        instance_id: uuid.UUID,
        obj_in: Union[Dict[str, Any], State],
    ) -> None:
        # 更新前校验
        state = await self.get(instance_id)
        if not state:
            raise StateNotFoundError(extra_info={"state_id": instance_id})

    async def _validate_delete(self, instance_id: uuid.UUID) -> None:
        # 删除前校验
        state = await self.get(instance_id)
        if not state:
            raise StateNotFoundError(extra_info={"state_id": instance_id})

    async def list_states(
        self,
        user_id: uuid.UUID,
        pagination: Optional[PaginationParams] = None,
    ) -> Tuple[int, List[State]]:
        # 分页列出用户的 state
        filters = {"user_id": user_id}
        total = await self.count_by_fields(filters=filters)
        states = await self.paginate(
            pagination=pagination,
            filters=filters,
        )
        return total, states

    async def create_state(
        self,
        conversation_id: uuid.UUID,
        content: str,
    ) -> State:
        # 如果已有 state，则走“更新”
        state = await self.get_state(conversation_id)
        if state:
            logger.info(
                f"Created state through update state: {conversation_id}",
            )
            return await self.update_state(
                conversation_id=conversation_id,
                content=content,
            )

        # 新建 state 记录
        state = State(
            conversation_id=conversation_id,
            content=content,
        )
        state = await self.create(state)
        await self.set_cache(conversation_id, state)
        logger.info(f"Created state: {state.id}")
        return state

    async def get_state(self, conversation_id: uuid.UUID) -> Optional[State]:
        # 先查缓存，再查库
        state = await self.get_cache(conversation_id)
        if not state:
            state = await self.get_last_by_field(
                "conversation_id",
                conversation_id,
            )
            if state:
                await self.set_cache(conversation_id, state)
        return state

    async def update_state(
        self,
        conversation_id: uuid.UUID,
        content: str,
    ) -> State:
        # 更新 state 内容
        state = await self.get_state(conversation_id)
        if not state:
            raise StateNotFoundError(
                extra_info={"conversation_id": conversation_id},
            )
        state.content = content
        state.update_time = get_current_time()
        await self.set_cache(conversation_id, state)
        return await self.update(state.id, state)

    async def delete_state(self, conversation_id: uuid.UUID) -> None:
        # 删除会话对应的 state
        state = await self.get_state(conversation_id=conversation_id)
        if state:
            await self.delete(state.id)
            await self.clear_cache(conversation_id)
