"""
Skill 模型 - 智能体技能定义
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base


# Agent-Skill 多对多关联表
agent_skill_association = Table(
    'agent_skills',
    Base.metadata,
    Column('agent_id', String(36), ForeignKey('agents.id')),
    Column('skill_id', String(36), ForeignKey('skills.id'))
)


class Skill(Base):
    """技能定义"""
    __tablename__ = "skills"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon = Column(String(50), default="🔧")  # 技能图标

    # 技能类型: builtin(内置) / custom(自定义)
    skill_type = Column(String(20), default="builtin")
    is_active = Column(Boolean, default=True)

    # 系统提示词片段（会被组合到 Agent 的完整提示词中）
    system_prompt_fragment = Column(Text)

    # 能力声明（用于意图路由）
    capabilities = Column(JSON)  # ["query", "analysis", "forecast"]

    # 输入/输出定义
    input_schema = Column(JSON)   # {"query": "string", "context": "object"}
    output_schema = Column(JSON)  # {"sql": "string", "explanation": "string"}

    # 执行配置
    execution_config = Column(JSON)  # {"timeout": 30, "max_retries": 2}

    # 关联的 Agent
    agents = relationship("Agent", secondary=agent_skill_association, back_populates="skills")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentSkillConfig(Base):
    """Agent 对 Skill 的个性化配置"""
    __tablename__ = "agent_skill_configs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(36), ForeignKey("agents.id"))
    skill_id = Column(String(36), ForeignKey("skills.id"))

    # 个性化提示词（覆盖或扩展 Skill 默认提示词）
    custom_prompt = Column(Text)

    # 执行参数覆盖
    custom_config = Column(JSON)

    # 排序权重（决定 Skill 执行顺序）
    priority = Column(String(36), default=0)

    is_enabled = Column(Boolean, default=True)
