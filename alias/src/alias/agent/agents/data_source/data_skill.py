# -*- coding: utf-8 -*-
"""
================================================================================
Data Skill - 数据技能管理
================================================================================

【什么是数据技能？】
数据技能是针对特定数据源类型的"专业知识"：
- CSV 文件如何分析？
- Excel 表格怎么处理？
- 图片数据怎么理解？

每个技能包含：
- 技能名称
- 技能描述
- 适用数据源类型
- 技能内容（提示词）

【技能的作用】

┌─────────────────────────────────────────────────────────────────────────────┐
│                        DataScienceAgent 工作流程                              │
│                                                                              │
│  用户任务："分析销售数据"                                                     │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ DataSkillManager                                                     │    │
│  │                                                                      │    │
│  │ 1. 检测数据源类型：sales.csv → CSV                                   │    │
│  │ 2. 加载对应技能：csv_analysis_skill                                  │    │
│  │ 3. 把技能添加到系统提示词                                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         ▼                                                                    │
│  Agent 获得专业知识：                                                        │
│  "对于 CSV 文件，应该先检查列类型，然后..."                                  │
│         │                                                                    │
│         ▼                                                                    │
│  更准确的数据分析                                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

【技能文件格式】
技能存储在 SKILL.md 文件中，使用 YAML Front Matter：

```markdown
---
name: csv_analysis
description: CSV 文件分析技能
type: [csv]
---

# CSV 文件分析指南

1. 首先检查文件的分隔符...
2. 然后分析列的数据类型...
```

【技能目录结构】
```
_built_in_skill/
└── data/
    ├── csv/
    │   └── SKILL.md
    ├── excel/
    │   └── SKILL.md
    └── image/
        └── SKILL.md
```

【学习要点】
1. YAML Front Matter（文件头元数据）
2. 技能注册和发现机制
3. 类型到技能的映射
"""
import os
from pathlib import Path
from typing import List

import frontmatter  # YAML Front Matter 解析库
from loguru import logger

from agentscope.tool._types import AgentSkill  # Agent 技能基类

from alias.agent.agents.ds_agent_utils.utils import get_prompt_from_file
from alias.agent.agents.data_source._typing import SourceType


# ==============================================================================
# DataSkill 数据模型
# ==============================================================================
class DataSkill(AgentSkill):
    """
    数据技能模型 - 继承自 AgentSkill。

    【继承关系】
    AgentSkill（父类）提供：
    - name: 技能名称
    - description: 技能描述
    - dir: 技能文件路径

    DataSkill 添加：
    - type: 适用数据源类型列表

    【示例】
    skill = DataSkill(
        name="csv_analysis",
        description="CSV 文件分析技能",
        type=[SourceType.CSV],
        dir="/path/to/SKILL.md"
    )
    """

    # 数据源类型列表：这个技能适用于哪些类型的数据
    type: List[SourceType]


