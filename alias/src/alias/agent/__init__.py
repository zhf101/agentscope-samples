# -*- coding: utf-8 -*-
"""
================================================================================
Agent 模块入口文件 - Python 子包结构
================================================================================

【什么是子包？】
在 Python 中，包可以嵌套包。alias 是一个包，agent 是 alias 的子包。
目录结构：
alias/                    <- 主包
├── __init__.py
├── agent/               <- 子包
│   ├── __init__.py     <- 你现在看到的文件
│   ├── agents/         <- 孙子包
│   ├── tools/
│   ├── mock/
│   └── utils/

【模块组织原则】
Python 项目通常按功能组织模块：
- agents/    : 存放各种 Agent 实现
- tools/     : 存放工具类
- mock/      : 存放模拟对象（用于测试）
- utils/     : 存放工具函数
"""

# ==============================================================================
# 导出列表
# ==============================================================================
# 定义当使用 `from alias.agent import *` 时导出的内容
# 这里导出四个子模块：
# - agents: 各种 Agent 的实现（如 MetaPlanner, BrowserAgent 等）
# - tools: 工具包（如 AliasToolkit）
# - mock: 模拟服务（如 MockSessionService）
# - utils: 工具函数和常量
__all__ = ["agents", "tools", "mock", "utils"]

# ==============================================================================
# 子模块导入
# ==============================================================================
# 这些导入让用户可以这样访问：
#   import alias.agent
#   alias.agent.agents.MetaPlanner  # 访问 agents 子包中的类
#   alias.agent.tools.AliasToolkit  # 访问 tools 子包中的类
#
# 【关于 noqa 注释】
# E402: 模块级导入不在文件顶部
# F401: 导入但未使用
# 这些是 Pylint 静态检查工具的规则编号，我们故意跳过这些检查
from . import agents  # noqa: E402, F401
from . import tools  # noqa: E402, F401
from . import mock  # noqa: E402, F401
from . import utils  # noqa: E402, F401