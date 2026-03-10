#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=R0912
"""
================================================================================
Alias 命令行接口 (CLI) - 从零开始学习命令行工具开发
================================================================================

【什么是 CLI？】
CLI = Command Line Interface（命令行界面）
它是一种通过文本命令与程序交互的方式，而不是通过鼠标点击图形界面。

【本文件的作用】
这个文件是 Alias 项目的主入口点，当你执行：
    alias run --task "帮我分析数据"
    
Python 就会运行这个文件中的 main() 函数。

【学习路线图】
1. 导入模块 - 了解 Python 如何引入外部代码
2. 全局变量 - 理解模块级别的变量
3. 智能路由 - 学习正则表达式和决策逻辑
4. 异步编程 - 理解 async/await 关键字
5. 信号处理 - 学习如何优雅地处理中断
6. 命令行解析 - 掌握 argparse 库的使用
"""

# ==============================================================================
# 第一部分：导入模块 (Import Statements)
# ==============================================================================
# 【Python 导入机制详解】
# 当你写 `import xxx` 时，Python 会：
# 1. 在 sys.path（搜索路径列表）中查找 xxx 模块
# 2. 找到后执行该模块的代码
# 3. 将模块中的名字绑定到当前命名空间

# ------------------------------------------------------------------------------
# 标准库导入（Python 自带的库）
# ------------------------------------------------------------------------------
import argparse  # 命令行参数解析库
# 【argparse 是什么？】
# 它帮你解析命令行参数，比如：
#   python script.py --name "张三" --age 25
# argparse 会自动解析出 name="张三", age=25
# 还会自动生成帮助信息（--help）

import asyncio  # 异步编程支持库
# 【asyncio 是什么？】
# Python 的异步编程框架，用于处理 I/O 密集型任务
# 例如：同时处理多个网络请求，而不需要等待每个请求完成
# 核心：事件循环（Event Loop）+ 协程（Coroutine）

import signal  # 信号处理库
# 【signal 是什么？】
# 用于处理操作系统发送的信号，比如：
# - Ctrl+C 会发送 SIGINT 信号
# - kill 命令会发送 SIGTERM 信号
# 你可以"捕获"这些信号并执行自定义代码

import sys  # 系统相关功能
# 【sys 常用功能】
# - sys.argv：命令行参数列表
# - sys.exit()：退出程序
# - sys.path：模块搜索路径
# - sys.stdin/stdout/stderr：标准输入输出

import traceback  # 错误追踪
# 【traceback 是什么？】
# 当程序出错时，打印详细的错误堆栈信息
# 帮助开发者定位问题所在

import webbrowser  # 网页浏览器控制
# 【webbrowser 是什么？】
# 可以在代码中打开浏览器
# 例如：webbrowser.open("https://www.baidu.com")

import re  # 正则表达式库
# 【正则表达式是什么？】
# 一种用于匹配文本模式的强大工具
# 例如：r"\d+" 可以匹配一个或多个数字

# ------------------------------------------------------------------------------
# 第三方库导入
# ------------------------------------------------------------------------------
from loguru import logger  # 日志库
# 【loguru 是什么？】
# 一个更好用的日志库，比 Python 自带的 logging 模块更简洁
# 使用方法：
#   logger.info("普通信息")
#   logger.warning("警告信息")
#   logger.error("错误信息")
#   logger.debug("调试信息")

# ------------------------------------------------------------------------------
# AgentScope 框架导入
# ------------------------------------------------------------------------------
from agentscope.agent import TerminalUserInput, UserAgent
from agentscope.message import Msg

# 【AgentScope 是什么？】
# AgentScope 是阿里巴巴开源的 AI Agent 框架
# - UserAgent：模拟用户输入的 Agent
# - TerminalUserInput：终端输入处理器
# - Msg：消息对象，用于 Agent 之间通信

# ------------------------------------------------------------------------------
# 项目内部模块导入
# ------------------------------------------------------------------------------
from alias.agent.mock import MockSessionService, UserMessage
# Mock = "模拟"，用于测试或简化场景
# MockSessionService：模拟的会话服务，不需要真实的后端服务器
# UserMessage：用户消息的数据结构

