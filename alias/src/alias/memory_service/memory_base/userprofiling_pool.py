# -*- coding: utf-8 -*-
"""
用户画像记忆池实现（新手教学注释版）。

在 BaseAsyncVectorMemory 之上增加：
1) is_confirmed 元数据标准化
2) 用户信息/用户事件抽取接口
"""

import asyncio
import ast
import re
from typing import Any, Dict, List, Optional

from mem0.memory.setup import setup_config

from alias.memory_service.profiling_utils.logging_utils import setup_logging
from alias.memory_service.profiling_utils.memory_utils import (
    _normalize_is_confirmed,
)

from .base_vec_memory import BaseAsyncVectorMemory
from .prompt import EXTRACT_USER_EVENT, EXTRACT_USER_INFO

logger = setup_logging()

setup_config()


class AsyncVectorUserProfilingMemory(BaseAsyncVectorMemory):
    def _prepare_metadata_for_add(
        self,
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        # 统一把 is_confirmed 归一为 0/1 整数，便于过滤。
        prepared_metadata = super()._prepare_metadata_for_add(metadata)
        if "is_confirmed" in prepared_metadata:
            prepared_metadata["is_confirmed"] = _normalize_is_confirmed(
                prepared_metadata["is_confirmed"],
            )
        else:
            prepared_metadata["is_confirmed"] = 0
        return prepared_metadata

    async def get_user_info_memory(self, content: Any) -> List[str]:
        """
        Extracts the User Info Memory from the given content.
        """
        try:
            memory_content = self._preprocess_content(content)
            user_prompt = (
                f"Please extract the user information from the following "
                f"content: \n'{memory_content}'"
            )

            await asyncio.sleep(2)
            user_info_response = await asyncio.to_thread(
                self.llm.generate_response,
                messages=[
                    {"role": "system", "content": EXTRACT_USER_INFO},
                    {"role": "user", "content": user_prompt},
                ],
            )

            facts = self._format_llm_output_to_list(user_info_response)
            return facts

        except Exception as exc:
            logger.warning(f"Error in get_user_info_memory: {exc}")
            return []

    async def get_user_event_memory(self, content: Any) -> List[str]:
        """
        从内容中抽取用户事件记忆。
        """
        try:
            memory_content = self._preprocess_content(content)
            user_prompt = (
                f"Please extract the event information from the following "
                f"content: \n'{memory_content}'"
            )

            await asyncio.sleep(2)
            user_event_response = await asyncio.to_thread(
                self.llm.generate_response,
                messages=[
                    {"role": "system", "content": EXTRACT_USER_EVENT},
                    {"role": "user", "content": user_prompt},
                ],
            )

            facts = self._format_llm_output_to_list(user_event_response)
            return facts

        except Exception as exc:
            logger.warning(f"Error in get_user_event_memory: {exc}")
            return []

    def _format_llm_output_to_list(self, llm_output: str) -> List[str]:
        """
        Convert LLM output into a Python list of strings.
        """
        if not llm_output or not isinstance(llm_output, str):
            return []

        cleaned = llm_output.strip()
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)
        else:
            return []

        try:
            parsed_list = ast.literal_eval(cleaned)
            if isinstance(parsed_list, list):
                return [str(item).strip() for item in parsed_list]
            return []
        except (SyntaxError, ValueError):
            return []
