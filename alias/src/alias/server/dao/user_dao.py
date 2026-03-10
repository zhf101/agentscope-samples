# -*- coding: utf-8 -*-
"""
User DAO（中文教学注释版）。

在 BaseDAO 基础上扩展了“更新最后登录信息”的方法。
参考 docs/user_dao_py_total_beginner_walkthrough.md。
"""

import uuid

from alias.server.dao.base_dao import BaseDAO
from alias.server.models.user import User
from alias.server.utils.request_context import request_context_var
from alias.server.utils.timestamp import get_current_time


class UserDao(BaseDAO[User]):
    # 绑定 User 模型
    _model_class = User

    async def update_last_login_info(
        self,
        user_id: uuid.UUID,
    ) -> User:
        """Update the last login info of the user."""
        # 1) 读取用户对象（如果不存在 BaseDAO 会返回 None）
        user = await self.get(user_id)
        # 2) 从请求上下文拿到客户端 IP
        ip_address = request_context_var.get().ip_address
        # 3) 组装更新字典（只更新需要的字段）
        update_data = {}
        if ip_address:
            update_data["last_login_ip"] = ip_address
        update_data["last_login_time"] = get_current_time()
        # 4) 调 BaseDAO.update 写库
        user = await self.update(user_id, update_data)
        return user
