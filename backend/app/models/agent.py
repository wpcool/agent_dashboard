import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY as PG_ARRAY, JSONB
from app.database import Base


class Agent(Base):
    """智能体模型"""
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_builtin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # 角色配置
    persona_system_prompt = Column(Text)
    persona_expertise = Column(PG_ARRAY(String))
    thinking_style = Column(String(50))

    # 输出风格
    output_format = Column(Text)
    output_verbosity = Column(String(20))
    visualization_preferences = Column(PG_ARRAY(String))

    # 工作流定义
    workflow_definition = Column(JSONB)

    # 审计
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
