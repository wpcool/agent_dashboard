import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON
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

    # 工作流定义
    workflow_definition = Column(JSON)

    # 审计
    created_by = Column(String(36))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
