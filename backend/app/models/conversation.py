import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.database import Base


class Conversation(Base):
    """对话会话"""
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    current_agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"))

    title = Column(String(200))

    # 当前智能体上下文
    current_context = Column(JSONB, default={})

    # 历史切换记录
    context_history = Column(ARRAY(JSONB), default=[])

    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Message(Base):
    """消息记录"""
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"))

    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    content_type = Column(String(20), default="text")  # text, sql, chart, report

    # 执行元数据
    execution_metadata = Column(JSONB)

    # 流式响应标记
    is_streaming = Column(Boolean, default=False)
    streaming_completed_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