from alias.agent.run import (
    arun_meta_planner,      # 运行元规划器 Agent（通用型）
    arun_browseruse_agent,  # 运行浏览器 Agent
    MODEL_FORMATTER_MAPPING, # 模型配置映射
    MODEL_CONFIG_NAME,       # 当前使用的模型配置名
)
# 【这些函数是什么？】
# 每个 arun_xxx 函数都是启动对应 Agent 的入口
# "a" 前缀表示这是异步函数（async function）

from alias.agent.utils.prepare_data_source import (
    get_data_source_config_from_file,
)
# 从配置文件读取数据源设置

from alias.runtime.alias_sandbox.alias_sandbox import AliasSandbox
# Sandbox = "沙盒"，一个隔离的执行环境
# AliasSandbox 提供了一个安全的代码运行环境


# ==============================================================================
# 第二部分：全局变量 (Global Variables)
# ==============================================================================
# 【什么是全局变量？】
# 在模块级别定义的变量，可以在整个模块中访问
# 全局变量在模块加载时创建，在模块卸载时销毁

# 保存原始的信号处理器
# 【为什么要保存原始处理器？】
# 当我们要修改信号处理行为时，最好保存原来的处理器
# 这样在程序结束时可以恢复，避免影响其他代码
_original_sigint_handler = None


# ==============================================================================
# 第三部分：智能路由 - 关键词定义
# ==============================================================================
# 【什么是"智能路由"？】
# 根据用户输入的内容，自动判断应该使用哪种 Agent 来处理任务
# 就像一个智能客服，能判断你的问题应该转给哪个部门

# 【正则表达式基础语法】
# r"..." 中的 r 表示"原始字符串"，不转义反斜杠
# |      表示"或"
# .*?    表示"任意字符，非贪婪匹配"
# \.     表示真正的点号（. 在正则中有特殊含义，需要转义）

# ------------------------------------------------------------------------------
# 浏览器相关关键词
# ------------------------------------------------------------------------------
BROWSER_KEYWORDS = [
    # 【中文关键词】
    # | 是"或"的意思，比如 r"浏览|打开|访问" 可以匹配"浏览"或"打开"或"访问"
    r"浏览|打开|访问|登录|注册|网站|网页",
    
    # 【英文关键词】
    # .*? 表示"任意数量的任意字符，但尽可能少匹配"（非贪婪）
    # sign.*?up 可以匹配 "sign up", "sign-up", "sign   up" 等
    r"browse|open|visit|login|sign.*?up|website|webpage",
    
    # 【交互动作】
    r"click|点击|填写|填表|submit|提交",
    
    # 【电商与预订】
    # 这些关键词如果出现，很可能是要做网上购物或订票
    r"购物|下单|预订|购买|买票|订票|机票|酒店|火车票",
    r"shop|buy|order|book|ticket|hotel|flight|train",
    
    # 【常见电商平台】
    # 如果用户提到这些平台名，几乎肯定要用浏览器
    r"amazon|taobao|jd|淘宝|京东|携程|trip|airbnb",
    
    # 【网页相关表述】
    # 在.*?网上 = "在网上"、"在官网上"等
    r"在.*?网上|从.*?网站|官网",
    r"on.*?website|from.*?site",
    
    # 【社交媒体】
    r"twitter|facebook|instagram|linkedin|微博|抖音|小红书",
]


