import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Agent(Base):
    """智能体模型"""
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_builtin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # 角色配置
    persona_system_prompt = Column(Text)
    persona_expertise = Column(Text)  # JSON string for SQLite compatibility
    thinking_style = Column(String(50))

    # 输出风格
    output_format = Column(Text)
    output_verbosity = Column(String(20))
    visualization_preferences = Column(Text)  # JSON string for SQLite compatibility

    # 数据权限配置 (JSON)
    data_scope = Column(JSON)

    # 关联的 Skills
    skills = relationship("Skill", secondary="agent_skills", back_populates="agents")

    # 审计
    created_by = Column(String(36))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_system_prompt(self):
        """组装完整的系统提示词"""
        import json

        # 基础提示词
        base_prompt = self.persona_system_prompt or "你是一位数据分析助手。"

        # 收集所有 Skill 的提示词片段
        skill_prompts = []
        for skill in self.skills:
            if skill.is_active and skill.system_prompt_fragment:
                skill_prompts.append(f"\n## {skill.name}\n{skill.system_prompt_fragment}")

        # 专长
        expertise = json.loads(self.persona_expertise) if self.persona_expertise else []
        expertise_str = ", ".join(expertise) if expertise else "数据分析"

        # 输出风格
        output_format = self.output_format or "简洁回答，必要时提供数据支撑"

        full_prompt = f"""{base_prompt}

你具备以下专业能力：{expertise_str}

你拥有以下技能模块：
{chr(10).join(skill_prompts)}

输出风格要求：
- 格式：{output_format}
- 详细程度：{self.output_verbosity or "concise"}
- 思考方式：{self.thinking_style or "先分析再回答"}
"""
        return full_prompt

    def to_config(self):
        """转换为配置字典"""
        import json
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "is_builtin": self.is_builtin,
            "persona": {
                "system_prompt": self.persona_system_prompt,
                "expertise": json.loads(self.persona_expertise) if self.persona_expertise else [],
                "thinking_style": self.thinking_style
            },
            "data_scope": self.data_scope or {},
            "output": {
                "format": self.output_format,
                "verbosity": self.output_verbosity,
                "visualization_preferences": json.loads(self.visualization_preferences) if self.visualization_preferences else ["table"]
            },
            "workflow": self.workflow_definition or {}
        }
