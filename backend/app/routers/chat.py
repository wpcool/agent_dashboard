import uuid
import json
import asyncio
from typing import Optional, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text

from app.database import get_db
from app.models import Conversation, Message, DataSource, Agent
from app.schemas.chat import (
    ChatRequest, ChatResponse, ChatMessageResponse,
    ConversationCreate, ConversationResponse, ConversationDetailResponse
)
from app.schemas.data_source import DataSourceCreate, DataSourceUpdate, DataSourceResponse
from app.services.ai_engine import AIEngine
from app.services.time_resolver import TimeResolver
from app.services.query_executor import QueryExecutor
from app.services.accuracy_guard import AccuracyGuard
from app.services.agent_analysis_engine import AgentAnalysisEngine, TaskType
from cryptography.fernet import Fernet
import os
import time

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
    """获取对话详情（包含消息列表）"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    return conversation


@router.get("/conversations/{conversation_id}/messages", response_model=list[ChatMessageResponse])
def get_conversation_messages(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """获取对话的消息列表"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")

    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).all()

    return messages


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
    3. 获取数据源 Schema
    4. 获取 Agent 系统提示词（如有）
    5. 生成 SQL
    6. SQL 完整性检查
    7. 执行查询
    8. 解读结果
    9. 保存助手消息
    10. 返回响应
    """
    # 获取或创建对话
    if req.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == str(req.conversation_id)
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

    # 3. 获取 Schema（使用指定的数据源或默认第一个）
    if req.data_source_id:
        data_source = db.query(DataSource).filter(
            DataSource.id == req.data_source_id,
            DataSource.is_active == True
        ).first()
    else:
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

    # 4. 获取 Agent 信息（如果提供了 agent_id）
    agent = None
    custom_system_prompt = None
    if req.agent_id:
        agent = db.query(Agent).filter(
            Agent.id == str(req.agent_id),
            Agent.is_active == True
        ).first()
        if agent:
            custom_system_prompt = agent.get_system_prompt()
            # 更新对话的当前智能体
            conversation.current_agent_id = str(req.agent_id)

    # 5. 根据是否有 Agent 选择分析模式
    # 如果有 Agent，使用智能多步骤分析；否则使用简单查询
    if agent and req.agent_id:
        # ===== 智能分析模式 =====
        analysis_engine = AgentAnalysisEngine()
        analysis_result = await analysis_engine.analyze(
            question=req.message,
            schema=schema,
            data_source=data_source,
            system_prompt=custom_system_prompt
        )

        # 构建综合分析报告
        final_sql = ""
        all_results = []

        # 收集所有步骤的 SQL 和结果
        for step in analysis_result.plan.steps:
            if step.sql:
                final_sql += f"-- {step.description}\n{step.sql}\n\n"
            if step.result and isinstance(step.result, dict) and "rows" in step.result:
                all_results.extend(step.result["rows"][:5])  # 取前5行

        # 构建回复内容
        explanation = f"""### 📊 分析概览

{analysis_result.plan.user_intent}

### 🔍 分析过程

"""
        for i, step in enumerate(analysis_result.plan.steps, 1):
            explanation += f"**步骤 {i}**: {step.description}\n"
            explanation += f"- 目的: {step.purpose}\n"
            if step.insight:
                explanation += f"- 发现: {step.insight[:200]}...\n"
            explanation += "\n"

        explanation += f"""### 📈 综合结论

{analysis_result.final_analysis}

### 💡 行动建议

