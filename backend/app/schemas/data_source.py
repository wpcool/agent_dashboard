from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


class DataSourceBase(BaseModel):
    name: str = Field(..., description="数据源名称")
    type: str = Field(..., description="数据库类型: mysql, postgresql, etc.")
    host: str = Field(..., description="主机地址")
    port: int = Field(..., description="端口")
    database_name: str = Field(..., description="数据库名")
    username: str = Field(..., description="用户名")
    connection_options: Dict[str, Any] = Field(default={}, description="连接选项")


class DataSourceCreate(DataSourceBase):
    password: str = Field(..., description="密码")


class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    connection_options: Optional[Dict[str, Any]] = None


class DataSourceResponse(DataSourceBase):
    id: UUID
    schema_cache: Optional[Dict[str, Any]] = None
    schema_cache_updated_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
