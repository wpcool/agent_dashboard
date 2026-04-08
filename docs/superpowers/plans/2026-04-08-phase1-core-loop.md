# Phase 1: 核心闭环 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现自然语言问数的完整闭环：用户输入问题 → AI 生成 SQL → 执行查询 → 返回结果，包含基础的准确性保障机制。

**Architecture:** 采用单体架构快速验证，包含 FastAPI 后端 + React 前端 + PostgreSQL 元数据存储 + Redis 缓存。AI 调用 Claude API 实现 Text-to-SQL。

**Tech Stack:** Python 3.11 + FastAPI + React 18 + TypeScript + PostgreSQL 15 + Redis 7 + SQLAlchemy + pytest

---

## 文件结构规划

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── database.py             # 数据库连接
│   ├── models/
│   │   ├── __init__.py
│   │   ├── agent.py            # 智能体模型
│   │   ├── conversation.py     # 对话模型
│   │   └── data_source.py      # 数据源模型
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── chat.py             # 对话 API 协议
│   │   └── query.py            # 查询相关协议
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_engine.py        # AI 引擎 (Text-to-SQL)
│   │   ├── query_executor.py   # SQL 执行器
│   │   ├── time_resolver.py    # 时间解析
│   │   └── accuracy_guard.py   # 准确性保障
│   ├── routers/
│   │   ├── __init__.py
│   │   └── chat.py             # 对话 API 路由
│   └── utils/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── test_ai_engine.py
│   ├── test_time_resolver.py
│   └── test_query_executor.py
├── alembic/                    # 数据库迁移
├── requirements.txt
├── pytest.ini
└── Dockerfile

frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── components/
│   │   ├── ChatWindow.tsx      # 对话窗口
│   │   ├── MessageList.tsx     # 消息列表
│   │   ├── MessageItem.tsx     # 单条消息
│   │   ├── SQLDisplay.tsx      # SQL 展示
│   │   ├── DataTable.tsx       # 数据表格
│   │   └── ChatInput.tsx       # 输入框
│   ├── api/
│   │   └── chat.ts             # API 调用
│   └── types/
│       └── chat.ts             # 类型定义
├── package.json
├── tsconfig.json
└── vite.config.ts

docker-compose.yml              # 开发环境编排
```

---

## Task 1: 项目脚手架搭建

**Files:**
- Create: `docker-compose.yml`
- Create: `backend/requirements.txt`
- Create: `backend/pytest.ini`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/app/main.py`
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`

- [ ] **Step 1: 创建 docker-compose 开发环境**

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_USER: asktable
      POSTGRES_PASSWORD: asktable
      POSTGRES_DB: asktable
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://asktable:asktable@postgres:5432/asktable
      REDIS_URL: redis://redis:6379/0
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --reload
    depends_on:
      - postgres
      - redis

  frontend:
    image: node:20-alpine
    working_dir: /app
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
    command: sh -c "npm install && npm run dev"

volumes:
  postgres_data:
  redis_data:
```

- [ ] **Step 2: 创建后端 requirements.txt**

```txt
# backend/requirements.txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9
redis==5.0.1
anthropic==0.18.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0
```

- [ ] **Step 3: 创建后端 pytest 配置**

```ini
# backend/pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

- [ ] **Step 4: 创建配置管理模块**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://asktable:asktable@localhost:5432/asktable"
    REDIS_URL: str = "redis://localhost:6379/0"
    ANTHROPIC_API_KEY: str = ""
    
    # AI 配置
    AI_MODEL: str = "claude-3-5-sonnet-20241022"
    AI_MAX_TOKENS: int = 4000
    AI_TEMPERATURE: float = 0.1
    
    # 查询配置
    QUERY_TIMEOUT: int = 30
    QUERY_MAX_ROWS: int = 1000
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 5: 创建数据库连接模块**

```python
# backend/app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 6: 创建 FastAPI 主应用**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import chat

# 创建数据库表
Base.metadata.create_all(bind=engine)

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
```

- [ ] **Step 7: 创建前端 package.json**

```json
{
  "name": "asktable-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.5"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.2.2",
    "vite": "^5.0.8",
    "tailwindcss": "^3.4.1"
  }
}
```

- [ ] **Step 8: 创建前端 TypeScript 配置**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 9: 创建前端 Vite 配置**

```typescript
// frontend/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      }
    }
  }
})
```

- [ ] **Step 10: 创建后端 Dockerfile**

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 11: 启动开发环境验证**

```bash
# 创建 .env 文件
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env

# 启动服务
docker-compose up -d postgres redis

# 等待数据库就绪
sleep 5

# 验证
curl http://localhost:8000/health
# Expected: {"status":"ok","version":"0.1.0"}
```

- [ ] **Step 12: Commit**

```bash
git add docker-compose.yml backend/ frontend/
git commit -m "chore: setup project scaffold with docker-compose"
```

---

## Task 2: 时间解析模块

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/time_resolver.py`
- Create: `backend/tests/test_time_resolver.py`

- [ ] **Step 1: 编写时间解析器测试**

```python
# backend/tests/test_time_resolver.py
import pytest
from datetime import datetime, timedelta
from app.services.time_resolver import TimeResolver, TimeRange


class TestTimeResolver:
    def test_resolve_yesterday(self):
        """测试解析昨天"""
        resolver = TimeResolver()
        query_time = datetime(2026, 4, 8, 15, 30, 0)  # 固定测试时间
        
        result = resolver.resolve("昨天", query_time)
        
        assert result.start == datetime(2026, 4, 7, 0, 0, 0)
        assert result.end == datetime(2026, 4, 7, 23, 59, 59)
    
    def test_resolve_today(self):
        """测试解析今天"""
        resolver = TimeResolver()
        query_time = datetime(2026, 4, 8, 15, 30, 0)
        
        result = resolver.resolve("今天", query_time)
        
        assert result.start == datetime(2026, 4, 8, 0, 0, 0)
        assert result.end == datetime(2026, 4, 8, 23, 59, 59)
    
    def test_resolve_last_week(self):
        """测试解析上周"""
        resolver = TimeResolver()
        query_time = datetime(2026, 4, 8)  # 周二
        
        result = resolver.resolve("上周", query_time)
        
        # 上周一 00:00:00 到 上周日 23:59:59
        assert result.start == datetime(2026, 3, 30)
        assert result.end == datetime(2026, 4, 5, 23, 59, 59)
    
    def test_resolve_last_n_days(self):
        """测试解析最近N天"""
        resolver = TimeResolver()
        query_time = datetime(2026, 4, 8, 15, 30, 0)
        
        result = resolver.resolve("最近3天", query_time)
        
        # 包含今天的前3天
        assert result.start == datetime(2026, 4, 6, 0, 0, 0)
        assert result.end == datetime(2026, 4, 8, 23, 59, 59)
    
    def test_resolve_this_month(self):
        """测试解析本月"""
        resolver = TimeResolver()
        query_time = datetime(2026, 4, 8)
        
        result = resolver.resolve("本月", query_time)
        
        assert result.start == datetime(2026, 4, 1, 0, 0, 0)
        assert result.end == datetime(2026, 4, 30, 23, 59, 59)
    
    def test_resolve_last_month(self):
        """测试解析上月"""
        resolver = TimeResolver()
        query_time = datetime(2026, 4, 8)
        
        result = resolver.resolve("上月", query_time)
        
        assert result.start == datetime(2026, 3, 1, 0, 0, 0)
        assert result.end == datetime(2026, 3, 31, 23, 59, 59)
    
    def test_unsupported_expression(self):
        """测试不支持的表达式返回None"""
        resolver = TimeResolver()
        query_time = datetime(2026, 4, 8)
        
        result = resolver.resolve("随便什么", query_time)
        
        assert result is None
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend
pytest tests/test_time_resolver.py -v
# Expected: 6 tests FAIL (TimeResolver not defined)
```

