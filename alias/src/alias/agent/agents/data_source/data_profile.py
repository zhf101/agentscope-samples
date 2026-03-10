# -*- coding: utf-8 -*-
"""
================================================================================
Data Profile - 数据分析概况生成
================================================================================

【什么是数据概况？】
数据概况是对数据源的"体检报告"：
- 文件有多少行、多少列？
- 每列是什么数据类型？
- 有没有缺失值？
- 数据的统计特征是什么？

【为什么需要数据概况？】
1. 帮助 Agent 理解数据
   - 知道数据长什么样
   - 选择合适的分析方法

2. 帮助用户了解数据
   - 快速了解数据质量
   - 发现潜在问题

【支持的数据类型】
- CSV：逗号分隔值文件
- Excel：电子表格文件
- Image：图片文件
- Relational DB：关系型数据库

【工作流程】

┌─────────────────────────────────────────────────────────────────────────────┐
│                          data_profile() 函数                                 │
│                                                                              │
│  输入：                                                                       │
│  - sandbox: 沙箱环境                                                         │
│  - sandbox_path: 数据源路径                                                  │
│  - source_type: 数据源类型                                                   │
│  - llm_call_manager: LLM 调用管理器                                          │
│                                                                              │
│  处理流程：                                                                   │
│  1. 判断数据源类型                                                            │
│  2. 如果是文件，从沙箱复制到本地                                              │
│  3. 选择合适的分析器（Profiler）                                              │
│  4. 调用 LLM 生成数据概况                                                    │
│                                                                              │
│  输出：                                                                       │
│  - 数据概况字典，包含描述和统计信息                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

【学习要点】
1. 工厂模式（DataProfilerFactory）
2. 文件处理（tempfile、BytesIO）
3. 异步函数（async/await）
4. Base64 编解码
"""
import os
import base64
import tempfile  # 临时文件处理
from typing import Any, Dict
from io import BytesIO  # 内存中的二进制流
from pathlib import Path
import requests  # HTTP 请求库

from alias.agent.agents.data_source._typing import SourceType
from alias.agent.agents.data_source._data_profiler_factory import (
    DataProfilerFactory,  # 数据分析器工厂
)
from alias.agent.tools.sandbox_util import (
    get_workspace_file,  # 获取工作空间文件
)
from alias.runtime.alias_sandbox.alias_sandbox import AliasSandbox
from alias.agent.utils.llm_call_manager import (
    LLMCallManager,  # LLM 调用管理器
)


# ==============================================================================
# 辅助函数
# ==============================================================================
def _get_binary_buffer(
    sandbox: AliasSandbox,
    file_url: str,
):
    """
    获取文件的二进制缓冲区。

    【支持两种来源】
    1. URL（http/https）：从网络下载
    2. 沙箱路径：从沙箱获取

    【为什么返回 BytesIO？】
    BytesIO 是内存中的二进制流：
    - 不需要写入磁盘
    - 可以像文件一样读写
    - 性能更好

    Args:
        sandbox: 沙箱环境
        file_url: 文件 URL 或路径

    Returns:
        BytesIO: 内存中的二进制流
    """
    if file_url.startswith(("http://", "https://")):
        # 从网络下载
        response = requests.get(file_url)
        response.raise_for_status()  # 检查请求是否成功
        buffer = BytesIO(response.content)
    else:
        # 从沙箱获取
        # get_workspace_file 返回 base64 编码的内容
        # base64.b64decode 解码成二进制
        buffer = BytesIO(
            base64.b64decode(get_workspace_file(sandbox, file_url)),
        )
    return buffer


def _copy_file_from_sandbox_with_original_name(
    sandbox: AliasSandbox,
    file_path: str,
) -> str:
    """
    从沙箱或 URL 复制文件到本地临时文件。

    【为什么需要复制到本地？】
    数据分析库（pandas、PIL 等）需要本地文件路径。
    沙箱中的文件不能直接访问，需要先复制出来。

    【处理流程】
    1. 判断是 URL 还是沙箱路径
    2. 如果是 URL，直接使用 URL
    3. 如果是沙箱路径：
       a. 获取文件内容
       b. 创建临时目录
       c. 写入临时文件
       d. 返回临时文件路径

    Args:
        sandbox: 沙箱环境
        file_path: 源路径或 URL

    Returns:
        str: 本地临时文件路径
    """
    # 处理不同类型的文件 URL
    if file_path.startswith(("http://", "https://")):
        # 对于网络 URL，直接使用 URL
        file_source = file_path
    else:
        # 对于本地文件，保存到临时文件
        file_buffer = _get_binary_buffer(
            sandbox,
            file_path,
        )

        # 创建临时目录
        # tempfile.mkdtemp() 创建一个唯一的临时目录
        temp_dir = tempfile.mkdtemp()

        # 获取原始文件名
        target_file_name = os.path.basename(file_path)

        # 构建完整路径
        full_path = Path(temp_dir) / target_file_name

        # 写入文件
        with open(full_path, "wb") as f:
            f.write(file_buffer.getvalue())

        file_source = full_path

    return str(file_source)


# ==============================================================================
# 主要函数
# ==============================================================================
async def data_profile(
    sandbox: AliasSandbox,
    sandbox_path: str,
    source_type: SourceType,
    llm_call_manager: LLMCallManager,
) -> Dict[str, Any]:
    """
    生成数据源的详细概况。

    【这是数据源分析的入口函数】

    【参数详解】
    - sandbox: 沙箱环境实例
    - sandbox_path: 数据源位置
      - 文件：文件路径或 URL
      - 数据库：连接字符串（DSN）
    - source_type: 数据源类型（枚举值）
    - llm_call_manager: LLM 调用管理器（用于生成描述）

    【返回值】
    字典，包含数据概况：
    - description: 文字描述
    - statistics: 统计信息
    - columns: 列信息

    【工作流程】
    1. 根据数据源类型处理文件
    2. 使用工厂创建分析器
    3. 调用分析器生成概况

    【示例】
    profile = await data_profile(
        sandbox=sandbox,
        sandbox_path="/workspace/data.csv",
        source_type=SourceType.CSV,
        llm_call_manager=llm_manager,
    )
    # 返回: {"description": "销售数据，1000行，5列...", ...}
    """
    # 根据数据源类型处理文件
    if source_type in [SourceType.CSV, SourceType.EXCEL, SourceType.IMAGE]:
        # 文件类型：复制到本地
        local_path = _copy_file_from_sandbox_with_original_name(
            sandbox,
            sandbox_path,
        )
    elif source_type == SourceType.RELATIONAL_DB:
        # 数据库类型：直接使用连接字符串
        local_path = sandbox_path
    else:
        # 不支持的类型
        raise ValueError(f"Unsupported source type {source_type}")

    # 使用工厂模式创建分析器
    profiler = DataProfilerFactory.get_profiler(
        llm_call_manager=llm_call_manager,
        path=local_path,
        source_type=source_type,
    )

    # 生成并返回数据概况
    return await profiler.generate_profile()
