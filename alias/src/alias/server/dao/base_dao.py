# -*- coding: utf-8 -*-
# pylint: disable=C0301 W0622
"""
DAO 基类（中文教学注释版）。

DAO = Data Access Object（数据访问层）。
职责非常明确：只和数据库打交道，不写业务逻辑。

参考 docs/base_dao_py_total_beginner_walkthrough.md：
- 本文件提供通用 CRUD、分页、条件查询能力；
- 子类只需要指定具体模型类型即可复用。
"""

import uuid
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from loguru import logger
from sqlmodel import SQLModel, asc, desc, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from alias.server.schemas.common import PaginationParams

# 泛型类型变量：表示“任意 SQLModel 子类”
ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseDAO(Generic[ModelType]):
    """Base data access object providing basic CRUD operations
    for database models.

    Responsibilities:
    - Execute database operations
    - Return database model instances
    - No business logic or validation
    """

    # 子类必须指定具体的 SQLModel 类，例如 User / Message
    _model_class: Type[ModelType]

    def __init__(self, session: AsyncSession):
        # 保存异步数据库会话
        self.session = session
        # model 指向具体模型类（由子类提供）
        self.model = self._model_class

    async def get(self, id: uuid.UUID) -> Optional[ModelType]:
        try:
            # 1) 构造 SQL：SELECT * FROM table WHERE id = :id
            statement = select(self.model).where(self.model.id == id)
            # 2) 执行 SQL
            result = await self.session.execute(statement)
            # 3) 取出一条或 None
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Error getting {self.model.__name__} with id {id}: "
                f"{str(e)}. ",
            )
            raise

    async def count_by_fields(
        self,
        filters: Dict[str, Any],
        patents: Optional[List] = None,
    ) -> int:
        try:
            # SELECT COUNT(*) FROM table
            query = select(func.count()).select_from(self.model)
            # 遍历 filters 动态拼接 WHERE 条件
            for field_name, value in filters.items():
                if hasattr(self.model, field_name):
                    query = query.where(
                        getattr(self.model, field_name) == value,
                    )
            # patents 额外过滤条件（类似 “附加 where”）
            if patents:
                for patent in patents:
                    query = query.filter(patent)
            result = await self.session.execute(query)
            return result.scalar()

        except Exception as e:
            logger.error(
                f"Error counting {self.model.__name__} with fields "
                f"{filters}: {str(e)}.",
            )
            raise

    async def get_first_by_fields(
        self,
        filters: Dict[str, Any],
    ) -> Optional[ModelType]:
        try:
            # 按多个字段查第一条
            query = select(self.model)
            for field_name, value in filters.items():
                if hasattr(self.model, field_name):
                    query = query.where(
                        getattr(self.model, field_name) == value,
                    )
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Error getting {self.model.__name__} by fields "
                f"{filters}: {str(e)}. ",
            )
            raise

    async def get_all_by_fields(
        self,
        filters: Dict[str, Any],
    ) -> List[ModelType]:
        try:
            # 按多个字段查所有
            query = select(self.model)
            for field_name, value in filters.items():
                if hasattr(self.model, field_name):
                    query = query.where(
                        getattr(self.model, field_name) == value,
                    )
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(
                f"Error getting {self.model.__name__} by fields "
                f"{filters}: {str(e)}. ",
            )
            raise

    async def get_first_by_field(
        self,
        field_name: str,
        value: Any,
    ) -> Optional[ModelType]:
        try:
            # 单字段查询第一条
            query = select(self.model).where(
                getattr(self.model, field_name) == value,
            )
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Error getting {self.model.__name__} by {field_name}: "
                f"{str(e)}. ",
            )
            raise

    async def get_all_by_field(
        self,
        field_name: str,
        value: Any,
    ) -> List[ModelType]:
        try:
            # 单字段查询所有
            query = select(self.model).where(
                getattr(self.model, field_name) == value,
            )
            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(
                f"Error getting {self.model.__name__} by {field_name}: "
                f"{str(e)}. ",
            )
            raise

    async def delete_all_by_field(
        self,
        field_name: str,
        value: Any,
    ) -> List[ModelType]:
        try:
            # 先查出所有匹配的对象，再逐个删除
            query = select(self.model).where(
                getattr(self.model, field_name) == value,
            )
            result = await self.session.execute(query)
            items = result.scalars().all()
            for item in items:
                await self.session.delete(item)
            await self.session.commit()
            return items
        except Exception as e:
            # 删除失败需要回滚事务
            await self.session.rollback()
            logger.error(
                f"Error deleting {self.model.__name__} by {field_name}: "
                f"{str(e)}. ",
            )
            raise

    async def paginate(
        self,
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[PaginationParams] = None,
        patents: Optional[List] = None,
    ) -> List[ModelType]:
        try:
            # 1) 基础查询：SELECT * FROM table
            query = select(self.model)

            if filters:
                # 2) 加过滤条件
                for attr, value in filters.items():
                    if hasattr(self.model, attr):
                        query = query.where(getattr(self.model, attr) == value)

            if patents:
                # 3) 加额外过滤条件
                for patent in patents:
                    query = query.filter(patent)

            if (
                pagination
                and pagination.order_by
                and hasattr(self.model, pagination.order_by)
            ):
                # 4) 排序
                order_column = getattr(self.model, pagination.order_by)
                query = query.order_by(
                    desc(order_column)
                    if pagination.order_direction == "desc"
                    else asc(order_column),
                )
            else:
                # 默认按创建时间升序
                query = query.order_by(self.model.create_time.asc())

            if pagination:
                # 5) 分页：offset + limit
                query = query.offset(pagination.skip).limit(pagination.limit)

            result = await self.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(
                f"Error getting multiple {self.model.__name__}: {str(e)}. ",
            )
            raise

    async def create(
        self,
        obj_data: Union[Dict[str, Any], ModelType],
    ) -> ModelType:
        try:
            # 允许传入 dict / Pydantic / SQLModel
            for method in ["model_dump", "dict", "to_dict"]:
                if hasattr(obj_data, method):
                    obj_data = getattr(obj_data, method)()
                    break
            # 组装模型对象并写入数据库
            db_obj = self.model(**obj_data)
            self.session.add(db_obj)
            await self.session.commit()
            await self.session.refresh(db_obj)
            return db_obj
        except Exception as e:
            # 出错回滚
            await self.session.rollback()
            logger.error(
                f"Error creating {self.model.__name__}: {str(e)}. ",
            )
            raise

    async def update(
        self,
        id: uuid.UUID,
        obj_data: Union[Dict[str, Any], ModelType],
    ) -> ModelType:
        try:
            # 先查出原对象
            db_obj = await self.get(id)
            if not db_obj:
                raise ValueError(
                    f"{self.model.__name__} with id {id} not found",
                )

            # obj_data 可能是 Pydantic/SQLModel，转 dict
            for method in ["model_dump", "dict", "to_dict"]:
                if hasattr(obj_data, method):
                    obj_data = getattr(obj_data, method)()
                    break
            # 逐字段更新
            for field, value in obj_data.items():
                if hasattr(db_obj, field):
                    for method in ["model_dump", "dict", "to_dict"]:
                        if hasattr(value, method):
                            value = getattr(value, method)()
                            break
                    setattr(db_obj, field, value)
                else:
                    raise ValueError(
                        f"Field {field} not found in {self.model.__name__}",
                    )

            await self.session.commit()
            await self.session.refresh(db_obj)
            return db_obj
        except Exception as e:
            # 出错回滚
            await self.session.rollback()
            logger.error(
                f"Error updating {self.model.__name__} with id {id}: "
                f"{str(e)}. ",
            )
            raise

    async def delete(self, id: uuid.UUID) -> bool:
        try:
            # 先查对象是否存在
            db_obj = await self.get(id)
            if not db_obj:
                return False
            await self.session.delete(db_obj)
            await self.session.commit()
            return True
        except Exception as e:
            # 出错回滚
            await self.session.rollback()
            logger.error(
                f"Error deleting {self.model.__name__} with id {id}: "
                f"{str(e)}. ",
            )
            raise

    async def exists(self, id: uuid.UUID) -> bool:
        try:
            # exists 只判断是否存在，不取完整对象
            statement = select(self.model).where(self.model.id == id)
            result = await self.session.execute(statement)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(
                f"Error checking existence of {self.model.__name__} "
                f"with id {id}: {str(e)}. ",
            )
            raise