# ==============================================================================
# 第四部分：智能路由函数
# ==============================================================================
def smart_route(user_msg: str, user_data: list = None) -> str:
    """
    根据用户消息内容，智能选择最合适的 Agent 模式。
    
    【什么是"路由"？】
    路由（Routing）是指将请求分发到不同处理器的过程。
    就像快递分拣中心，根据目的地把包裹分发到不同的运输线路。
    
    【参数说明】
    Args:
        user_msg: 用户输入的任务/问题（字符串类型）
        user_data: 可选的数据源列表（比如用户上传的文件）
    
    【返回值说明】
    Returns:
        推荐的模式字符串：
        - 'general'  : 通用模式，使用元规划器处理复杂任务
        - 'browser'  : 浏览器模式，用于网页操作任务
    
    【评分机制】
    我们为每个模式设置一个分数，根据匹配的关键词增加分数，
    最后选择分数最高的模式。
    """
    # 将用户消息转为小写，便于匹配（不区分大小写）
    msg_lower = user_msg.lower()
    
    # 初始化各模式的分数
    # 【为什么要给 general 基础分？】
    # 如果其他模式都没有匹配，就使用 general 模式
    # 这是一种"默认兜底"策略
    scores = {
        "browser": 0,   # 浏览器模式
        "general": 1,   # 通用模式（默认有1分基础分）
    }
    
    # -------------------------------------------------------------------------
    # 关键词匹配评分
    # -------------------------------------------------------------------------
    # 【for 循环的工作原理】
    # 遍历每个关键词模式，如果在用户消息中找到匹配，就加分
    
    # 检查浏览器关键词
    for pattern in BROWSER_KEYWORDS:
        # re.search() 在字符串中搜索匹配正则表达式的位置
        # re.IGNORECASE 表示忽略大小写
        if re.search(pattern, msg_lower, re.IGNORECASE):
            scores["browser"] += 2  # 每匹配一个关键词加2分
    
    # -------------------------------------------------------------------------
    # 特殊情况处理
    # -------------------------------------------------------------------------
    # 如果浏览器模式得分很高（>=4），说明这确实是一个浏览器任务
    # 此时应该把 general 的分数设为0，避免被错误路由到通用模式
    if scores["browser"] >= 4:
        scores["general"] = 0
    
    # 记录路由决策日志
    logger.info(f"Smart routing scores: {scores}")
    
    # -------------------------------------------------------------------------
    # 选择最佳模式
    # -------------------------------------------------------------------------
    # max(scores, key=scores.get) 获取分数最高的模式名
    # 【工作原理】
    # 1. scores 是字典，max() 会遍历所有的键
    # 2. key=scores.get 表示用字典的值（分数）来比较
    # 3. 返回分数最高的键（模式名）
    best_mode = max(scores, key=scores.get)
    logger.info(f"Selected mode: {best_mode}")
    
    return best_mode


async def route_with_llm(
    user_msg: str,
    user_data: list = None,
) -> str:
    """
    使用 LLM（大语言模型）进行更智能的路由决策。
    
    【什么是 LLM 路由？】
    前面的 smart_route 使用关键词匹配，比较机械。
    这个函数会调用大语言模型（如 GPT），让 AI 理解用户意图并做出决策。
    
    【async 是什么？】
    async 是 Python 的异步编程关键字。
    调用 LLM API 需要等待网络响应，使用异步可以在等待时做其他事情。
    
    【为什么需要两个路由函数？】
    1. smart_route：简单快速，但可能不准确
    2. route_with_llm：更智能，但需要调用 API（有延迟和费用）
    
    实际使用时，先用 smart_route，如果不确定再用 LLM。
    """
    # 首先用关键词路由快速判断
    initial_mode = smart_route(user_msg, user_data)
    
    # 如果关键词路由已经很确定（不是 general），直接返回
    # 【为什么 general 要进一步判断？】
    # general 是"兜底"模式，当关键词无法匹配时使用
    # 这时用 LLM 可以更准确地判断用户意图
    if initial_mode != "general":
        return initial_mode
    
    # -------------------------------------------------------------------------
    # 使用 LLM 进行路由
    # -------------------------------------------------------------------------
    try:
        # 获取模型配置
        model, _ = MODEL_FORMATTER_MAPPING.get(MODEL_CONFIG_NAME, (None, None))
        if model is None:
            return "general"  # 如果没有配置模型，返回通用模式
        
        # 构造提示词（Prompt）
        # 【提示词工程】
        # 给 AI 的指令要清晰、具体：
        # 1. 说明 AI 的角色（任务路由器）
        # 2. 列出所有可选模式及其用途
        # 3. 提供用户的具体请求
        # 4. 指定输出格式（只返回模式名）
        router_prompt = f"""You are a task router. Analyze the user's request and select the best agent mode.

Available modes:
1. **browser**: For tasks requiring web browsing, clicking, form filling, booking, shopping, or interacting with websites
2. **general**: For general tasks that can be handled by a meta-planner with multiple workers

User request: {user_msg}

Data sources: {user_data if user_data else "None"}

Reply with ONLY the mode name (browser/general), nothing else."""
        
        # 调用模型获取响应
        # 【Msg 对象】
        # AgentScope 使用 Msg 对象来封装消息
        # 参数：角色名、内容、角色类型
        response = await model([Msg("user", router_prompt, "user")])
        
        # 提取响应文本并清理
        mode = response.content[0]["text"].strip().lower()
        
        # 验证返回的模式是否有效
        if mode in ["browser", "general"]:
            logger.info(f"LLM router selected mode: {mode}")
            return mode
        
    except Exception as e:
        # 如果 LLM 调用失败，回退到关键词路由结果
        # 【异常处理最佳实践】
        # 在关键路径上，总是要有备用方案
        logger.warning(f"LLM routing failed: {e}, using keyword-based result")
    
    return initial_mode