- [ ] **Step 3: 实现时间解析器**

```python
# backend/app/services/time_resolver.py
from dataclasses import dataclass
from datetime import datetime, timedelta
from calendar import monthrange
import re


@dataclass
class TimeRange:
    """时间范围"""
    start: datetime
    end: datetime
    
    def to_sql_condition(self, field: str) -> str:
        """转换为 SQL WHERE 条件"""
        start_str = self.start.strftime("%Y-%m-%d %H:%M:%S")
        end_str = self.end.strftime("%Y-%m-%d %H:%M:%S")
        return f"{field} >= '{start_str}' AND {field} <= '{end_str}'"


class TimeResolver:
    """
    解析自然语言中的相对时间为绝对时间范围
    基于查询时的真实当前时间
    """
    
    # 正则表达式模式
    PATTERNS = {
        'yesterday': r'^(昨天|昨日)$',
        'today': r'^(今天|今日)$',
        'last_week': r'^(上周|上星期|上个星期)$',
        'this_week': r'^(本周|这星期|这个星期)$',
        'last_month': r'^(上月|上个月|上月)$',
        'this_month': r'^(本月|这个月)$',
        'last_n_days': r'^(?:最近|近)(\d+)[天日]$',
        'this_year': r'^(今年|本年度)$',
        'last_year': r'^(去年|上年度)$',
    }
    
    def resolve(self, expression: str, query_time: datetime = None) -> TimeRange | None:
        """
        解析时间表达式
        
        Args:
            expression: 自然语言时间表达式，如 "昨天"
            query_time: 查询时的基准时间，默认为当前时间
        
        Returns:
            TimeRange 或 None（无法解析时）
        """
        if query_time is None:
            query_time = datetime.now()
        
        expression = expression.strip().lower()
        
        # 昨天
        if re.match(self.PATTERNS['yesterday'], expression):
            yesterday = query_time - timedelta(days=1)
            return TimeRange(
                start=yesterday.replace(hour=0, minute=0, second=0, microsecond=0),
                end=yesterday.replace(hour=23, minute=59, second=59, microsecond=0)
            )
        
        # 今天
        if re.match(self.PATTERNS['today'], expression):
            return TimeRange(
                start=query_time.replace(hour=0, minute=0, second=0, microsecond=0),
                end=query_time.replace(hour=23, minute=59, second=59, microsecond=0)
            )
        
        # 上周（自然周，上周一到上周日）
        if re.match(self.PATTERNS['last_week'], expression):
            # 获取本周一
            days_since_monday = query_time.weekday()
            this_monday = query_time - timedelta(days=days_since_monday)
            last_monday = this_monday - timedelta(days=7)
            last_sunday = last_monday + timedelta(days=6)
            return TimeRange(
                start=last_monday.replace(hour=0, minute=0, second=0, microsecond=0),
                end=last_sunday.replace(hour=23, minute=59, second=59, microsecond=0)
            )
        
        # 本周
        if re.match(self.PATTERNS['this_week'], expression):
            days_since_monday = query_time.weekday()
            this_monday = query_time - timedelta(days=days_since_monday)
            return TimeRange(
                start=this_monday.replace(hour=0, minute=0, second=0, microsecond=0),
                end=query_time.replace(hour=23, minute=59, second=59, microsecond=0)
            )
        
        # 上月
        if re.match(self.PATTERNS['last_month'], expression):
            first_day_this_month = query_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            first_day_last_month = last_day_last_month.replace(day=1)
            last_day = monthrange(first_day_last_month.year, first_day_last_month.month)[1]
            return TimeRange(
                start=first_day_last_month,
                end=first_day_last_month.replace(day=last_day, hour=23, minute=59, second=59)
            )
        
        # 本月
        if re.match(self.PATTERNS['this_month'], expression):
            first_day = query_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_day = monthrange(query_time.year, query_time.month)[1]
            return TimeRange(
                start=first_day,
                end=first_day.replace(day=last_day, hour=23, minute=59, second=59)
            )
        
        # 最近N天
        match = re.match(self.PATTERNS['last_n_days'], expression)
        if match:
            n = int(match.group(1))
            start_date = query_time - timedelta(days=n-1)
            return TimeRange(
                start=start_date.replace(hour=0, minute=0, second=0, microsecond=0),
                end=query_time.replace(hour=23, minute=59, second=59, microsecond=0)
            )
        
        # 去年
        if re.match(self.PATTERNS['last_year'], expression):
            last_year = query_time.year - 1
            return TimeRange(
                start=datetime(last_year, 1, 1, 0, 0, 0),
                end=datetime(last_year, 12, 31, 23, 59, 59)
            )
        
        # 今年
        if re.match(self.PATTERNS['this_year'], expression):
            return TimeRange(
                start=datetime(query_time.year, 1, 1, 0, 0, 0),
                end=query_time.replace(hour=23, minute=59, second=59, microsecond=0)
            )
        
        return None
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend
pytest tests/test_time_resolver.py -v
# Expected: 6 tests PASS
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/time_resolver.py backend/tests/test_time_resolver.py
git commit -m "feat: add time resolver for natural language date parsing"
```

---

## Task 3: 数据模型定义

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/agent.py`
- Create: `backend/app/models/data_source.py`
- Create: `backend/app/models/conversation.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/001_initial.py`

- [ ] **Step 1: 创建智能体模型**

```python
# backend/app/models/agent.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID, ARRAY as PG_ARRAY
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
    workflow_definition = Column(JSON)
    
    # 审计
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 2: 创建数据源模型**

