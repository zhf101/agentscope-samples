# -*- coding: utf-8 -*-
"""
Plan（计划）服务（中文教学注释版）。

Plan/ Roadmap 的用途：
- 记录一次对话的“计划结构”；
- 前端可视化展示；
- 允许用户编辑并追踪历史变化。
"""

import uuid
from typing import Any, Dict, Optional, Union

from loguru import logger

from alias.server.cache.plan_cache import PlanCache
from alias.server.dao.plan_dao import PlanDao
from alias.server.exceptions.service import PlanNotFoundError
from alias.server.models.plan import Plan, Roadmap
from alias.server.services.base_service import BaseService
from alias.server.utils.timestamp import get_current_time


class PlanService(BaseService[Plan]):
    _model_cls = Plan
    _dao_cls = PlanDao
    _cache_cls = PlanCache

    async def _validate_exists(self, instance_id: uuid.UUID) -> None:
        # 校验 plan 是否存在
        plan = await self.get(instance_id)
        if not plan:
            raise PlanNotFoundError(extra_info={"plan_id": instance_id})

    async def _validate_update(
        self,
        instance_id: uuid.UUID,
        obj_in: Union[Dict[str, Any], Plan],
    ) -> None:
        # 更新前校验
        plan = await self.get(instance_id)
        if not plan:
            raise PlanNotFoundError(extra_info={"plan_id": instance_id})

    async def _validate_delete(self, instance_id: uuid.UUID) -> None:
        # 删除前校验
        plan = await self.get(instance_id)
        if not plan:
            raise PlanNotFoundError(extra_info={"plan_id": instance_id})

    async def create_plan(
        self,
        conversation_id: uuid.UUID,
        content: Dict[str, Any],
    ) -> Plan:
        # 如果已有 plan，则改为“更新”
        plan = await self.get_plan(conversation_id)
        if plan:
            logger.info(
                f"Created plan through update plan: {conversation_id}",
            )
            return await self.update_plan(
                conversation_id=conversation_id,
                content=content,
            )

        # 新建 Plan 记录
        plan = Plan(
            conversation_id=conversation_id,
            content=content,
        )
        plan = await self.create(plan)
        await self.set_cache(conversation_id, plan)
        logger.info(f"Created plan: {plan.id}")
        return plan

    async def get_plan(self, conversation_id: uuid.UUID) -> Optional[Plan]:
        # 先查缓存，缓存没有再查库
        plan = await self.get_cache(conversation_id)
        if not plan:
            plan = await self.get_last_by_field(
                "conversation_id",
                conversation_id,
            )
            if plan:
                await self.set_cache(conversation_id, plan)
        return plan

    async def update_plan(
        self,
        conversation_id: uuid.UUID,
        content: Dict[str, Any],
    ) -> Plan:
        # 更新 plan 内容
        plan = await self.get_plan(conversation_id)
        if not plan:
            raise PlanNotFoundError(
                extra_info={"conversation_id": conversation_id},
            )
        plan.content = content
        plan.update_time = get_current_time()
        plan = await self.update(plan.id, plan)
        await self.set_cache(conversation_id, plan)
        return plan

    async def delete_plan(self, conversation_id: uuid.UUID) -> None:
        # 删除 conversation 对应的 plan
        plan = await self.get_plan(conversation_id=conversation_id)
        if plan:
            await self.delete(plan.id)
            await self.clear_cache(conversation_id)

    async def get_roadmap(self, conversation_id: uuid.UUID) -> Roadmap:
        # 没有 plan 时返回空 Roadmap
        plan = await self.get_plan(conversation_id)
        if not plan:
            return Roadmap()
        return plan.roadmap

    async def update_roadmap(
        self,
        conversation_id: uuid.UUID,
        roadmap: Roadmap,
    ) -> Plan:
        # Roadmap 是 Plan.content 的一种结构化视图
        plan = await self.create_plan(
            conversation_id=conversation_id,
            content=roadmap.model_dump(),
        )
        return plan.roadmap
