# -*- coding: utf-8 -*-
"""
数据科学 Agent 的模型与提示词路径配置（中文教学注释版）。

这个文件的目的：
1) 读取环境变量，决定“用哪个模型”；
2) 指定提示词（prompt）文件的默认路径；
3) 构造 model + formatter 的映射，供其他模块调用。
"""

import os
from agentscope.model import DashScopeChatModel
from agentscope.formatter import DashScopeChatFormatter

# 提示词（prompt）默认所在目录：
# 这里用 os.path.join + __file__ 计算“相对当前文件”的路径。
_DEFAULT_PROMPT_PATH = os.path.join(
    os.path.dirname(__file__),
    "built_in_prompt",
)
PROMPT_DS_BASE_PATH = os.getenv(
    # 允许外部通过环境变量覆盖默认路径
    "PROMPT_DS_BASE_PATH",
    _DEFAULT_PROMPT_PATH,
)

# 视觉模型和文本模型的名称：
# 如果环境变量没设置，就用默认值。
VL_MODEL_NAME = os.getenv("VISION_MODEL", "qwen-vl-max")
MODEL_CONFIG_NAME = os.getenv("MODEL", "qwen3-max")

# 模型与格式化器的映射：
# key 是模型名字，value 是 [模型实例, 格式化器实例]
MODEL_FORMATTER_MAPPING = {
    "qwen3-max": [
        DashScopeChatModel(
            api_key=os.environ.get("DASHSCOPE_API_KEY"),
            model_name="qwen3-max-preview",
            stream=True,
        ),
        DashScopeChatFormatter(),
    ],
    "qwen-vl-max": [
        DashScopeChatModel(
            api_key=os.environ.get("DASHSCOPE_API_KEY"),
            model_name="qwen-vl-max-latest",
            stream=True,
        ),
        DashScopeChatFormatter(),
    ],
}
