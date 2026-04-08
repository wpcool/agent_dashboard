from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


class ChatMessageBase(BaseModel):
    role: str = Field(..., description="消息角色: user/assistant/system")
    content: str = Field(..., description="消息内容")
    content_type: str = Field(default="text", description="内容类型: text/sql/chart/report")


class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessageResponse(ChatMessageBase):
    id: UUID
    conversation_id: UUID
    execution_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str = Field(..., description="用户消息")
    conversation_id: Optional[UUID] = Field(None, description="对话 ID，新建对话时为空")
    agent_id: Optional[UUID] = Field(None, description="智能体 ID")


class ChatResponse(BaseModel):
    message: ChatMessageResponse
    sql: Optional[str] = Field(None, description="生成的 SQL")
    results: Optional[List[Dict[str, Any]]] = Field(None, description="查询结果")
    explanation: Optional[str] = Field(None, description="结果解读")
    needs_verification: bool = Field(False, description="是否需要人工验证")


class ConversationCreate(BaseModel):
    title: Optional[str] = Field(None, description="对话标题")
    agent_id: Optional[UUID] = Field(None, description="初始智能体 ID")


class ConversationResponse(BaseModel):
    id: UUID
    title: Optional[str]
    current_agent_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    messages: List[ChatMessageResponse]