# ==============================================================================
# 第五部分：信号处理
# ==============================================================================
def _safe_sigint_handler(signum, frame):  # pylint: disable=W0613
    """
    自定义的 SIGINT 信号处理器，用于安全地处理 Ctrl+C 中断。
    
    【什么是 SIGINT？】
    SIGINT = Signal Interrupt（中断信号）
    当用户按下 Ctrl+C 时，操作系统会向程序发送这个信号。
    
    默认行为是立即终止程序，但我们可以自定义处理逻辑。
    
    【为什么需要自定义信号处理器？】
    1. 默认处理器会立即终止程序，可能导致资源泄漏
    2. 我们需要在退出前清理 Sandbox（沙盒环境）
    3. 我们需要优雅地取消正在运行的任务
    
    【参数说明】
    Args:
        signum: 信号编号（SIGINT 通常是 2）
        frame: 当前栈帧（包含程序执行位置信息）
        # pylint: disable=W0613 表示我们故意不使用这两个参数
    """
    logger.info(
        "Custom SIGINT handler triggered - preventing sandbox shutdown",
    )
    
    # -------------------------------------------------------------------------
    # 取消所有正在运行的异步任务
    # -------------------------------------------------------------------------
    try:
        # 获取当前正在运行的事件循环
        # 【事件循环是什么？】
        # 事件循环是异步编程的核心，它管理所有异步任务的执行
        loop = asyncio.get_running_loop()
        
        if loop and loop.is_running():
            # 获取所有未完成的任务
            # asyncio.all_tasks() 返回循环中所有任务
            # t.done() 检查任务是否已完成
            tasks = [t for t in asyncio.all_tasks(loop) if not t.done()]
            
            logger.info(f"Cancelling {len(tasks)} tasks due to SIGINT")
            
            # 取消每个任务
            # task.cancel() 会向任务抛出 CancelledError
            for task in tasks:
                task.cancel()
            
            logger.debug(f"Cancelled {len(tasks)} tasks due to SIGINT")
            
    except RuntimeError:
        # 如果没有运行中的事件循环，直接抛出 KeyboardInterrupt
        logger.info("No running event loop, raising KeyboardInterrupt")
        raise KeyboardInterrupt()  # pylint: disable=W0707


