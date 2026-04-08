from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base, SessionLocal
from app.routers import chat
from app.models import Agent
import uuid

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
                id=uuid.uuid4(),
                code="default_analyst",
                name="通用数据分析师",
                description="基础数据分析智能体，支持各种数据查询和分析任务",
                is_builtin=True,
                is_active=True,
                persona_system_prompt="你是一位专业的数据分析师，擅长将业务问题转化为 SQL 查询，并对数据进行深入解读。",
                persona_expertise=["数据查询", "统计分析", "趋势洞察"],
                thinking_style="先理解问题，再生成查询，最后解读结果",
                output_format="简洁回答，必要时提供数据支撑",
                output_verbosity="concise",
                visualization_preferences=["table", "line_chart"]
            )
            db.add(default_agent)
            db.commit()
            print("Default agent created")
    except Exception as e:
        print(f"Init agent error: {e}")
    finally:
        db.close()


init_default_agent()

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


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}
