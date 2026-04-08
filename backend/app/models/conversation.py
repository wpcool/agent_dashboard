import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean, JSON
from app.database import Base


class Conversation(Base):
    """对话会话"""
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False)
    current_agent_id = Column(String(36), ForeignKey("agents.id"))

    title = Column(String(200))

    # 当前智能体上下文
    current_context = Column(JSON, default={})

    # 历史切换记录 - stored as JSON string for SQLite
    context_history = Column(JSON, default=[])

    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Message(Base):
    """消息记录"""
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"))

    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    content_type = Column(String(20), default="text")  # text, sql, chart, report

    # 执行元数据
    execution_metadata = Column(JSON)

    # 流式响应标记
    is_streaming = Column(Boolean, default=False)
    streaming_completed_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