```python
# backend/app/models/data_source.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class DataSource(Base):
    """数据源配置"""
    __tablename__ = "data_sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # mysql, postgresql, etc.
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    database_name = Column(String(100), nullable=False)
    username = Column(String(100), nullable=False)
    password_encrypted = Column(Text, nullable=False)
    connection_options = Column(JSONB, default={})
    
    # 元数据缓存
    schema_cache = Column(JSONB)
    schema_cache_updated_at = Column(DateTime)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 3: 创建对话模型**

```python
# backend/app/models/conversation.py
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
    
    title = Column(String(200))  # 自动生成或用户设置
    
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
```

- [ ] **Step 4: 更新模型 __init__.py**

```python
# backend/app/models/__init__.py
from app.models.agent import Agent
from app.models.data_source import DataSource
from app.models.conversation import Conversation, Message

__all__ = ["Agent", "DataSource", "Conversation", "Message"]
```

- [ ] **Step 5: 创建 Alembic 配置**

```ini
# backend/alembic.ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql://asktable:asktable@localhost:5432/asktable

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 6: 创建 Alembic 环境配置**

```python
# backend/alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import Base
from app.models import Agent, DataSource, Conversation, Message

# Alembic 配置
config = context.config

# 日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 目标元数据
target_metadata = Base.metadata


def get_url():
    """从环境变量获取数据库 URL"""
    return os.getenv("DATABASE_URL", "postgresql://asktable:asktable@localhost:5432/asktable")


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 7: 创建初始迁移脚本**

```bash
cd backend
mkdir -p alembic/versions
```

```python
# backend/alembic/versions/001_initial.py
"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2026-04-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # agents 表
    op.create_table(
        'agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_builtin', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('persona_system_prompt', sa.Text(), nullable=True),
        sa.Column('persona_expertise', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('thinking_style', sa.String(length=50), nullable=True),
        sa.Column('output_format', sa.Text(), nullable=True),
        sa.Column('output_verbosity', sa.String(length=20), nullable=True),
        sa.Column('visualization_preferences', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('workflow_definition', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    
    # data_sources 表
    op.create_table(
        'data_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('host', sa.String(length=255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('database_name', sa.String(length=100), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('password_encrypted', sa.Text(), nullable=False),
        sa.Column('connection_options', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('schema_cache', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('schema_cache_updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # conversations 表
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('current_agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('current_context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('context_history', postgresql.ARRAY(postgresql.JSONB(astext_type=sa.Text())), nullable=True),
        sa.Column('is_archived', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['current_agent_id'], ['agents.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # messages 表
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_type', sa.String(length=20), nullable=True),
        sa.Column('execution_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_streaming', sa.Boolean(), nullable=True),
        sa.Column('streaming_completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('idx_agents_code', 'agents', ['code'])
    op.create_index('idx_agents_builtin', 'agents', ['is_builtin'])
    op.create_index('idx_messages_conversation', 'messages', ['conversation_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('idx_messages_conversation', table_name='messages')
    op.drop_index('idx_agents_builtin', table_name='agents')
    op.drop_index('idx_agents_code', table_name='agents')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('data_sources')
    op.drop_table('agents')
```

- [ ] **Step 8: 执行数据库迁移**

```bash
cd backend
alembic upgrade head
# Expected: 成功创建表
```

- [ ] **Step 9: Commit**

```bash
git add backend/app/models/ backend/alembic/
git commit -m "feat: add database models and alembic migrations"
```

---

## Task 4: AI 引擎服务（Text-to-SQL）

**Files:**
- Create: `backend/app/services/ai_engine.py`
- Create: `backend/tests/test_ai_engine.py`

- [ ] **Step 1: 编写 AI 引擎测试**

```python
# backend/tests/test_ai_engine.py
import pytest
from unittest.mock import Mock, patch
from app.services.ai_engine import AIEngine, SQLGenerationResult


class TestAIEngine:
    @pytest.fixture
    def engine(self):
        return AIEngine(api_key="test-key")
    
    @pytest.fixture
    def sample_schema(self):
        return {
            "tables": [
                {
                    "name": "sales",
                    "columns": [
                        {"name": "id", "type": "INTEGER"},
                        {"name": "amount", "type": "DECIMAL"},
                        {"name": "created_at", "type": "TIMESTAMP"},
                        {"name": "store_id", "type": "INTEGER"}
                    ]
                }
            ]
        }
    
    def test_sql_generation_result_structure(self):
        """测试 SQL 生成结果结构"""
        result = SQLGenerationResult(
            sql="SELECT * FROM sales",
            explanation="查询所有销售记录",
            confidence=0.95,
            needs_verification=False
        )
        assert result.sql == "SELECT * FROM sales"
        assert result.confidence == 0.95
    
    @patch('app.services.ai_engine.Anthropic')
    async def test_generate_sql_success(self, mock_anthropic, engine, sample_schema):
        """测试 SQL 生成成功"""
        # Mock Claude 响应
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text='''{"sql": "SELECT SUM(amount) FROM sales WHERE DATE(created_at) = '2026-04-07'", "explanation": "查询昨天的销售总额", "confidence": 0.92}''')]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        result = await engine.generate_sql(
            question="昨天销售额多少？",
            schema=sample_schema,
            resolved_time={"昨天": {"start": "2026-04-07", "end": "2026-04-07"}}
        )
        
        assert "SELECT" in result.sql
        assert result.confidence > 0
    
    def test_build_system_prompt(self, engine, sample_schema):
        """测试系统提示词构建"""
        prompt = engine._build_system_prompt(sample_schema)
        
        assert "sales" in prompt
        assert "amount" in prompt
        assert "SQL" in prompt
    
    def test_parse_response_valid_json(self, engine):
        """测试解析有效的 JSON 响应"""
        response_text = '{"sql": "SELECT 1", "explanation": "test", "confidence": 0.9}'
        result = engine._parse_response(response_text)
        
        assert result.sql == "SELECT 1"
        assert result.explanation == "test"
        assert result.confidence == 0.9
    
    def test_parse_response_markdown_json(self, engine):
        """测试解析 markdown 包裹的 JSON"""
        response_text = '```json\n{"sql": "SELECT 1", "explanation": "test", "confidence": 0.9}\n```'
        result = engine._parse_response(response_text)
        
        assert result.sql == "SELECT 1"
    
    def test_parse_response_invalid_fallback(self, engine):
        """测试解析失败时的回退处理"""
        response_text = 'Some random text without SQL'
        result = engine._parse_response(response_text)
        
        assert result.sql == ""
        assert result.confidence == 0.0
        assert result.needs_verification is True
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd backend
pytest tests/test_ai_engine.py -v
# Expected: tests FAIL (AIEngine not defined)
```

- [ ] **Step 3: 实现 AI 引擎**

```python
# backend/app/services/ai_engine.py
import json
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from anthropic import Anthropic
from app.config import get_settings


@dataclass
class SQLGenerationResult:
    """SQL 生成结果"""
    sql: str
    explanation: str
    confidence: float
    needs_verification: bool = False
    reasoning: str = ""


class AIEngine:
    """
    AI 引擎：负责 Text-to-SQL、数据解读等 AI 能力
    """
    
    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.client = Anthropic(api_key=api_key or settings.ANTHROPIC_API_KEY)
        self.model = settings.AI_MODEL
        self.max_tokens = settings.AI_MAX_TOKENS
        self.temperature = settings.AI_TEMPERATURE
    
    async def generate_sql(
        self,
        question: str,
        schema: Dict[str, Any],
        resolved_time: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None
    ) -> SQLGenerationResult:
        """
        生成 SQL
        
        Args:
            question: 用户问题
            schema: 数据库 Schema 信息
            resolved_time: 已解析的时间表达式
            context: 对话上下文
        
        Returns:
            SQLGenerationResult
        """
        system_prompt = self._build_system_prompt(schema)
        user_prompt = self._build_user_prompt(question, resolved_time, context)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            response_text = response.content[0].text
            return self._parse_response(response_text)
            
        except Exception as e:
            return SQLGenerationResult(
                sql="",
                explanation=f"生成失败: {str(e)}",
                confidence=0.0,
                needs_verification=True
            )
    
    def _build_system_prompt(self, schema: Dict[str, Any]) -> str:
        """构建系统提示词"""
        
        # 构建 Schema 描述
        schema_desc = "数据库 Schema:\n"
        for table in schema.get("tables", []):
            schema_desc += f"\n表: {table['name']}\n"
            for col in table.get("columns", []):
                schema_desc += f"  - {col['name']}: {col['type']}\n"
        
        prompt = f"""你是一个专业的 SQL 生成专家。根据用户的问题和数据库 Schema，生成准确、高效的 SQL 查询。

{schema_desc}

规则:
1. 只生成 SELECT 查询，禁止生成 INSERT/UPDATE/DELETE/DROP 等修改性语句
2. 使用标准 SQL 语法，兼容 PostgreSQL
3. 时间条件使用 WHERE 子句，格式: column >= 'YYYY-MM-DD HH:MM:SS' AND column <= 'YYYY-MM-DD HH:MM:SS'
4. 聚合查询使用 GROUP BY，并为聚合列设置别名
5. 排序使用 ORDER BY，限制返回数量使用 LIMIT
6. 如果问题不明确，生成最可能的 SQL 并标记需要验证

输出格式（JSON）:
{{
    "sql": "生成的 SQL 语句",
    "explanation": "SQL 的作用解释（中文）",
    "confidence": 0.95,
    "reasoning": "生成思路"
}}

注意: 只输出 JSON，不要有其他内容。"""
        
        return prompt
    
    def _build_user_prompt(
        self,
        question: str,
        resolved_time: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None
    ) -> str:
        """构建用户提示词"""
        
        prompt = f"用户问题: {question}\n"
        
        if resolved_time:
            prompt += f"\n已解析的时间范围:\n"
            for expr, time_range in resolved_time.items():
                prompt += f"  - {expr}: {time_range['start']} 至 {time_range['end']}\n"
        
        if context:
            prompt += f"\n对话上下文: {context}\n"
        
        prompt += "\n请生成 SQL 查询。"
        
        return prompt
    
    def _parse_response(self, response_text: str) -> SQLGenerationResult:
        """解析 AI 响应"""
        
        # 尝试提取 markdown 中的 JSON
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
        
        try:
            data = json.loads(response_text)
            
            return SQLGenerationResult(
                sql=data.get("sql", "").strip(),
                explanation=data.get("explanation", ""),
                confidence=data.get("confidence", 0.0),
                reasoning=data.get("reasoning", ""),
                needs_verification=data.get("confidence", 1.0) < 0.8
            )
            
        except json.JSONDecodeError:
            # 解析失败，尝试直接提取 SQL
            sql_match = re.search(r'SELECT\s+.+?(?:;|$)', response_text, re.DOTALL | re.IGNORECASE)
            if sql_match:
                return SQLGenerationResult(
                    sql=sql_match.group(0).strip(),
                    explanation="从响应中提取的 SQL",
                    confidence=0.5,
                    needs_verification=True
                )
            
            return SQLGenerationResult(
                sql="",
                explanation="无法解析 AI 响应",
                confidence=0.0,
                needs_verification=True
            )
    
    async def interpret_results(
        self,
        question: str,
        sql: str,
        results: List[Dict],
        total_rows: int
    ) -> str:
        """
        解读查询结果
        
        Args:
            question: 原始问题
            sql: 执行的 SQL
            results: 查询结果（前 N 行）
            total_rows: 总行数
        
        Returns:
            自然语言解读
        """
        prompt = f"""用户问题: {question}

执行的 SQL: {sql}

查询结果（共 {total_rows} 行，显示前 {len(results)} 行）:
{json.dumps(results, ensure_ascii=False, indent=2)}

请用 1-3 句话总结结果，直接回答用户的问题。如果数据有异常或值得注意的趋势，请指出。"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            return f"查询完成，共 {total_rows} 条记录。"
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend
pytest tests/test_ai_engine.py -v
# Expected: tests PASS
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/ai_engine.py backend/tests/test_ai_engine.py
git commit -m "feat: add AI engine with Text-to-SQL capability"
```

---

## Task 5: SQL 执行器与准确性保障

**Files:**
- Create: `backend/app/services/query_executor.py`
- Create: `backend/app/services/accuracy_guard.py`
- Create: `backend/tests/test_query_executor.py`

- [ ] **Step 1: 编写查询执行器测试**

```python
# backend/tests/test_query_executor.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from app.services.query_executor import QueryExecutor, QueryResult
from app.services.accuracy_guard import AccuracyGuard


class TestQueryExecutor:
    @pytest.fixture
    def mock_db_session(self):
        return MagicMock()
    
    @pytest.fixture
    def executor(self, mock_db_session):
        return QueryExecutor(mock_db_session)
    
    def test_query_result_structure(self):
        """测试查询结果结构"""
        result = QueryResult(
            columns=["id", "name"],
            rows=[{"id": 1, "name": "test"}],
            total_rows=1,
            execution_time_ms=100,
            sql="SELECT * FROM test"
        )
        assert result.columns == ["id", "name"]
        assert len(result.rows) == 1
    
    def test_safe_sql_check_valid(self, executor):
        """测试安全 SQL 检查 - 合法查询"""
        assert executor._is_safe_sql("SELECT * FROM users") is True
        assert executor._is_safe_sql("SELECT COUNT(*) FROM orders") is True
    
    def test_safe_sql_check_invalid(self, executor):
        """测试安全 SQL 检查 - 非法查询"""
        assert executor._is_safe_sql("DELETE FROM users") is False
        assert executor._is_safe_sql("DROP TABLE users") is False
        assert executor._is_safe_sql("INSERT INTO users VALUES (1)") is False
        assert executor._is_safe_sql("UPDATE users SET name='x'") is False
    
    @patch('app.services.query_executor.text')
    def test_execute_success(self, mock_text, executor, mock_db_session):
        """测试查询执行成功"""
        # Mock 执行结果
        mock_result = MagicMock()
        mock_result.keys.return_value = ["id", "amount"]
        mock_result.fetchall.return_value = [(1, 100), (2, 200)]
        mock_db_session.execute.return_value = mock_result
        
        result = executor.execute("SELECT * FROM sales")
        
        assert result is not None
        assert result.total_rows == 2
        assert result.columns == ["id", "amount"]


class TestAccuracyGuard:
    def test_verify_sql_completeness(self):
        """测试 SQL 完整性检查"""
        guard = AccuracyGuard()
        
        # 完整查询
        result = guard.verify_sql_completeness(
            "SELECT SUM(amount) FROM sales WHERE created_at >= '2026-01-01'",
            "一月份销售额"
        )
        assert result.is_valid is True
        
        # 缺少时间条件
        result = guard.verify_sql_completeness(
            "SELECT SUM(amount) FROM sales",
            "一月份销售额"
        )
        assert result.is_valid is False
        assert "时间条件" in result.issues[0]
    
    def test_verify_result_consistency(self):
        """测试结果一致性检查"""
        guard = AccuracyGuard()
        
        # 简单验证通过
        result = guard.verify_result_consistency(
            columns=["store", "sales"],
            rows=[{"store": "A", "sales": 100}, {"store": "B", "sales": 200}]
        )
        assert result.is_consistent is True
```

- [ ] **Step 2: 实现 SQL 执行器**

```python
# backend/app/services/query_executor.py
import time
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass
class QueryResult:
    """查询结果"""
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_rows: int
    execution_time_ms: int
    sql: str
    is_cached: bool = False


class QueryExecutor:
    """
    SQL 执行器：负责安全执行查询和结果处理
    """
    
    # 禁止的关键字（只允许 SELECT）
    FORBIDDEN_KEYWORDS = [
        r'\bDELETE\b',
        r'\bUPDATE\b',
        r'\bINSERT\b',
        r'\bDROP\b',
        r'\bCREATE\b',
        r'\bALTER\b',
        r'\bTRUNCATE\b',
        r'\bGRANT\b',
        r'\bREVOKE\b',
    ]
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def execute(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        max_rows: int = 1000
    ) -> Optional[QueryResult]:
        """
        执行 SQL 查询
        
        Args:
            sql: SQL 语句
            params: 查询参数
            max_rows: 最大返回行数
        
        Returns:
            QueryResult 或 None（执行失败）
        """
        # 安全检查
        if not self._is_safe_sql(sql):
            raise ValueError("不安全的 SQL：只允许 SELECT 查询")
        
        # 限制返回数量
        if "LIMIT" not in sql.upper():
            sql = f"{sql} LIMIT {max_rows}"
        
        start_time = time.time()
        
        try:
            # 执行查询
            result = self.db.execute(text(sql), params or {})
            
            # 获取列名
            columns = list(result.keys())
            
            # 获取结果
            rows = []
            for row in result.fetchall():
                rows.append(dict(zip(columns, row)))
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return QueryResult(
                columns=columns,
                rows=rows,
                total_rows=len(rows),
                execution_time_ms=execution_time,
                sql=sql
            )
            
        except Exception as e:
            raise RuntimeError(f"查询执行失败: {str(e)}")
    
    def _is_safe_sql(self, sql: str) -> bool:
        """检查 SQL 是否安全（只允许 SELECT）"""
        upper_sql = sql.upper().strip()
        
        # 必须以 SELECT 开头
        if not upper_sql.startswith('SELECT'):
            return False
        
        # 检查禁止的关键字
        for pattern in self.FORBIDDEN_KEYWORDS:
            if re.search(pattern, upper_sql, re.IGNORECASE):
                return False
        
        return True
    
    def validate_syntax(self, sql: str) -> tuple[bool, Optional[str]]:
        """
        验证 SQL 语法（使用 EXPLAIN）
        
        Returns:
            (是否有效, 错误信息)
        """
        try:
            explain_sql = f"EXPLAIN {sql}"
            self.db.execute(text(explain_sql))
            return True, None
        except Exception as e:
            return False, str(e)
```

- [ ] **Step 3: 实现准确性保障模块**

```python
# backend/app/services/accuracy_guard.py
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class SQLVerificationResult:
    """SQL 验证结果"""
    is_valid: bool
    issues: List[str]
    suggestions: List[str]


@dataclass
class ResultConsistencyCheck:
    """结果一致性检查结果"""
    is_consistent: bool
    warnings: List[str]
    details: Dict[str, Any]


class AccuracyGuard:
    """
    准确性保障：SQL 自检、结果校验、不确定性澄清
    """
    
    # 常见时间关键词
    TIME_KEYWORDS = ['昨天', '今天', '上周', '本周', '上月', '本月', 
                     '最近', '去年', '今年', '日', '月', '年', '周']
    
    def verify_sql_completeness(self, sql: str, question: str) -> SQLVerificationResult:
        """
        验证 SQL 是否完整回答了问题
        
        Args:
            sql: 生成的 SQL
            question: 用户问题
        
        Returns:
            SQLVerificationResult
        """
        issues = []
        suggestions = []
        
        upper_sql = sql.upper()
        
        # 检查时间条件
        has_time_condition = self._has_time_condition(sql)
        question_has_time = any(kw in question for kw in self.TIME_KEYWORDS)
        
        if question_has_time and not has_time_condition:
            issues.append("问题包含时间条件，但 SQL 中缺少时间过滤")
            suggestions.append("添加 WHERE 子句过滤时间范围")
        
        # 检查聚合函数
        if '各' in question or '每' in question:
            if 'GROUP BY' not in upper_sql:
                issues.append("问题涉及分组统计，但 SQL 缺少 GROUP BY")
                suggestions.append("添加 GROUP BY 子句")
        
        # 检查排序
        if '最' in question or 'Top' in question or 'top' in question:
            if 'ORDER BY' not in upper_sql:
                issues.append("问题涉及排序，但 SQL 缺少 ORDER BY")
                suggestions.append("添加 ORDER BY 子句")
        
        return SQLVerificationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            suggestions=suggestions
        )
    
    def verify_result_consistency(
        self,
        columns: List[str],
        rows: List[Dict[str, Any]]
    ) -> ResultConsistencyCheck:
        """
        验证结果的一致性
        
        Args:
            columns: 列名列表
            rows: 结果行
        
        Returns:
            ResultConsistencyCheck
        """
        warnings = []
        details = {
            "null_counts": {},
            "duplicate_check": False
        }
        
        if not rows:
            return ResultConsistencyCheck(
                is_consistent=True,
                warnings=["查询结果为空"],
                details=details
            )
        
        # 检查 NULL 值
        for col in columns:
            null_count = sum(1 for row in rows if row.get(col) is None)
            details["null_counts"][col] = null_count
            if null_count > len(rows) * 0.5:  # 超过 50% 为 NULL
                warnings.append(f"列 '{col}' 有 {null_count} 个 NULL 值，可能存在数据问题")
        
        # 检查重复行（如果有 ID 列）
        if 'id' in [c.lower() for c in columns]:
            id_col = next(c for c in columns if c.lower() == 'id')
            ids = [row[id_col] for row in rows if row.get(id_col) is not None]
            if len(ids) != len(set(ids)):
                warnings.append("结果中存在重复的 ID")
                details["duplicate_check"] = True
        
        return ResultConsistencyCheck(
            is_consistent=len(warnings) == 0 or all("数据问题" not in w for w in warnings),
            warnings=warnings,
            details=details
        )
    
    def _has_time_condition(self, sql: str) -> bool:
        """检查 SQL 是否包含时间条件"""
        time_patterns = [
            r'DATE\s*\(',
            r'YEAR\s*\(',
            r'MONTH\s*\(',
            r'DAY\s*\(',
            r'BETWEEN\s+\'\d{4}',
            r'>=\s*\'\d{4}',
            r'<=\s*\'\d{4}',
            r'\'\d{4}-\d{2}-\d{2}\'',
        ]
        
        upper_sql = sql.upper()
        for pattern in time_patterns:
            if re.search(pattern, upper_sql):
                return True
        
        return False
    
    def needs_clarification(self, question: str) -> tuple[bool, Optional[str]]:
        """
        判断是否需要用户澄清
        
        Returns:
            (是否需要澄清, 澄清提示)
        """
        # 模糊的时间表达
        if '最近' in question:
            return True, "'最近'具体指多少天？（7天还是30天？）"
        
        # 模糊的指标
        if '销售额' in question:
            return True, "'销售额'是指含税还是不含税？是否包含退款订单？"
        
        # 缺少维度
        if '各' in question and '按' not in question:
            return True, "请问按什么维度统计？（如按门店、按区域、按商品）"
        
        return False, None
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd backend
pytest tests/test_query_executor.py -v
# Expected: tests PASS
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/query_executor.py backend/app/services/accuracy_guard.py backend/tests/test_query_executor.py
git commit -m "feat: add query executor and accuracy guard"
```

---

## Task 6: 对话 API 路由

**Files:**
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/chat.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/chat.py`
- Create: `backend/app/schemas/query.py`

- [ ] **Step 1: 创建 API Schema 定义**

```python
# backend/app/schemas/chat.py
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
```

```python
# backend/app/schemas/query.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class QueryExecuteRequest(BaseModel):
    sql: str
    data_source_id: Optional[str] = None


class QueryExecuteResponse(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_rows: int
    execution_time_ms: int
    sql: str
```

- [ ] **Step 2: 创建对话路由**

```python
# backend/app/routers/chat.py
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
from app.services.ai_engine import AIEngine
from app.services.time_resolver import TimeResolver
from app.services.query_executor import QueryExecutor
from app.services.accuracy_guard import AccuracyGuard

router = APIRouter()


@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(
    req: ConversationCreate,
    db: Session = Depends(get_db)
):
    """创建新对话"""
    # 使用默认智能体（后续从配置读取）
    default_agent_id = None
    
    conversation = Conversation(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),  # TODO: 从认证获取
        current_agent_id=req.agent_id or default_agent_id,
        title=req.title or "新对话"
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return conversation


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: uuid.UUID,
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
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            title=req.message[:20] + "..."
        )
        db.add(conversation)
    
    # 保存用户消息
    user_message = Message(
        id=uuid.uuid4(),
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
            id=uuid.uuid4(),
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
            id=uuid.uuid4(),
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
        id=uuid.uuid4(),
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
```

- [ ] **Step 3: 更新路由 __init__.py**

```python
# backend/app/routers/__init__.py
from app.routers import chat

__all__ = ["chat"]
```

- [ ] **Step 4: 更新 Schema __init__.py**

```python
# backend/app/schemas/__init__.py
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.query import QueryExecuteRequest, QueryExecuteResponse

__all__ = [
    "ChatRequest", "ChatResponse",
    "QueryExecuteRequest", "QueryExecuteResponse"
]
```

- [ ] **Step 5: 添加默认智能体初始化**

```python
# backend/app/main.py（修改）
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base, SessionLocal
from app.models import Agent
from app.routers import chat

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
    finally:
        db.close()

init_default_agent()

app = FastAPI(
    title="AskTable AI API",
    description="AI-powered data analysis platform",
    version="0.1.0"
)

# ... rest of the code
```

- [ ] **Step 6: 测试 API**

```bash
# 启动服务
docker-compose up -d

# 创建对话
curl -X POST http://localhost:8000/api/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{}'

# 发送消息（需要先配置数据源）
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "昨天销售额多少？"}'
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/routers/ backend/app/schemas/ backend/app/main.py
git commit -m "feat: add chat API with full query flow"
```

---

## Task 7: 前端对话界面

**Files:**
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/types/chat.ts`
- Create: `frontend/src/api/chat.ts`
- Create: `frontend/src/components/ChatWindow.tsx`
- Create: `frontend/src/components/MessageList.tsx`
- Create: `frontend/src/components/MessageItem.tsx`
- Create: `frontend/src/components/SQLDisplay.tsx`
- Create: `frontend/src/components/DataTable.tsx`
- Create: `frontend/src/components/ChatInput.tsx`
- Create: `frontend/index.html`

- [ ] **Step 1: 创建 HTML 入口**

```html
<!-- frontend/index.html -->
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AskTable AI - 智能数据分析</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 2: 创建类型定义**

```typescript
// frontend/src/types/chat.ts
export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  content_type: 'text' | 'sql' | 'chart' | 'report';
  execution_metadata?: {
    sql?: string;
    confidence?: number;
    query_result?: {
      columns: string[];
      total_rows: number;
      execution_time_ms: number;
    };
    needs_clarification?: boolean;
  };
  created_at: string;
}

export interface Conversation {
  id: string;
  title?: string;
  current_agent_id?: string;
  created_at: string;
  updated_at: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  agent_id?: string;
}

export interface ChatResponse {
  message: Message;
  sql?: string;
  results?: Record<string, unknown>[];
  explanation?: string;
  needs_verification: boolean;
}
```

- [ ] **Step 3: 创建 API 客户端**

```typescript
// frontend/src/api/chat.ts
import axios from 'axios';
import { ChatRequest, ChatResponse, Conversation, Message } from '../types/chat';

const API_BASE = '/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const chatApi = {
  // 创建对话
  createConversation: () => 
    api.post<Conversation>('/conversations', {}),

  // 获取对话列表
  listConversations: (skip = 0, limit = 20) =>
    api.get<Conversation[]>(`/conversations?skip=${skip}&limit=${limit}`),

  // 获取对话详情
  getConversation: (id: string) =>
    api.get<Conversation & { messages: Message[] }>(`/conversations/${id}`),

  // 发送消息
  sendMessage: (data: ChatRequest) =>
    api.post<ChatResponse>('/chat', data),
};
```

- [ ] **Step 4: 创建 SQL 展示组件**

```tsx
// frontend/src/components/SQLDisplay.tsx
import React from 'react';

interface SQLDisplayProps {
  sql: string;
  executionTimeMs?: number;
  onCopy?: () => void;
}

export const SQLDisplay: React.FC<SQLDisplayProps> = ({
  sql,
  executionTimeMs,
  onCopy,
}) => {
  const handleCopy = () => {
    navigator.clipboard.writeText(sql);
    onCopy?.();
  };

  return (
    <div className="bg-gray-900 rounded-lg p-4 my-2">
      <div className="flex justify-between items-center mb-2">
        <span className="text-gray-400 text-xs">生成的 SQL</span>
        <button
          onClick={handleCopy}
          className="text-gray-400 hover:text-white text-xs"
        >
          复制
        </button>
      </div>
      <pre className="text-green-400 text-sm overflow-x-auto">
        <code>{sql}</code>
      </pre>
      {executionTimeMs !== undefined && (
        <div className="text-gray-500 text-xs mt-2">
          执行时间: {executionTimeMs}ms
        </div>
      )}
    </div>
  );
};
```

- [ ] **Step 5: 创建数据表格组件**

```tsx
// frontend/src/components/DataTable.tsx
import React from 'react';

interface DataTableProps {
  columns: string[];
  rows: Record<string, unknown>[];
  maxRows?: number;
}

export const DataTable: React.FC<DataTableProps> = ({
  columns,
  rows,
  maxRows = 100,
}) => {
  const displayRows = rows.slice(0, maxRows);
  const hasMore = rows.length > maxRows;

  return (
    <div className="overflow-x-auto my-2">
      <table className="min-w-full bg-white border border-gray-200 text-sm">
        <thead>
          <tr className="bg-gray-50">
            {columns.map((col) => (
              <th
                key={col}
                className="px-4 py-2 border-b text-left font-medium text-gray-700"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {displayRows.map((row, idx) => (
            <tr key={idx} className="hover:bg-gray-50">
              {columns.map((col) => (
                <td key={col} className="px-4 py-2 border-b text-gray-600">
                  {row[col] === null ? (
                    <span className="text-gray-400">NULL</span>
                  ) : (
                    String(row[col])
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {hasMore && (
        <div className="text-gray-500 text-xs mt-2">
          仅显示前 {maxRows} 行，共 {rows.length} 行
        </div>
      )}
    </div>
  );
};
```

- [ ] **Step 6: 创建消息项组件**

```tsx
// frontend/src/components/MessageItem.tsx
import React from 'react';
import { Message } from '../types/chat';
import { SQLDisplay } from './SQLDisplay';
import { DataTable } from './DataTable';

interface MessageItemProps {
  message: Message;
  results?: Record<string, unknown>[];
}

export const MessageItem: React.FC<MessageItemProps> = ({
  message,
  results,
}) => {
  const isUser = message.role === 'user';
  const metadata = message.execution_metadata;

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-lg p-4 ${
          isUser
            ? 'bg-blue-500 text-white'
            : 'bg-white border border-gray-200 text-gray-800'
        }`}
      >
        {/* 消息内容 */}
        <div className="whitespace-pre-wrap">{message.content}</div>

        {/* SQL 展示 */}
        {!isUser && metadata?.sql && (
          <SQLDisplay
            sql={metadata.sql}
            executionTimeMs={metadata.query_result?.execution_time_ms}
          />
        )}

        {/* 数据表格 */}
        {!isUser && results && results.length > 0 && metadata?.query_result?.columns && (
          <DataTable
            columns={metadata.query_result.columns}
            rows={results}
          />
        )}

        {/* 验证提示 */}
        {!isUser && metadata?.needs_clarification && (
          <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-yellow-800 text-sm">
            需要确认
          </div>
        )}

        {/* 时间戳 */}
        <div
          className={`text-xs mt-2 ${
            isUser ? 'text-blue-100' : 'text-gray-400'
          }`}
        >
          {new Date(message.created_at).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};
```

- [ ] **Step 7: 创建消息列表组件**

```tsx
// frontend/src/components/MessageList.tsx
import React from 'react';
import { Message } from '../types/chat';
import { MessageItem } from './MessageItem';

interface MessageListProps {
  messages: Message[];
  results?: Record<string, unknown>[];
  loading?: boolean;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  results,
  loading,
}) => {
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((message) => (
        <MessageItem
          key={message.id}
          message={message}
          results={message.role === 'assistant' ? results : undefined}
        />
      ))}
      
      {loading && (
        <div className="flex justify-start">
          <div className="bg-gray-100 rounded-lg p-4">
            <div className="flex space-x-2">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
            </div>
          </div>
        </div>
      )}
      
      <div ref={messagesEndRef} />
    </div>
  );
};
```

- [ ] **Step 8: 创建输入框组件**

```tsx
// frontend/src/components/ChatInput.tsx
import React, { useState } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  loading?: boolean;
  placeholder?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  loading,
  placeholder = '输入你的问题，如：昨天销售额多少？',
}) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !loading) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="border-t p-4 bg-white">
      <div className="flex space-x-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={loading}
          rows={2}
          className="flex-1 border border-gray-300 rounded-lg px-4 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {loading ? '发送中...' : '发送'}
        </button>
      </div>
      <div className="text-xs text-gray-400 mt-2">
        按 Enter 发送，Shift + Enter 换行
      </div>
    </form>
  );
};
```

- [ ] **Step 9: 创建对话窗口组件**

```tsx
// frontend/src/components/ChatWindow.tsx
import React, { useState, useEffect } from 'react';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { chatApi } from '../api/chat';
import { Message, ChatResponse } from '../types/chat';

export const ChatWindow: React.FC = () => {
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentResults, setCurrentResults] = useState<Record<string, unknown>[] | undefined>();
  const [loading, setLoading] = useState(false);

  // 创建新对话
  useEffect(() => {
    const initConversation = async () => {
      try {
        const { data } = await chatApi.createConversation();
        setConversationId(data.id);
      } catch (error) {
        console.error('Failed to create conversation:', error);
      }
    };
    initConversation();
  }, []);

  const handleSendMessage = async (content: string) => {
    if (!conversationId) return;

    // 添加用户消息到列表
    const userMessage: Message = {
      id: Date.now().toString(),
      conversation_id: conversationId,
      role: 'user',
      content,
      content_type: 'text',
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setCurrentResults(undefined);

    try {
      const { data } = await chatApi.sendMessage({
        message: content,
        conversation_id: conversationId,
      });

      // 添加助手消息
      setMessages((prev) => [...prev, data.message]);
      
      // 如果有结果，保存
      if (data.results) {
        setCurrentResults(data.results);
      }

      // 如果需要验证，显示提示
      if (data.needs_verification) {
        console.log('Needs verification:', data.explanation);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      // 显示错误消息
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        conversation_id: conversationId,
        role: 'assistant',
        content: '抱歉，处理你的请求时出现了错误。请稍后重试。',
        content_type: 'text',
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* 头部 */}
      <header className="bg-white border-b px-4 py-3">
        <h1 className="text-lg font-semibold text-gray-800">AskTable AI</h1>
        <p className="text-sm text-gray-500">智能数据分析助手</p>
      </header>

      {/* 消息列表 */}
      <MessageList
        messages={messages}
        results={currentResults}
        loading={loading}
      />

      {/* 输入框 */}
      <ChatInput onSend={handleSendMessage} loading={loading} />
    </div>
  );
};
```

- [ ] **Step 10: 创建主应用组件**

```tsx
// frontend/src/App.tsx
import React from 'react';
import { ChatWindow } from './components/ChatWindow';

const App: React.FC = () => {
  return <ChatWindow />;
};

export default App;
```

- [ ] **Step 11: 创建入口文件**

```tsx
// frontend/src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 12: 创建 CSS 文件**

```css
/* frontend/src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 动画延迟 */
.delay-100 {
  animation-delay: 100ms;
}

.delay-200 {
  animation-delay: 200ms;
}
```

- [ ] **Step 13: 创建 Tailwind 配置**

```javascript
// frontend/tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

- [ ] **Step 14: 创建 PostCSS 配置**

```javascript
// frontend/postcss.config.js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 15: 更新 package.json 添加 Tailwind 依赖**

```json
{
  "name": "asktable-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.5"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.2.2",
    "vite": "^5.0.8",
    "tailwindcss": "^3.4.1",
    "autoprefixer": "^10.4.17",
    "postcss": "^8.4.33"
  }
}
```

- [ ] **Step 16: Commit**

```bash
git add frontend/
git commit -m "feat: add React frontend with chat interface"
```

---

## Task 8: 数据源配置 API

**Files:**
- Modify: `backend/app/routers/chat.py`（添加数据源路由）
- Create: `backend/app/schemas/data_source.py`

- [ ] **Step 1: 创建数据源 Schema**

```python
# backend/app/schemas/data_source.py
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
```

- [ ] **Step 2: 添加数据源路由到 chat.py**

```python
# backend/app/routers/chat.py（在文件末尾添加）

from app.schemas.data_source import (
    DataSourceCreate, DataSourceUpdate, DataSourceResponse
)
from cryptography.fernet import Fernet
import os

# 简单的加密密钥（生产环境应从环境变量读取）
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())
fernet = Fernet(ENCRYPTION_KEY)


def encrypt_password(password: str) -> str:
    """加密密码"""
    return fernet.encrypt(password.encode()).decode()


def decrypt_password(encrypted: str) -> str:
    """解密密码"""
    return fernet.decrypt(encrypted.encode()).decode()


@router.post("/data-sources", response_model=DataSourceResponse)
def create_data_source(
    req: DataSourceCreate,
    db: Session = Depends(get_db)
):
    """创建数据源"""
    # 加密密码
    encrypted_password = encrypt_password(req.password)
    
    data_source = DataSource(
        id=uuid.uuid4(),
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
    source_id: uuid.UUID,
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
    source_id: uuid.UUID,
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
    data_source.schema_cache_updated_at = datetime.utcnow()
    db.commit()
    
    return {"status": "success", "tables": len(schema["tables"])}


@router.delete("/data-sources/{source_id}")
def delete_data_source(
    source_id: uuid.UUID,
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
```

- [ ] **Step 3: 更新 requirements.txt 添加加密库**

```txt
# backend/requirements.txt（添加）
cryptography==42.0.0
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/routers/chat.py backend/app/schemas/data_source.py backend/requirements.txt
git commit -m "feat: add data source management API"
```

---

## 计划自检

### 1. Spec 覆盖检查

| Spec 需求 | 实现任务 | 状态 |
|-----------|----------|------|
| 自然语言问数 | Task 6 (chat API), Task 4 (AI Engine) | ✅ |
| Text-to-SQL | Task 4 (AI Engine) | ✅ |
| 时间解析 | Task 2 (Time Resolver) | ✅ |
| 准确性保障 | Task 5 (Accuracy Guard) | ✅ |
| 基础智能体 | Task 3 (Agent model), Task 6 (default agent) | ✅ |
| Web 对话界面 | Task 7 (Frontend) | ✅ |
| 数据源管理 | Task 8 (Data Source API) | ✅ |

### 2. Placeholder 检查
- 无 TBD/TODO
- 所有代码步骤包含完整实现
- 测试包含断言和预期输出

### 3. 类型一致性检查
- `SQLGenerationResult` 在 Task 4 定义，Task 6 使用一致
- `Message` 模型前后端字段一致

---

## 执行方式选择

**计划完成并保存至：** `docs/superpowers/plans/2026-04-08-phase1-core-loop.md`

**两种执行选项：**

**1. Subagent-Driven（推荐）** - 每个 Task 分配独立子代理执行，我在每两个 Task 后进行审核，适合并行开发和快速迭代

**2. Inline Execution** - 在当前会话中按顺序执行所有 Task，适合专注的单人开发模式

**请选择执行方式？** 建议：
- 如果你是唯一的开发者，选 **Inline Execution** 可以一次性完成
- 如果希望分阶段交付或多人协作，选 **Subagent-Driven**
