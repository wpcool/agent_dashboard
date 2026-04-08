import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Conversation, Message, DataSource
from app.schemas.chat import (
    ChatRequest, ChatResponse, ChatMessageResponse,
    ConversationCreate, ConversationResponse, ConversationDetailResponse
)
from app.schemas.data_source import DataSourceCreate, DataSourceUpdate, DataSourceResponse
from app.services.ai_engine import AIEngine
from app.services.time_resolver import TimeResolver
from app.services.query_executor import QueryExecutor
from app.services.accuracy_guard import AccuracyGuard
from cryptography.fernet import Fernet
import os

router = APIRouter()

# 简单的加密密钥（生产环境应从环境变量读取）
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())
fernet = Fernet(ENCRYPTION_KEY)


def encrypt_password(password: str) -> str:
    """加密密码"""
    return fernet.encrypt(password.encode()).decode()


def decrypt_password(encrypted: str) -> str:
    """解密密码"""
    return fernet.decrypt(encrypted.encode()).decode()


@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(
    req: ConversationCreate,
    db: Session = Depends(get_db)
):
    """创建新对话"""
    # 使用默认智能体（后续从配置读取）
    default_agent_id = None

    conversation = Conversation(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),  # TODO: 从认证获取
        current_agent_id=req.agent_id or default_agent_id,
        title=req.title or "新对话"
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """获取对话详情"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    return conversation


@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    对话接口：自然语言问数

    完整流程：
    1. 保存用户消息
    2. 解析时间表达式
    3. 生成 SQL
    4. 执行查询
    5. 解读结果
    6. 返回响应
    """
    # 获取或创建对话
    if req.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == req.conversation_id
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
    else:
        conversation = Conversation(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            title=req.message[:20] + "..."
        )
        db.add(conversation)

    # 保存用户消息
    user_message = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        role="user",
        content=req.message
    )
    db.add(user_message)
    db.commit()

    # 初始化服务
    ai_engine = AIEngine()
    time_resolver = TimeResolver()
    accuracy_guard = AccuracyGuard()

    # 1. 检查是否需要澄清
    needs_clarify, clarify_hint = accuracy_guard.needs_clarification(req.message)
    if needs_clarify:
        assistant_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role="assistant",
            content=f"我需要确认一下：{clarify_hint}",
            execution_metadata={"needs_clarification": True}
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)

        return ChatResponse(
            message=ChatMessageResponse.model_validate(assistant_message),
            needs_verification=True
        )

    # 2. 解析时间表达式
    resolved_time = {}
    # 简单提取常见时间词
    time_keywords = ['昨天', '今天', '上周', '本周', '上月', '本月', '最近']
    for keyword in time_keywords:
        if keyword in req.message:
            time_range = time_resolver.resolve(keyword)
            if time_range:
                resolved_time[keyword] = {
                    "start": time_range.start.isoformat(),
                    "end": time_range.end.isoformat()
                }

    # 3. 获取 Schema（使用默认数据源）
    # TODO: 支持多数据源
    data_source = db.query(DataSource).filter(DataSource.is_active == True).first()
    if not data_source:
        # 没有数据源，返回提示
        assistant_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role="assistant",
            content="请先配置数据源。"
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)

        return ChatResponse(message=ChatMessageResponse.model_validate(assistant_message))

    schema = data_source.schema_cache or {"tables": []}

    # 4. 生成 SQL
    sql_result = await ai_engine.generate_sql(
        question=req.message,
        schema=schema,
        resolved_time=resolved_time
    )

    # 5. SQL 完整性检查
    verification = accuracy_guard.verify_sql_completeness(sql_result.sql, req.message)
    if not verification.is_valid:
        sql_result.needs_verification = True
        sql_result.explanation += f"\n\n注意：{', '.join(verification.issues)}"

    # 6. 执行查询（如果需要）
    query_result = None
    results = None
    explanation = sql_result.explanation

    if sql_result.sql and not sql_result.needs_verification:
        try:
            executor = QueryExecutor(db)
            query_result = executor.execute(sql_result.sql)
            results = query_result.rows

            # 结果一致性检查
            consistency = accuracy_guard.verify_result_consistency(
                query_result.columns,
                query_result.rows
            )

            # 7. 解读结果
            explanation = await ai_engine.interpret_results(
                question=req.message,
                sql=sql_result.sql,
                results=results[:10],
                total_rows=query_result.total_rows
            )

            if consistency.warnings:
                explanation += f"\n\n注意：{'; '.join(consistency.warnings)}"

        except Exception as e:
            explanation = f"查询执行失败：{str(e)}"
            sql_result.needs_verification = True

    # 8. 保存助手消息
    execution_metadata = {
        "sql": sql_result.sql,
        "confidence": sql_result.confidence,
        "resolved_time": resolved_time,
        "verification_issues": verification.issues if not verification.is_valid else [],
        "query_result": {
            "columns": query_result.columns if query_result else [],
            "total_rows": query_result.total_rows if query_result else 0,
            "execution_time_ms": query_result.execution_time_ms if query_result else 0
        } if query_result else None
    }

    assistant_message = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        role="assistant",
        content=explanation,
        content_type="text",
        execution_metadata=execution_metadata
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return ChatResponse(
        message=ChatMessageResponse.model_validate(assistant_message),
        sql=sql_result.sql if sql_result.sql else None,
        results=results,
        explanation=explanation,
        needs_verification=sql_result.needs_verification
    )


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """列出对话"""
    conversations = db.query(Conversation).order_by(
        Conversation.updated_at.desc()
    ).offset(skip).limit(limit).all()

    return conversations


