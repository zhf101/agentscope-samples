# -*- coding: utf-8 -*-
# pylint: disable=C0301 W0622
"""
通用 Service 基类（中文教学注释版）。

这层属于“业务服务层（Service Layer）”：
- 上接 API/路由（Controller），下接 DAO/数据库；
- 负责把“业务规则 + 数据访问 + 缓存”组合起来；
- 统一异常日志和缓存策略，避免各业务 Service 重复造轮子。

理解这层很重要，因为几乎所有业务 Service 都继承它。
"""

import traceback
import uuid
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from loguru import logger
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel

from alias.server.cache.base_cache import BaseCache
from alias.server.dao.base_dao import BaseDAO
from alias.server.schemas.common import PaginationParams

# TypeVar 是“类型变量”，用于泛型类。
# 这里表示：BaseService 可以服务于任意 SQLModel 子类（比如 User、Message 等）。
ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseService(Generic[ModelType]):
    """
    所有业务 Service 的父类。

    三个核心组件：
    1) DAO：真正访问数据库
    2) Cache：可选缓存层（加速读）
    3) Session：数据库会话（事务控制）
    """

    # 子类需要指定对应的 Model / DAO / Cache
    _model_cls: Type[ModelType]
    _dao_cls: Type[BaseDAO[ModelType]]
    _cache_cls: Optional[Type[BaseCache[ModelType]]] = None

    def __init__(self, session: AsyncSession):
        # 初始化 DAO（负责数据库 CRUD）
        self.dao = self._dao_cls(session=session)
        # 如果子类提供了 Cache，就实例化；否则为 None
        self.cache = (
            self._cache_cls()  # pylint: disable=E1102
            if self._cache_cls
            else None
        )
        # 保存会话，便于子类按需使用
        self.session = session

    # ======================================================================
    # 缓存相关方法（Cache）
    # ======================================================================
    async def set_cache(
        self,
        key: Union[str, uuid.UUID],
        value: ModelType,
    ) -> bool:
        # 如果没有 cache，直接返回 True 表示“缓存写入视为成功”
        return await self.cache.set_cache(key, value) if self.cache else True

    async def get_cache(
        self,
        key: Union[str, uuid.UUID],
    ) -> Optional[ModelType]:
        # 没有 cache 时返回 None，表示“缓存未命中”
        return await self.cache.get_cache(key) if self.cache else None

    async def clear_cache(self, key: Union[str, uuid.UUID]) -> None:
        # 清理缓存（如果存在）
        if self.cache:
            await self.cache.clear_cache(key)

    # ======================================================================
    # DAO 相关方法（数据库 CRUD）
    # ======================================================================
    async def get(self, id: uuid.UUID) -> Optional[ModelType]:
        try:
            # 先尝试从缓存获取
            cached_item = await self.get_cache(id)
            if cached_item:
                return cached_item
            # 缓存未命中，去数据库读
            item = await self.dao.get(id)
            if item:
                # 数据库命中后写入缓存
                await self.set_cache(id, item)
            return item
        except Exception as e:
            logger.error(
                f"Service error getting entity with id {id}: {str(e)}, "
                f"\n traceback: {traceback.format_exc()}",
            )
            raise

    async def create(
        self,
        obj_in: Union[Dict[str, Any], ModelType],
    ) -> ModelType:
        try:
            # DAO 执行插入
            item = await self.dao.create(obj_in)
            # 写入缓存，避免后续读库
            await self.set_cache(item.id, item)
            return item
        except Exception as e:
            logger.error(
                f"Service error creating entity: {obj_in}, error: {str(e)}, "
                f"\n traceback: {traceback.format_exc()}",
            )
            raise

    async def update(
        self,
        id: uuid.UUID,
        obj_in: Union[Dict[str, Any], ModelType],
    ) -> ModelType:
        try:
            # 先做业务级校验（子类可重写）
            await self._validate_update(id, obj_in)
            item = await self.dao.update(
                id,
                obj_in,
            )
            # 更新缓存
            await self.set_cache(id, item)
            return item
        except Exception as e:
            logger.error(
                f"Service error updating entity with id {id}: {str(e)}, "
                f"\n traceback: {traceback.format_exc()}",
            )
            raise

    async def delete(self, id: uuid.UUID) -> bool:
        try:
            # 删除前校验（子类可重写）
            await self._validate_delete(id)
            result = await self.dao.delete(id)
            if result:
                # 删除成功则清缓存
                await self.clear_cache(id)
            return result
        except Exception as e:
            logger.error(
                f"Service error deleting entity with id {id}: {str(e)}, "
                f"\n traceback: {traceback.format_exc()}",
            )
            raise

    async def count_by_fields(
        self,
        filters: Dict[str, Any],
        patents: Optional[List] = None,
    ) -> int:
        try:
            # 统计满足 filters 条件的记录数
            return await self.dao.count_by_fields(
                filters=filters,
                patents=patents,
            )
        except Exception as e:
            logger.error(
                f"Service error counting entities by {filters}: {str(e)}, "
                f"\n traceback: {traceback.format_exc()}",
            )
            raise

    async def paginate(
        self,
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[PaginationParams] = None,
        patents: Optional[List] = None,
    ) -> List[ModelType]:
        try:
            # 分页查询
            return await self.dao.paginate(
                filters=filters,
                pagination=pagination,
                patents=patents,
            )
        except Exception as e:
            logger.error(
                f"Service error getting multiple entities: {str(e)}, "
                f"\n traceback: {traceback.format_exc()}",
            )
            raise

    async def get_last_by_fields(
        self,
        filters: Dict[str, Any],
    ) -> Optional[ModelType]:
        try:
            # 取满足条件的所有记录，返回最后一条
            items = await self.dao.get_all_by_fields(filters)
            if len(items) > 0:
                return items[-1]
            return None
        except Exception as e:
            logger.error(
                f"Service error getting last entity by fields {filters}: "
                f"{str(e)}, \n traceback: {traceback.format_exc()}",
            )
            raise

    async def get_all_by_fields(
        self,
        filters: Dict[str, Any],
    ) -> List[ModelType]:
        try:
            # 获取满足 filters 的所有记录
            return await self.dao.get_all_by_fields(filters)
        except Exception as e:
            logger.error(
                f"Service error getting entities by fields {filters}: "
                f"{str(e)}, \n traceback: {traceback.format_exc()}",
            )
            raise

    async def get_first_by_field(
        self,
        field_name: str,
        value: Any,
    ) -> Optional[ModelType]:
        try:
            # 取某字段等于 value 的第一条记录
            return await self.dao.get_first_by_field(field_name, value)
        except Exception as e:
            logger.error(
                f"Service error getting entity by {field_name}: {str(e)}, "
                f"\n traceback: {traceback.format_exc()}",
            )
            raise

    async def get_last_by_field(
        self,
        field_name: str,
        value: Any,
    ) -> Optional[ModelType]:
        try:
            # 获取某字段等于 value 的最后一条记录
            values = await self.dao.get_all_by_field(field_name, value)
            if len(values) > 0:
                return values[-1]
            return None
        except Exception as e:
            logger.error(
                f"Service error getting last entity by {field_name}: "
                f"{str(e)}, \n traceback: {traceback.format_exc()}",
            )
            raise

    async def get_all_by_field(
        self,
        field_name: str,
        value: Any,
    ) -> List[ModelType]:
        try:
            # 获取某字段等于 value 的所有记录
            return await self.dao.get_all_by_field(field_name, value)
        except Exception as e:
            logger.error(
                f"Service error getting entities by {field_name}: "
                f"{str(e)}, \n traceback: {traceback.format_exc()}",
            )
            raise

    async def delete_all_by_field(
        self,
        field_name: str,
        value: Any,
    ) -> List[ModelType]:
        try:
            # 删除某字段等于 value 的所有记录
            return await self.dao.delete_all_by_field(field_name, value)
        except Exception as e:
            logger.error(
                f"Service error deleting entities by {field_name}: "
                f"{str(e)}, \n traceback: {traceback.format_exc()}",
            )
            raise

    async def _validate_create(
        self,
        obj_in: Union[Dict[str, Any], ModelType],
    ) -> None:
        # 子类可重写：创建前校验（默认不做任何校验）
        pass

    async def _validate_update(
        self,
        instance_id: uuid.UUID,
        obj_in: Union[Dict[str, Any], ModelType],
    ) -> None:
        # 子类可重写：更新前校验
        pass

    async def _validate_delete(self, instance_id: uuid.UUID) -> None:
        # 子类可重写：删除前校验
        pass

    async def _validate_exists(self, instance_id: uuid.UUID) -> None:
        # 子类可重写：通用存在性校验
        pass
