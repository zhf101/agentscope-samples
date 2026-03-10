# -*- coding: utf-8 -*-
"""长文本后处理 Hook（新手教学注释版）。"""

from alias.agent.tools.toolkit_hooks.text_post_hook import TextPostHook


class LongTextPostHook(TextPostHook):
    def __init__(self, sandbox):
        # 继承 TextPostHook，仅放宽预算并关闭自动落盘。
        super().__init__(sandbox, budget=8194 * 10, auto_save=False)