# ========== 数据源管理 API ==========

@router.post("/data-sources", response_model=DataSourceResponse)
def create_data_source(
    req: DataSourceCreate,
    db: Session = Depends(get_db)
):
    """创建数据源"""
    # 加密密码
    encrypted_password = encrypt_password(req.password)

    data_source = DataSource(
        id=str(uuid.uuid4()),
        name=req.name,
        type=req.type,
        host=req.host,
        port=req.port,
        database_name=req.database_name,
        username=req.username,
        password_encrypted=encrypted_password,
        connection_options=req.connection_options,
        is_active=True
    )

    db.add(data_source)
    db.commit()
    db.refresh(data_source)

    return data_source


@router.get("/data-sources", response_model=list[DataSourceResponse])
def list_data_sources(
    db: Session = Depends(get_db)
):
    """列出数据源"""
    return db.query(DataSource).filter(DataSource.is_active == True).all()


@router.get("/data-sources/{source_id}", response_model=DataSourceResponse)
def get_data_source(
    source_id: str,
    db: Session = Depends(get_db)
):
    """获取数据源详情"""
    data_source = db.query(DataSource).filter(
        DataSource.id == source_id,
        DataSource.is_active == True
    ).first()

    if not data_source:
        raise HTTPException(status_code=404, detail="数据源不存在")

    return data_source


@router.post("/data-sources/{source_id}/sync-schema")
def sync_data_source_schema(
    source_id: str,
    db: Session = Depends(get_db)
):
    """同步数据源 Schema"""
    data_source = db.query(DataSource).filter(
        DataSource.id == source_id
    ).first()

    if not data_source:
        raise HTTPException(status_code=404, detail="数据源不存在")

    # TODO: 实际连接数据库获取 Schema
    # 这里使用模拟数据
    schema = {
        "tables": [
            {
                "name": "sales",
                "columns": [
                    {"name": "id", "type": "INTEGER", "nullable": False},
                    {"name": "amount", "type": "DECIMAL(10,2)", "nullable": False},
                    {"name": "created_at", "type": "TIMESTAMP", "nullable": False},
                    {"name": "store_id", "type": "INTEGER", "nullable": False},
                ],
                "primary_key": ["id"]
            }
        ]
    }

    data_source.schema_cache = schema
    from datetime import datetime
    data_source.schema_cache_updated_at = datetime.utcnow()
    db.commit()

    return {"status": "success", "tables": len(schema["tables"])}


@router.delete("/data-sources/{source_id}")
def delete_data_source(
    source_id: str,
    db: Session = Depends(get_db)
):
    """删除数据源（软删除）"""
    data_source = db.query(DataSource).filter(
        DataSource.id == source_id
    ).first()

    if not data_source:
        raise HTTPException(status_code=404, detail="数据源不存在")

    data_source.is_active = False
    db.commit()

    return {"status": "success"}