# ==============================================================================
# 第六部分：Agent 执行函数
# ==============================================================================
async def run_agent_task(
    user_msg: str,
    mode: str = "auto",
    user_data_config: list | None = None,
    use_long_term_memory_service: bool = False,
    use_llm_routing: bool = True,
) -> None:
    """
    运行 Agent 任务的主函数。
    
    【这个函数做了什么？】
    1. 根据模式选择合适的 Agent
    2. 创建 Sandbox（沙盒环境）
    3. 启动 Agent 执行用户任务
    4. 处理用户后续交互
    
    【参数说明】
    Args:
        user_msg: 用户的任务描述
        mode: Agent 模式
            - 'auto'   : 自动选择（智能路由）
            - 'general': 通用模式
            - 'browser': 浏览器模式
        user_data_config: 用户数据源配置
        use_long_term_memory_service: 是否启用长期记忆服务
        use_llm_routing: 是否使用 LLM 进行智能路由
    """
    global _original_sigint_handler

    # -------------------------------------------------------------------------
    # 智能路由选择
    # -------------------------------------------------------------------------
    # 如果模式是 'auto'，使用智能路由自动选择
    if mode == "auto":
        if use_llm_routing:
            # 使用 LLM 进行更智能的路由
            mode = await route_with_llm(user_msg, user_data_config)
        else:
            # 只使用关键词匹配
            mode = smart_route(user_msg, user_data_config)
        logger.info(f"🤖 Smart routing selected mode: {mode}")
    else:
        logger.info(f"📌 Using specified mode: {mode}")

    # -------------------------------------------------------------------------
    # 信号处理器设置（已注释）
    # -------------------------------------------------------------------------
    # 这部分代码被注释掉了，说明可能在某些环境下会有问题
    # 信号处理器在后面的代码中会再次设置

    # -------------------------------------------------------------------------
    # 初始化会话服务
    # -------------------------------------------------------------------------
    # 【什么是会话服务？】
    # 会话服务负责管理用户与 Agent 之间的对话
    # 它保存消息历史，管理对话状态
    session = MockSessionService(
        data_config=user_data_config,
        use_long_term_memory_service=use_long_term_memory_service,
    )

    # -------------------------------------------------------------------------
    # 创建用户代理
    # -------------------------------------------------------------------------
    # UserAgent 是一个模拟用户输入的 Agent
    # 当 Agent 需要用户反馈时，会通过这个对象获取输入
    user_agent = UserAgent(name="User")
    
    # 设置终端输入方式
    # TerminalUserInput 提供命令行输入功能
    user_agent.override_instance_input_method(
        input_method=TerminalUserInput(
            input_hint="User (Enter `exit` or `quit` to exit): ",
        ),
    )

    # -------------------------------------------------------------------------
    # 创建并进入 Sandbox
    # -------------------------------------------------------------------------
    # 【什么是 Sandbox？】
    # Sandbox（沙盒）是一个隔离的执行环境：
    # - 提供安全的代码执行空间
    # - 包含文件系统、浏览器等工具
    # - 任务结束后可以清理所有资源
    
    # 创建 Sandbox 实例
    sandbox = AliasSandbox()
    
    # __enter__() 是 Python 上下文管理器协议的一部分
    # 进入沙盒环境（启动容器等）
    sandbox.__enter__()

    # -------------------------------------------------------------------------
    # 设置信号处理器
    # -------------------------------------------------------------------------
    # 在 Sandbox 创建后重新设置信号处理器
    # 因为 Sandbox 库可能在 __enter__ 时安装了自己的处理器
    if _original_sigint_handler is None:
        _original_sigint_handler = signal.signal(
            signal.SIGINT,
            _safe_sigint_handler,
        )
    else:
        signal.signal(signal.SIGINT, _safe_sigint_handler)
    logger.debug("Re-installed custom SIGINT handler after sandbox creation")

    # 打印 Sandbox 信息
    logger.info(
        f"Sandbox mount dir: {sandbox.get_info().get('mount_dir')}",
    )
    logger.info(f"Sandbox desktop URL: {sandbox.desktop_url}")
    
    # 自动打开浏览器，显示 Sandbox 的桌面界面
    webbrowser.open(sandbox.desktop_url)

    # -------------------------------------------------------------------------
    # 创建初始用户消息
    # -------------------------------------------------------------------------
    # UserMessage 封装用户输入的内容
    initial_user_message = UserMessage(
        content=user_msg,
    )
    # 将消息添加到会话中
    await session.create_message(initial_user_message)

    # -------------------------------------------------------------------------
    # 执行 Agent 循环
    # -------------------------------------------------------------------------
    try:
        await _run_agent_loop(
            mode=mode,
            session=session,
            user_agent=user_agent,
            sandbox=sandbox,
        )
    finally:
        # -------------------------------------------------------------------------
        # 清理资源
        # -------------------------------------------------------------------------
        # finally 块确保无论是否发生异常，都会执行清理
        try:
            # 退出 Sandbox（停止容器等）
            sandbox.__exit__(None, None, None)
        except Exception:
            pass
        
        # 恢复原始信号处理器
        if _original_sigint_handler is not None:
            signal.signal(signal.SIGINT, _original_sigint_handler)
            _original_sigint_handler = None
            logger.debug("Restored original SIGINT handler")