# ==============================================================================
# DataSkillManager 类定义
# ==============================================================================
class DataSkillManager:
    """
    数据技能管理器 - 管理和选择数据技能。

    【核心功能】
    1. 注册技能：从目录加载技能定义
    2. 选择技能：根据数据源类型选择合适的技能
    3. 加载技能：返回技能内容

    【映射机制】
    维护一个 source_type -> skill 的映射：
    {
        SourceType.CSV: csv_skill,
        SourceType.EXCEL: excel_skill,
        SourceType.IMAGE: image_skill,
    }
    """

    # 默认技能目录路径
    # Path(__file__) 获取当前文件路径
    # .parent.parent 向上两级目录
    _default_skill_path_base = os.path.join(
        Path(__file__).resolve().parent.parent,
        "_built_in_skill/data",
    )

    def __init__(
        self,
    ):
        """初始化技能管理器，自动注册默认技能目录中的所有技能。"""
        # 注册所有技能
        self.skills = self.register_skill_dir()

        # 构建数据源类型到技能的映射
        self.source_type_2_skills = {}
        for skill in self.skills:
            # 每个技能可能适用于多种数据源类型
            for t in skill["type"]:
                self.source_type_2_skills[t] = skill

    def load(self, data_source_types: List[SourceType]) -> List[str]:
        """
        根据数据源类型加载技能。

        【使用场景】
        当 Agent 需要处理特定类型的数据时：
        1. 告诉管理器数据源类型
        2. 管理器返回对应的技能内容
        3. Agent 把技能内容加入系统提示词

        Args:
            data_source_types: 数据源类型列表

        Returns:
            技能内容列表（字符串形式）
        """
        if not data_source_types:
            return []

        selected_skills = []

        # 去重
        data_source_types = set(data_source_types)

        for source_type in data_source_types:
            try:
                # 从映射中获取技能
                skill = self.source_type_2_skills.get(source_type, None)

                # 如果没有对应的技能，跳过
                if not skill:
                    logger.warning(
                        "DataSkillSelector found no valid skill for data "
                        f"source type: {source_type}",
                    )
                else:
                    logger.info(
                        f"DataSkillSelector selected skill: {skill['name']} "
                        f"for data source type: {source_type}",
                    )

                # 读取技能文件内容
                skill_content = get_prompt_from_file(
                    skill["dir"],
                    return_json=False,
                )
                if skill_content:
                    selected_skills.append(skill_content)

            except Exception as e:
                logger.error(
                    f"DataSkillSelector selection failed: {str(e)} "
                    f"for data source type: {source_type}",
                )
                continue

        return selected_skills

    def register_skill_dir(self, skill_dir=_default_skill_path_base):
        """
        注册目录中的所有技能。

        【工作原理】
        遍历目录结构，找到所有包含 SKILL.md 的子目录，
        解析并注册这些技能。

        Args:
            skill_dir: 技能目录路径

        Returns:
            技能列表
        """
        skills = []

        # 检查目录是否存在
        if not os.path.isdir(skill_dir):
            raise ValueError(
                f"The skill directory '{skill_dir}' does not exist or is "
                "not a directory.",
            )

        # 遍历目录
        # os.walk 返回 (root, dirs, files) 三元组
        for root, dirs, _ in os.walk(skill_dir):
            # 处理每个子目录
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                skill = self.register_skill(dir_path)
                if skill:
                    skills.append(skill)

        return skills

    def register_skill(self, path: str, name=None):
        """
        注册单个技能。

        【工作流程】
        1. 解析技能路径
        2. 读取 SKILL.md 文件
        3. 解析 YAML Front Matter
        4. 验证必填字段
        5. 创建 DataSkill 对象

        Args:
            path: 技能目录路径
            name: 可选的技能名称

        Returns:
            DataSkill 对象，或 None（失败时）
        """
        try:
            # 解析技能路径
            file_path = self._resolve_skill_path(path)
            if not file_path:
                raise FileNotFoundError("`SKILL.md` not found")

            # 解析技能文件
            skill = self._parse_skill_file(file_path, name)
            logger.info(
                f"Successfully registered skill '{skill['name']}' "
                f"from '{file_path}'",
            )

            return skill

        except Exception as e:
            logger.error(
                f"Failed to register skill '{skill['name']}' from "
                f"'{path}': {e}",
            )
            return None

    def _resolve_skill_path(self, path: str) -> str:
        """
        解析技能路径，找到 SKILL.md 文件。

        【路径解析规则】
        - 如果是目录，查找目录下的 SKILL.md
        - 如果是文件路径，直接返回

        Args:
            path: 目录路径或文件路径

        Returns:
            SKILL.md 的完整路径
        """
        if os.path.isdir(path):
            skill_md_path = os.path.join(path, "SKILL.md")
            if not os.path.isfile(skill_md_path):
                logger.warning(f"Directory '{path}' does not contain SKILL.md")
                return ""
            return skill_md_path
        else:
            logger.warning(f"Invalid skill path: {path}")
            return ""

    def _parse_skill_file(self, file_path, name=None):
        """
        解析技能文件。

        【YAML Front Matter 格式】
        ---
        name: skill_name
        description: 技能描述
        type: [csv, excel]  # 或单个值: csv
        ---

        技能内容（Markdown 格式）...

        【解析过程】
        1. 使用 frontmatter.load() 解析文件
        2. 提取 YAML 头中的元数据
        3. 验证必填字段
        4. 创建 DataSkill 对象

        Args:
            file_path: 技能文件路径
            name: 可选的技能名称

        Returns:
            DataSkill 对象
        """
        # 解析 YAML Front Matter
        post = frontmatter.load(file_path)

        # 获取技能名称
        if name is None:
            dir_name = os.path.basename(os.path.dirname(file_path))
            name = post.get("name", dir_name)
        else:
            name = post.get("name", name)

        # 获取描述和类型
        description = post.get("description", None)
        _type = post.get("type", None)

        # 验证必填字段
        if not name or not description or not _type:
            raise ValueError(
                f"The file '{file_path}' must have a YAML Front "
                "Matter including `name`, `description`, and `type` fields",
            )

        # 确保类型是列表
        _type = _type if isinstance(_type, list) else [_type]

        # 验证类型值是否有效
        if any(not SourceType.is_valid_source_type(t) for t in _type):
            raise ValueError(
                f"Type of file '{file_path}' must be a member "
                "(or a list of members) of SourceType",
            )

        # 转换类型
        name, description = str(name), str(description)
        _type = [SourceType(t) for t in _type]

        # 创建并返回 DataSkill 对象
        return DataSkill(
            name=name,
            description=description,
            type=_type,
            dir=file_path,
        )