"""
        for i, rec in enumerate(analysis_result.recommendations, 1):
            explanation += f"{i}. {rec}\n"

        explanation += f"\n---\n*分析置信度: {analysis_result.confidence:.0%}*"

        # 保存助手消息
        execution_metadata = {
            "analysis_mode": "intelligent",
            "agent_id": str(req.agent_id),
            "agent_name": agent.name,
            "task_type": analysis_result.plan.task_type.value,
            "user_intent": analysis_result.plan.user_intent,
            "analysis_strategy": analysis_result.plan.overall_strategy,
            "steps_completed": analysis_result.steps_completed,
            "total_steps": len(analysis_result.plan.steps),
            "steps_detail": [
                {
                    "description": step.description,
                    "purpose": step.purpose,
                    "sql": step.sql,
                    "insight": step.insight,
                    "validation": {
                        "is_valid": step.validation.is_valid if step.validation else True,
                        "errors": step.validation.errors if step.validation else [],
                        "warnings": step.validation.warnings if step.validation else []
                    } if step.validation else None
                }
                for step in analysis_result.plan.steps
            ],
            "validation_summary": {
                "total_steps": len(analysis_result.plan.steps),
                "steps_with_errors": sum(1 for s in analysis_result.plan.steps if s.validation and not s.validation.is_valid),
                "steps_with_warnings": sum(1 for s in analysis_result.plan.steps if s.validation and s.validation.warnings)
            },
            "sql": final_sql,
            "confidence": analysis_result.confidence,
            "key_insights": analysis_result.data_points,
            "recommendations": analysis_result.recommendations
        }

        assistant_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role="assistant",
            content=explanation,
            content_type="analysis_report",
            execution_metadata=execution_metadata
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)

        return ChatResponse(
            message=ChatMessageResponse.model_validate(assistant_message),
            sql=final_sql if final_sql else None,
            results=all_results if all_results else None,
            explanation=explanation,
            needs_verification=analysis_result.confidence < 0.7
        )

    else:
        # ===== 简单查询模式 =====
        sql_result = await ai_engine.generate_sql(
            question=req.message,
            schema=schema,
            resolved_time=resolved_time,
            custom_system_prompt=custom_system_prompt
        )

        # 6. SQL 完整性检查
        verification = accuracy_guard.verify_sql_completeness(sql_result.sql, req.message)
        if not verification.is_valid:
            sql_result.needs_verification = True
            sql_result.explanation += f"\n\n注意：{', '.join(verification.issues)}"

        # 7. 执行查询（如果需要）
        query_result = None
        results = None
        explanation = sql_result.explanation

        if sql_result.sql and not sql_result.needs_verification:
            try:
                # 判断数据源类型，SQLite 文件（包括示例和上传的）直接查询
                if data_source.type == 'sqlite':
                    # 直接连接 SQLite 数据库执行查询
                    db_path = data_source.host
                    # 确保是绝对路径
                    if not os.path.isabs(db_path):
                        db_path = os.path.abspath(db_path)
                    sample_engine = create_engine(f"sqlite:///{db_path}")
                    with sample_engine.connect() as conn:
                        # 安全检查
                        upper_sql = sql_result.sql.upper().strip()
                        if not upper_sql.startswith('SELECT'):
                            raise ValueError("不安全的 SQL：只允许 SELECT 查询")

                        start_time = time.time()
                        result = conn.execute(text(sql_result.sql))
                        columns = list(result.keys())
                        rows = []
                        for row in result.fetchall():
                            rows.append(dict(zip(columns, row)))
                        execution_time = int((time.time() - start_time) * 1000)

                        query_result = type('QueryResult', (), {
                            'columns': columns,
                            'rows': rows,
                            'total_rows': len(rows),
                            'execution_time_ms': execution_time,
                            'sql': sql_result.sql
                        })()
                        results = rows
                else:
                    # 使用 QueryExecutor 执行（其他数据源）
                    executor = QueryExecutor(db)
                    query_result = executor.execute(sql_result.sql)
                    results = query_result.rows

                # 结果一致性检查
                consistency = accuracy_guard.verify_result_consistency(
                    query_result.columns,
                    query_result.rows
                )

                # 8. 解读结果
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

        # 9. 保存助手消息
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


async def generate_stream_response(
    req: ChatRequest,
    db: Session
) -> AsyncGenerator[str, None]:
    """生成流式响应"""
    import time

    start_time = time.time()

    # 发送开始事件
    yield f"data: {json.dumps({'type': 'start', 'timestamp': start_time}, ensure_ascii=False)}\n\n"

    try:
        # 获取或创建对话
        if req.conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == str(req.conversation_id)
            ).first()
            if not conversation:
                yield f"data: {json.dumps({'type': 'error', 'message': '对话不存在'}, ensure_ascii=False)}\n\n"
                return
        else:
            conversation = Conversation(
                id=str(uuid.uuid4()),
                user_id=str(uuid.uuid4()),
                title=req.message[:20] + "..."
            )
            db.add(conversation)
            db.commit()
            yield f"data: {json.dumps({'type': 'conversation_created', 'conversation_id': conversation.id}, ensure_ascii=False)}\n\n"

        # 保存用户消息
        user_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role="user",
            content=req.message
        )
        db.add(user_message)
        db.commit()

        # 发送用户消息确认
        yield f"data: {json.dumps({'type': 'user_message_saved', 'message_id': user_message.id}, ensure_ascii=False)}\n\n"

        # 初始化分析阶段
        yield f"data: {json.dumps({'type': 'status', 'message': '正在分析问题...'}, ensure_ascii=False)}\n\n"

        # 获取数据源和 Agent
        data_source = db.query(DataSource).filter(DataSource.is_active == True).first()
        if not data_source:
            yield f"data: {json.dumps({'type': 'error', 'message': '请先配置数据源'}, ensure_ascii=False)}\n\n"
            return

        agent = None
        if req.agent_id:
            agent = db.query(Agent).filter(
                Agent.id == str(req.agent_id),
                Agent.is_active == True
            ).first()

        schema = data_source.schema_cache or {"tables": []}

        # 流式分析过程
        if agent and req.agent_id:
            # 智能分析模式 - 流式展示步骤
            yield f"data: {json.dumps({'type': 'mode', 'mode': 'intelligent', 'agent_name': agent.name}, ensure_ascii=False)}\n\n"

            analysis_engine = AgentAnalysisEngine()

            # 创建分析计划
            yield f"data: {json.dumps({'type': 'step_start', 'step': 'planning', 'message': '正在制定分析计划...'}, ensure_ascii=False)}\n\n"

            plan = await analysis_engine._create_analysis_plan(
                req.message, schema, agent.get_system_prompt() if agent else None
            )

            yield f"data: {json.dumps({'type': 'plan_complete', 'task_type': plan.task_type.value, 'user_intent': plan.user_intent, 'total_steps': len(plan.steps)}, ensure_ascii=False)}\n\n"

            # 执行每个步骤并流式输出
            for i, step in enumerate(plan.steps):
                step_num = i + 1
                yield f"data: {json.dumps({'type': 'step_start', 'step_number': step_num, 'total_steps': len(plan.steps), 'description': step.description}, ensure_ascii=False)}\n\n"

                # 生成/验证 SQL
                if not step.sql:
                    yield f"data: {json.dumps({'type': 'step_progress', 'step_number': step_num, 'message': '正在生成查询...'}, ensure_ascii=False)}\n\n"
                    step.sql = await analysis_engine._generate_step_sql(step, schema, plan)

                # Schema 验证
                validation = analysis_engine._validate_sql_schema(step.sql, schema)
                if not validation.is_valid:
                    yield f"data: {json.dumps({'type': 'step_progress', 'step_number': step_num, 'message': '正在修正查询...', 'warnings': validation.errors}, ensure_ascii=False)}\n\n"
                    step.sql = await analysis_engine._fix_sql_schema(step.sql, schema, validation.errors, plan)

                # 执行查询
                yield f"data: {json.dumps({'type': 'step_progress', 'step_number': step_num, 'message': '正在执行查询...'}, ensure_ascii=False)}\n\n"

                try:
                    if data_source.type == 'sqlite':
                        step.result = analysis_engine._execute_sqlite_query(step.sql, data_source.host)
                    else:
                        step.result = analysis_engine._execute_db_query(step.sql, data_source)

                    yield f"data: {json.dumps({'type': 'step_data', 'step_number': step_num, 'row_count': step.result.get('total_rows', 0)}, ensure_ascii=False)}\n\n"

                except Exception as e:
                    yield f"data: {json.dumps({'type': 'step_error', 'step_number': step_num, 'error': str(e)}, ensure_ascii=False)}\n\n"
                    continue

                # 分析结果
                yield f"data: {json.dumps({'type': 'step_progress', 'step_number': step_num, 'message': '正在分析结果...'}, ensure_ascii=False)}\n\n"
                step.insight = await analysis_engine._analyze_step_result(step, plan)

                yield f"data: {json.dumps({'type': 'step_complete', 'step_number': step_num, 'insight': step.insight[:200]}, ensure_ascii=False)}\n\n"

            # 综合分析
            yield f"data: {json.dumps({'type': 'status', 'message': '正在生成综合分析...'}, ensure_ascii=False)}\n\n"
            final_analysis = await analysis_engine._synthesize_analysis(plan, req.message)

            # 保存助手消息
            assistant_message = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation.id,
                role="assistant",
                content=final_analysis["analysis"],
                content_type="analysis_report",
                execution_metadata={
                    "analysis_mode": "intelligent",
                    "agent_id": str(req.agent_id) if req.agent_id else None,
                    "agent_name": agent.name if agent else None,
                    "task_type": plan.task_type.value,
                    "steps_completed": len([s for s in plan.steps if s.result]),
                    "total_steps": len(plan.steps),
                    "steps_detail": [{"description": s.description, "purpose": s.purpose, "sql": s.sql, "insight": s.insight} for s in plan.steps],
                    "recommendations": final_analysis["recommendations"],
                    "confidence": final_analysis["confidence"]
                }
            )
            db.add(assistant_message)
            db.commit()

            # 发送最终结果
            yield f"data: {json.dumps({'type': 'complete', 'message': final_analysis["analysis"], 'recommendations': final_analysis["recommendations"], 'confidence': final_analysis["confidence"], 'execution_time': time.time() - start_time}, ensure_ascii=False)}\n\n"

        else:
            # 简单查询模式
            yield f"data: {json.dumps({'type': 'mode', 'mode': 'simple'}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'status', 'message': '正在生成SQL...'}, ensure_ascii=False)}\n\n"

            ai_engine = AIEngine()
            sql_result = await ai_engine.generate_sql(
                question=req.message,
                schema=schema,
                custom_system_prompt=agent.get_system_prompt() if agent else None
            )

            yield f"data: {json.dumps({'type': 'sql_generated', 'sql': sql_result.sql}, ensure_ascii=False)}\n\n"

            # 执行查询
            results = None
            if sql_result.sql:
                try:
                    if data_source.type == 'sqlite':
                        db_path = data_source.host
                        if not os.path.isabs(db_path):
                            db_path = os.path.abspath(db_path)
                        engine = create_engine(f"sqlite:///{db_path}")
                        with engine.connect() as conn:
                            result = conn.execute(text(sql_result.sql))
                            columns = list(result.keys())
                            rows = [dict(zip(columns, row)) for row in result.fetchall()]
                            results = rows
                            yield f"data: {json.dumps({'type': 'data', 'row_count': len(rows), 'columns': columns}, ensure_ascii=False)}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'status', 'message': '执行查询...'}, ensure_ascii=False)}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

            # 解读结果
            yield f"data: {json.dumps({'type': 'status', 'message': '正在解读结果...'}, ensure_ascii=False)}\n\n"
            explanation = sql_result.explanation
            if results:
                explanation = await ai_engine.interpret_results(
                    req.message, sql_result.sql, results[:10], len(results)
                )

            # 保存消息
            assistant_message = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation.id,
                role="assistant",
                content=explanation,
                content_type="text",
                execution_metadata={"sql": sql_result.sql}
            )
            db.add(assistant_message)
            db.commit()

            yield f"data: {json.dumps({'type': 'complete', 'message': explanation, 'sql': sql_result.sql, 'results': results[:10] if results else None, 'execution_time': time.time() - start_time}, ensure_ascii=False)}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    finally:
        yield f"data: {json.dumps({'type': 'end'}, ensure_ascii=False)}\n\n"


@router.post("/chat/stream")
async def chat_stream(
    req: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    流式对话接口 - 使用 SSE (Server-Sent Events)
    实时返回分析进度和结果
    """
    return StreamingResponse(
        generate_stream_response(req, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
        }
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
    """
    删除数据源（软删除）
    - 对于上传的 SQLite 文件，同时删除数据库文件
    """
    import os
    data_source = db.query(DataSource).filter(
        DataSource.id == source_id
    ).first()

    if not data_source:
        raise HTTPException(status_code=404, detail="数据源不存在")

    # 对于上传的 SQLite 文件，删除实际数据库文件
    if data_source.type == "sqlite":
        try:
            if data_source.connection_options.get("is_uploaded"):
                db_path = data_source.host
                if os.path.exists(db_path):
                    os.remove(db_path)
                    print(f"Deleted database file: {db_path}")
        except Exception as e:
            print(f"Failed to delete database file: {e}")

    data_source.is_active = False
    db.commit()

    return {"success": True, "message": "数据源已删除"}
