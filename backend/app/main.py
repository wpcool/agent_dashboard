from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base, SessionLocal
from app.routers import chat, upload, agents
from app.models import Agent, DataSource
import uuid
import json
import os

# 创建数据库表
Base.metadata.create_all(bind=engine)


# 初始化默认智能体
def init_default_agent():
    db = SessionLocal()
    try:
        # 检查是否已存在默认智能体
        existing = db.query(Agent).filter(Agent.code == "default_analyst").first()
        if not existing:
            default_agent = Agent(
                id=str(uuid.uuid4()),
                code="default_analyst",
                name="通用数据分析师",
                description="基础数据分析智能体，支持各种数据查询和分析任务",
                is_builtin=True,
                is_active=True,
                persona_system_prompt="你是一位专业的数据分析师，擅长将业务问题转化为 SQL 查询，并对数据进行深入解读。",
                persona_expertise=json.dumps(["数据查询", "统计分析", "趋势洞察"]),
                thinking_style="先理解问题，再生成查询，最后解读结果",
                output_format="简洁回答，必要时提供数据支撑",
                output_verbosity="concise",
                visualization_preferences=json.dumps(["table", "line_chart"])
            )
            db.add(default_agent)
            db.commit()
            print("Default agent created")
    except Exception as e:
        print(f"Init agent error: {e}")
    finally:
        db.close()


# 初始化示例数据源
def init_sample_data_source():
    from app.services.sample_data import generate_sample_database, get_sample_schema

    db = SessionLocal()
    try:
        # 检查是否已存在示例数据源
        existing = db.query(DataSource).filter(DataSource.name == "示例销售数据").first()
        if not existing:
            # 生成示例数据库
            sample_db_path = os.path.join(os.path.dirname(__file__), "..", "sample_data.db")
            sample_db_path = os.path.abspath(sample_db_path)

            if not os.path.exists(sample_db_path):
                generate_sample_database(sample_db_path)
                print(f"Sample database created at: {sample_db_path}")

            # 创建数据源记录
            sample_schema = get_sample_schema()
            data_source = DataSource(
                id=str(uuid.uuid4()),
                name="示例销售数据",
                type="sqlite",
                host=sample_db_path,
                port=0,
                database_name="sample_data",
                username="",
                password_encrypted="",
                connection_options={"is_sample": True},
                schema_cache=sample_schema,
                is_active=True
            )
            db.add(data_source)
            db.commit()
            print("Sample data source created")
    except Exception as e:
        print(f"Init sample data source error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


init_default_agent()
init_sample_data_source()

# 初始化 Phase 2 技能和智能体
def init_phase2_agents():
    try:
        from app.services.agent_initializer import init_skills_and_agents
        init_skills_and_agents()
    except Exception as e:
        print(f"Phase 2 init warning: {e}")

init_phase2_agents()

app = FastAPI(
    title="AskTable AI API",
    description="AI-powered data analysis platform",
    version="0.1.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
app.include_router(agents.router, prefix="/api/v1", tags=["agents"])


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}
