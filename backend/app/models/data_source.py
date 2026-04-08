import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, JSON
from app.database import Base


class DataSource(Base):
    """数据源配置"""
    __tablename__ = "data_sources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # mysql, postgresql, etc.
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    database_name = Column(String(100), nullable=False)
    username = Column(String(100), nullable=False)
    password_encrypted = Column(Text, nullable=False)
    connection_options = Column(JSON, default={})

    # 元数据缓存
    schema_cache = Column(JSON)
    schema_cache_updated_at = Column(DateTime)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