async def _run_agent_loop(
    mode: str,
    session: MockSessionService,
    user_agent: UserAgent,
    sandbox: AliasSandbox,
) -> None:
    """
    执行 Agent 循环，处理任务和后续交互。
    
    【什么是"循环"？】
    Agent 执行完一个任务后，不立即退出，而是等待用户的下一条指令。
    这就像聊天软件，可以持续对话。
    
    【参数说明】
    Args:
        mode: Agent 模式
        session: 会话服务实例
        user_agent: 用户代理，用于获取用户输入
        sandbox: Sandbox 实例
    """
    # -------------------------------------------------------------------------
    # 主循环
    # -------------------------------------------------------------------------
    # while True 创建一个无限循环
    # 只有在用户输入 exit/quit 或发生错误时才会退出
    while True:
        # ---------------------------------------------------------------------
        # 根据模式选择并执行 Agent
        # ---------------------------------------------------------------------
        try:
            if mode == "browser":
                # 浏览器 Agent：用于网页操作任务
                await arun_browseruse_agent(
                    session,
                    sandbox=sandbox,
                )
            elif mode == "general":
                # 通用 Agent：用于复杂任务，可以调用其他 Agent
                await arun_meta_planner(
                    session,
                    sandbox=sandbox,
                )
            else:
                # 未知模式，抛出错误
                raise ValueError(f"Unknown mode: {mode}")

        except (KeyboardInterrupt, asyncio.CancelledError):
            # 用户按下 Ctrl+C 或任务被取消
            logger.info("Agent execution interrupted by user")
            # 继续循环，等待用户下一步指令
            
        except RuntimeError as e:
            # 检查是否是 Sandbox 容器被销毁的错误
            if "No container found" in str(e):
                logger.error(
                    "Sandbox container was destroyed during interruption. "
                    "Please restart the application to continue.",
                )
                logger.error(traceback.format_exc())
                break  # Sandbox 已不可用，退出循环
            else:
                raise  # 其他 RuntimeError，重新抛出
                
        except Exception as e:
            # 捕获所有其他异常，记录日志但不崩溃
            logger.error(f"Error running {mode} mode: {e}")
            logger.error(traceback.format_exc())

        # ---------------------------------------------------------------------
        # 检查后续交互
        # ---------------------------------------------------------------------
        # 等待用户输入下一条指令
        # user_agent() 会阻塞等待用户在终端输入
        follow_msg = await user_agent()
        
        # 检查用户是否要退出
        if len(follow_msg.content) == 0 or follow_msg.content.lower() in [
            "exit",
            "quit",
        ]:
            logger.info("Exiting agent loop")
            break  # 用户要求退出，跳出循环

        # 用户输入了新消息，添加到会话中
        await session.create_message(UserMessage(content=follow_msg.content))
        # 循环继续，Agent 会处理新消息


