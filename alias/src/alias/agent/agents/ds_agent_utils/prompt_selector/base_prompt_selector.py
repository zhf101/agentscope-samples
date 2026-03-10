# -*- coding: utf-8 -*-
"""
Prompt 选择器的抽象基类（中文教学注释版）。

使用场景：
- 同一类任务有多个 prompt 模板；
- 需要根据用户输入自动选最合适的模板；
- 不同实现可以用规则、模型或检索来做选择。
"""

from abc import ABC, abstractmethod
from typing import Dict, List


class PromptSelector(ABC):
    """
    Prompt 选择器的“抽象基类”。

    抽象基类（ABC）说明：
    - 不能直接实例化；
    - 子类必须实现 @abstractmethod 标记的方法；
    - 用来强制统一接口。
    """

    def __init__(self, available_prompts: Dict[str, str]):
        """
        Args:
            available_prompts: 可用 prompt 的字典
            结构为 {场景名: prompt 内容}
            例子：{"data_analyze": "...", "forecast": "..."}
        """
        # 保存可用 prompt 列表，后续选择时会用到
        self.available_prompts = available_prompts

    @abstractmethod
    async def select(self, input_data: str) -> List[str]:
        """
        根据输入选择最合适的 prompt（抽象方法）。
        Args:
            input: 用户输入或任务描述
        Returns:
            选中的 prompt 场景列表（按优先级排序）
            例如：["data_analyze", "forecast"]
        """

    def get_prompt_by_scenario(self, scenario: str) -> str:
        """
        根据场景名拿到 prompt 内容。
        Args:
            scenario: 场景名
        Returns:
            prompt 内容，如果场景不存在则返回空字符串
        """
        return self.available_prompts.get(scenario, "")

    def get_all_scenarios(self) -> List[str]:
        """获取所有可用场景名列表。"""
        return list(self.available_prompts.keys())