# ==============================================================================
# 第七部分：命令行入口
# ==============================================================================
def main():
    """
    CLI 主入口函数。
    
    【这个函数做什么？】
    1. 解析命令行参数
    2. 配置日志
    3. 执行用户请求的命令
    
    【执行流程】
    当用户执行 `alias run --task "xxx"` 时：
    1. Python 调用 main() 函数
    2. argparse 解析参数
    3. 根据参数调用 run_agent_task()
    """
    
    # -------------------------------------------------------------------------
    # 创建参数解析器
    # -------------------------------------------------------------------------
    # argparse.ArgumentParser 是参数解析的核心类
    parser = argparse.ArgumentParser(
        prog="alias",  # 程序名称
        description="Alias Agent System",  # 程序描述
        epilog=(  # 帮助信息末尾的示例
            "Example: alias run --mode general "
            "--task 'Analyze Meta stock performance'"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,  # 保留帮助文本格式
    )

    # -------------------------------------------------------------------------
    # 创建子命令
    # -------------------------------------------------------------------------
    # 子命令允许程序支持多种操作
    # 例如：alias run, alias status, alias config
    subparsers = parser.add_subparsers(
        dest="command",  # 存储子命令名的属性名
        help="Available commands",
    )

    # -------------------------------------------------------------------------
    # 'run' 子命令
    # -------------------------------------------------------------------------
    run_parser = subparsers.add_parser(
        "run",
        help="Run an agent task",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # --task 参数：用户要执行的任务
    run_parser.add_argument(
        "--task",
        type=str,
        required=True,  # 必填参数
        help="The task or query for the agent to execute",
    )

    # --mode 参数：Agent 模式选择
    run_parser.add_argument(
        "--mode",
        choices=["auto", "general", "browser"],  # 可选值
        default="auto",  # 默认值
        help=(
            "Agent mode (default: auto - intelligent selection):\n"
            "  'auto'     - Smart routing based on task content\n"
            "  'general'  - Meta planner with workers\n"
            "  'browser'  - Browser agent"
        ),
    )

    # --verbose 参数：详细日志输出
    run_parser.add_argument(
        "--verbose",
        "-v",  # 短参数名
        action="store_true",  # 布尔标志，出现即为 True
        help="Enable verbose logging",
    )

    # --datasource 参数：数据源
    run_parser.add_argument(
        "--datasource",
        "--files",
        "-d",
        dest="datasource",  # 存储时的属性名
        nargs="+",  # 接受一个或多个值
        help=(
            "Data sources for the agent to use. Multiple formats supported:\n"
            "  • Local files: ./data.txt, /absolute/path/file.json\n"
            "  • Databases: postgresql://localhost/db, sqlite:///data.db\n"
            "Example: "
            "    --datasource file.txt postgresql://localhost/db\n"
            "    --files file.txt"
        ),
    )

    # --dataconfig 参数：数据源配置文件
    run_parser.add_argument(
        "--dataconfig",
        "-dc",
        help=("Path to the data source configuration file"),
    )

    # --use_long_term_memory 参数：启用长期记忆
    run_parser.add_argument(
        "--use_long_term_memory",
        action="store_true",
        help="Enable long-term memory service for retrieving user profiling "
        "information at session start",
    )

    # --no-llm-routing 参数：禁用 LLM 路由
    run_parser.add_argument(
        "--no-llm-routing",
        action="store_true",
        help="Disable LLM-based intelligent routing, use keyword matching only",
    )

    # -------------------------------------------------------------------------
    # --version 参数：显示版本
    # -------------------------------------------------------------------------
    parser.add_argument(
        "--version",
        action="version",  # 特殊 action，自动处理版本显示
        version="Alias 0.2.0",
    )

    # -------------------------------------------------------------------------
    # 解析参数
    # -------------------------------------------------------------------------
    # parse_args() 读取 sys.argv 并返回解析后的参数对象
    args = parser.parse_args()

    # -------------------------------------------------------------------------
    # 配置日志
    # -------------------------------------------------------------------------
    if hasattr(args, "verbose") and args.verbose:
        # 如果指定了 -v，启用 DEBUG 级别日志
        logger.remove()  # 移除默认处理器
        logger.add(sys.stderr, level="DEBUG")  # 添加新的处理器

    # -------------------------------------------------------------------------
    # 处理命令
    # -------------------------------------------------------------------------
    if args.command == "run":
        try:
            # 处理数据源参数
            user_data = None
            data_endpoint = (
                args.datasource if hasattr(args, "datasource") else None
            )
            if data_endpoint:
                # 用户通过命令行提供了数据源
                user_data = (
                    data_endpoint
                    if isinstance(data_endpoint, list)
                    else [data_endpoint]
                )
            else:
                # 用户提供了配置文件
                if hasattr(args, "dataconfig") and args.dataconfig:
                    user_data = get_data_source_config_from_file(
                        args.dataconfig,
                    )

            # 运行 Agent 任务
            # asyncio.run() 创建事件循环并运行异步函数
            asyncio.run(
                run_agent_task(
                    user_msg=args.task,
                    mode=args.mode,
                    user_data_config=user_data,
                    use_long_term_memory_service=(
                        args.use_long_term_memory
                        if hasattr(args, "use_long_term_memory")
                        else False
                    ),
                    use_llm_routing=(
                        not args.no_llm_routing
                        if hasattr(args, "no_llm_routing")
                        else True
                    ),
                ),
            )
        except (KeyboardInterrupt, SystemExit) as e:
            # 处理中断和退出信号
            if isinstance(e, SystemExit) and e.code == 0:
                logger.info("\nInterrupted by user (signal handler)")
                sys.exit(0)
            else:
                logger.info("\nInterrupted by user")
                sys.exit(0)
        except Exception as e:
            # 处理其他异常
            logger.error(f"Error running agent: {e}")
            if hasattr(args, "verbose") and args.verbose:
                traceback.print_exc()
            sys.exit(1)
    else:
        # 没有指定子命令，显示帮助信息
        parser.print_help()
        sys.exit(1)


# ==============================================================================
# 程序入口点
# ==============================================================================
# 当直接运行这个文件时（python cli.py），__name__ 会是 "__main__"
# 当作为模块导入时（import cli），__name__ 会是 "cli"
if __name__ == "__main__":
    main()
