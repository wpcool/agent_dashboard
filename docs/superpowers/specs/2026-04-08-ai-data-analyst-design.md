# AI 数据分析平台设计方案

**日期**: 2026-04-08  
**版本**: v1.0  
**状态**: 待实现

---

## 1. 项目概述

### 1.1 背景
面向企业内部的数据分析需求，构建一个基于大模型驱动的 AI 数据分析平台，类似 AskTable（察言观数）。支持自然语言查询、AI 分析报告、多智能体协作，以及自定义分析流程编排。

### 1.2 核心目标
- **降低数据分析门槛**：非技术人员通过自然语言获取数据洞察
- **提升分析效率**：一句话生成传统 BI 需要数小时的分析报告
- **灵活适配业务**：支持自定义智能体，匹配不同业务场景的分析需求

### 1.3 用户画像
- 门店经营者：关注坪效、客流、库存
- 电商运营：关注转化、ROI、盯盘
- 财务人员：关注现金流、成本、利润
- 高管：关注整体经营指标、红黄灯预警
- 数据分析师：关注数据质量、异常监控

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Presentation Layer                        │
├──────────────────┬──────────────────┬────────────────────────────┤
│   Web Frontend   │   IM Gateway     │    Admin Console           │
│  (对话/报告/画布) │ (钉钉/飞书/企微)  │  (智能体配置/权限管理)      │
└────────┬─────────┴────────┬─────────┴────────────┬───────────────┘
         │                  │                      │
         └──────────────────┼──────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway                              │
│              (路由/认证/限流/智能体上下文管理)                    │
└─────────────────────────────────────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  Query Agent  │  │ Report Agent  │  │ Monitor Agent │
│   (即席查询)   │  │  (分析报告)   │  │   (监控预警)  │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Agent Orchestrator                           │
│         (智能体调度/上下文切换/多智能体协作/流程编排引擎)          │
└─────────────────────────────────────────────────────────────────┘
                           │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌────────────────┐ ┌──────────────┐ ┌──────────────┐
│   AI Engine    │ │  Metadata    │ │  Execution   │
│ (SQL/解读/规划) │ │   Service    │ │   Engine     │
└────────────────┘ │(术语/权限/数据源)│ │(SQL执行/缓存)│
                   └──────────────┘ └──────────────┘
```

### 2.2 核心服务职责

| 服务 | 职责 | 关键技术 |
|------|------|----------|
| **API Gateway** | 统一入口、认证、限流、智能体上下文管理 | FastAPI + JWT |
| **AI Engine** | SQL 生成、数据解读、意图识别、术语解析、流程规划 | Claude API + 本地缓存 |
| **Metadata Service** | 智能体配置、权限管理、术语词典、数据源管理 | PostgreSQL |
| **Agent Orchestrator** | 智能体生命周期、上下文切换、工作流编排执行 | Temporal/自研 |
| **Execution Engine** | SQL 执行、结果缓存、查询优化 | SQLAlchemy + Redis |

---

## 3. 智能体设计

### 3.1 智能体模型

每个智能体是**角色 + 权限 + 风格 + 工作流**的组合：

```yaml
agent:
  id: "store_analyst"
  name: "门店经营分析师"
  description: "专注门店运营效率分析，提供坪效、客流、库存等专业洞察"
  
  # 1. 角色定义 (Role)
  persona:
    system_prompt: "你是一位资深门店运营专家，熟悉零售行业的坪效分析、客流转化、库存周转等核心指标..."
    expertise: ["坪效分析", "客流转化", "库存周转", "人效分析"]
    thinking_style: "先诊断问题，再找原因，给出可执行建议"
  
  # 2. 数据权限 (Permission)
  data_scope:
    allowed_databases: ["retail_dw"]
    allowed_tables: ["store_sales", "inventory", "traffic", "staff"]
    row_filter: "store_id IN (${user.store_ids})"
    sensitive_fields: ["customer_phone", "staff_salary"]
    field_masks:
      - field: "customer_phone"
        mask: "mask_phone"  # 脱敏规则
  
  # 3. 输出风格 (Style)
  output:
    format: "结论先行 + 数据支撑 + 行动建议"
    verbosity: "concise"  # concise/detailed/verbose
    visualization_preference: ["table", "line_chart", "heatmap"]
    language_style: "专业但易懂，避免过多财务术语"
  
  # 4. 分析流程 (Workflow)
  workflow:
    - step: "理解问题"
      action: "intent_recognition"
      output: "parsed_intent"
    - step: "提取数据"
      action: "sql_generation"
      input: ["parsed_intent"]
      output: "query_result"
    - step: "洞察分析"
      action: "pattern_analysis"
      input: ["query_result", "parsed_intent"]
      output: "insights"
    - step: "生成建议"
      action: "recommendation"
      input: ["insights"]
      output: "final_response"
```

### 3.2 内置智能体列表

| 智能体 | 角色定位 | 核心能力 | 数据范围 |
|--------|----------|----------|----------|
| **门店经营分析师** | 门店运营专家 | 坪效、客流、库存、人效 | 单店/多店 |
| **电商数据盯盘助手** | 实时监控员 | 转化漏斗、ROI、流量来源 | 电商平台 |
| **财务数据分析师** | 财务专家 | 现金流、成本、利润、预算 | 全公司 |
| **市场洞察分析师** | 市场研究 | 竞品、趋势、用户画像 | 市场数据 |
| **用户增长分析师** | 增长黑客 | 留存、活跃、LTV、渠道 | 用户数据 |
| **供应链监控官** | 供应链专家 | 库存周转、交付、供应商 | 供应链 |
| **高管数据助手** | 决策支持 | 综合指标、红黄灯、趋势 | 全公司汇总 |
| **经营红黄灯分析师** | 预警专家 | 异常检测、风险预警、根因 | 关键指标 |
| **数据质量守护者** | 数据治理 | 完整性、准确性、一致性检查 | 元数据 |

### 3.3 自定义智能体

用户可创建自定义智能体，配置维度包括：

1. **基础配置**：名称、描述、系统提示词
2. **数据权限**：可见的数据源、表、行级过滤
3. **业务术语**：专属术语词典
4. **分析流程**：通过画布或配置定义工作流节点

---

## 4. 核心数据流

### 4.1 对话流程（单次查询）

```
用户: "昨天北京门店销售额多少？"
         │
         ▼
┌─────────────────┐
│ 1. 上下文管理器  │ ◄── 加载当前智能体（门店经营分析师）
│   (Agent Context)│     用户权限（北京门店范围）
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. 意图识别      │ ◄── AI 解析意图：销售数据查询
│  (Intent Recog) │     实体提取：时间=昨天，维度=北京门店，指标=销售额
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. 术语解析      │ ◄── 查术语词典: "销售额" → SUM(amount)
│  (Term Resolver)│     时间解析: "昨天" → 基于当前时间计算 [2026-04-07 00:00, 23:59]
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. SQL 生成      │ ◄── AI 生成 SQL，注入权限过滤
│  (SQL Generator)│     WHERE store_city = '北京' AND store_id IN (101,102,103)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. SQL 自检      │ ◄── AI 验证 SQL 完整性、正确性
│ (Self-Verify)   │     检查：时间条件？聚合正确？维度完整？
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 6. 执行与校验    │ ◄── 执行 SQL，交叉验证（如 COUNT + SUM）
│   (Execution)   │     结果缓存 5 分钟
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 7. 结果解读      │ ◄── AI: "昨天北京 5 家门店共销售 128 万"
│  (Interpretation)│    "环比增长 15%，其中朝阳店贡献最高（45 万）"
└────────┬────────┘
         │
         ▼
      [返回用户，附带审计信息]
```

### 4.2 智能体切换流程

```
用户当前: 门店经营分析师
              │
    "帮我看看公司整体现金流"
              │
              ▼
┌─────────────────────────────┐
│      Agent Switch Flow       │
├─────────────────────────────┤
│ 1. 意图检测: 检测到领域切换   │
│    "现金流" ∉ 门店经营领域    │
│                             │
│ 2. 目标识别: "现金流" → 财务  │
│    推荐智能体: 财务数据分析师 │
│                             │
│ 3. 上下文保存:               │
│    {                        │
│      agent: "store_analyst",│
│      focus: "北京门店销售", │
│      metrics: {sales: 128}, │
│      timestamp: "2026-04-08"│
│    } → 存入 context_history │
│                             │
│ 4. 上下文加载（财务分析师）:  │
│    {                        │
│      agent: "finance_analyst"│
│      scope: "全公司",        │
│      tables: ["cash_flow"]   │
│    }                        │
│                             │
│ 5. 可选: 关联传递             │
│    "用户刚查过北京门店销售，   │
│     现在想看公司整体现金流"   │
│                             │
│ 6. 确认提示:                  │
│    "已切换至【财务数据分析师】 │
│     数据范围：全公司"         │
└─────────────────────────────┘
```

---

## 5. 准确性保障机制

### 5.1 多层校验体系

```
┌─────────────────────────────────────────────────────────────┐
│                  Accuracy Assurance Layer                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. SQL 生成后自检                                           │
│     ┌─────────────────────────────────────────────────┐     │
│     │  AI 必须验证:                                    │     │
│     │  • SQL 是否完整回答用户问题？                     │     │
│     │  • 有没有遗漏条件（时间、范围、过滤）？           │     │
│     │  • 聚合维度是否正确？                            │     │
│     │  • 是否有潜在的 NULL 处理问题？                  │     │
│     │  如有疑问 → 重新生成或澄清询问                  │     │
│     └─────────────────────────────────────────────────┘     │
│                           │                                  │
│                           ▼                                  │
│  2. 执行前校验                                               │
│     • 语法检查 (EXPLAIN)                                    │
│     • 预估数据量（防止全表扫描）                             │
│     • 敏感操作拦截（DELETE/UPDATE/DDL 确认）                 │
│                                                              │
│                           ▼                                  │
│  3. 结果一致性校验                                           │
│     ┌─────────────────────────────────────────────────┐     │
│     │  首次查询后，触发交叉验证:                        │     │
│     │                                                 │     │
│     │  例: 用户问"各门店销售额"                        │     │
│     │  主查询: SELECT store, SUM(sales) GROUP BY store │     │
│     │                                                 │     │
│     │  验证查询:                                       │     │
│     │  ① COUNT(DISTINCT store) = 结果行数？            │     │
│     │  ② SUM(门店销售额) = 全表总销售额？              │     │
│     │  ③ 检查 NULL / 异常值                            │     │
│     │                                                 │     │
│     │  如有异常 → 触发补充查询或告警                  │     │
│     └─────────────────────────────────────────────────┘     │
│                           │                                  │
│                           ▼                                  │
│  4. 不确定性澄清                                             │
│     检测到以下情况，主动询问而非猜测:                        │
│     • 时间模糊: "最近" → 确认 7 天 or 30 天                │
│     • 指标歧义: "销售额" → 含税？含退款？                   │
│     • 维度缺失: "各区域" → 确认区域划分标准                 │
│                                                              │
│                           ▼                                  │
│  5. 审计追溯                                                 │
│     每个结果附带:                                            │
│     • 执行的完整 SQL 及参数                                  │
│     • 查询时间范围和数据源                                    │
│     • 校验步骤及结果                                          │
│     • AI 推理过程（Chain-of-Thought）                        │
│     用户可随时查看"这个数字怎么来的"                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 时间解析模块

```python
class TimeResolver:
    """
    解析相对时间为绝对时间范围
    基于查询时的真实当前时间
    """
    
    def resolve(self, expression: str, query_time: datetime) -> TimeRange:
        """
        示例:
        "昨天" → [2026-04-07 00:00:00, 2026-04-07 23:59:59]
        "上周" → [2026-03-30, 2026-04-05]  (自然周)
        "最近3个月" → [2026-01-08, 2026-04-07]
        "本季度" → [2026-04-01, 2026-06-30]
        "上月" → [2026-03-01, 2026-03-31]
        """
        pass
    
    def resolve_business_time(self, expression: str,
                              query_time: datetime,
                              business_calendar: Calendar) -> TimeRange:
        """
        业务时间语义（考虑工作日、营业日）
        例: "最近3个工作日" 需排除周末和节假日
        """
        pass
```

---

## 6. 工作流编排引擎

### 6.1 节点类型

| 节点类型 | 说明 | 示例 |
|----------|------|------|
| **query** | 执行 SQL 查询 | 提取销售数据 |
| **calculate** | 数值计算 | 同比、环比、达成率 |
| **ai_analysis** | AI 洞察分析 | 异常检测、根因分析 |
| **visualization** | 生成图表 | 柱状图、趋势图、热力图 |
| **report** | 组装报告 | 整合多节点输出为报告 |
| **condition** | 条件分支 | 根据指标值走不同分支 |
| **loop** | 循环处理 | 对每个区域重复分析 |
| **merge** | 合并结果 | 合并多个并行节点输出 |

### 6.2 自定义智能体示例

用户创建"月度经营复盘助手":

```yaml
agent_id: "monthly_review_assistant"
name: "月度经营复盘助手"

workflow:
  nodes:
    - id: "fetch_sales"
      type: "query"
      config:
        sql: |
          SELECT region, SUM(amount) as sales, target
          FROM sales_monthly
          WHERE month = ${input.month}
          GROUP BY region
      
    - id: "calc_achievement"
      type: "calculate"
      config:
        expression: "sales / target * 100"
        output_field: "achievement_rate"
      depends_on: ["fetch_sales"]
      
    - id: "check_low_performers"
      type: "condition"
      config:
        condition: "achievement_rate < 80"
        true_branch: "analyze_gap"
        false_branch: "skip_analysis"
      depends_on: ["calc_achievement"]
      
    - id: "analyze_gap"
      type: "ai_analysis"
      config:
        prompt: "分析这些区域达成率低的原因，给出具体建议"
      depends_on: ["check_low_performers"]
      
    - id: "generate_chart"
      type: "visualization"
      config:
        chart_type: "bar"
        x: "region"
        y: "achievement_rate"
        reference_line: 80
      depends_on: ["calc_achievement"]
      
    - id: "compile_report"
      type: "report"
      config:
        title: "${input.month} 经营复盘报告"
        sections:
          - title: "销售总览"
            source: "fetch_sales"
          - title: "达成率分析"
            source: "calc_achievement"
          - title: "差距分析"
            source: "analyze_gap"
            condition: "has_low_performers"
          - title: "可视化"
            source: "generate_chart"
      depends_on: ["analyze_gap", "generate_chart"]
```

### 6.3 执行引擎特性

- **DAG 执行**: 基于依赖图自动调度节点
- **并行优化**: 无依赖节点并行执行
- **状态持久**: 支持长时间运行，可断点续跑
- **错误处理**: 支持重试、回滚、告警
- **缓存复用**: 中间结果缓存，避免重复计算

---

## 7. 数据模型

### 7.1 核心表结构

```sql
-- 智能体定义
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_builtin BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    
    -- 角色配置
    persona_system_prompt TEXT,
    persona_expertise TEXT[],
    thinking_style VARCHAR(50),
    
    -- 输出风格
    output_format TEXT,
    output_verbosity VARCHAR(20) CHECK (output_verbosity IN ('concise', 'detailed', 'verbose')),
    visualization_preferences TEXT[],
    
    -- 工作流定义
    workflow_definition JSONB,
    
    -- 审计
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 数据源配置
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,  -- mysql, postgresql, clickhouse, etc.
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    database_name VARCHAR(100) NOT NULL,
    username VARCHAR(100) NOT NULL,
    password_encrypted TEXT NOT NULL,  -- 加密存储
    connection_options JSONB DEFAULT '{}',
    
    -- 元数据缓存
    schema_cache JSONB,
    schema_cache_updated_at TIMESTAMP WITH TIME ZONE,
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 业务术语词典
CREATE TABLE term_dictionary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    term VARCHAR(100) NOT NULL,  -- 中文术语
    definition_sql TEXT,         -- SQL 片段或计算逻辑
    description TEXT,
    examples TEXT[],
    
    -- 关联
    agent_id UUID REFERENCES agents(id),  -- NULL 表示全局术语
    data_source_id UUID REFERENCES data_sources(id),
    
    -- 向量嵌入（用于相似匹配）
    embedding VECTOR(1536),
    
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(term, agent_id)
);

-- 用户权限
CREATE TABLE user_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    agent_id UUID REFERENCES agents(id),
    
    -- 数据范围
    allowed_data_source_ids UUID[],
    allowed_table_patterns TEXT[],  -- 支持通配，如 "sales_*"
    
    -- 行级过滤（JSON 格式，可定义多个条件）
    row_filters JSONB DEFAULT '[]',
    -- 示例: [{"table": "sales", "condition": "region = 'north'"}]
    
    -- 字段脱敏
    field_masks JSONB DEFAULT '[]',
    -- 示例: [{"table": "customers", "field": "phone", "mask_type": "partial"}]
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 对话会话
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    current_agent_id UUID REFERENCES agents(id),
    
    title VARCHAR(200),  -- 自动生成的会话标题
    
    -- 当前智能体上下文
    current_context JSONB DEFAULT '{}',
    -- 示例: {"focus": "北京门店销售", "last_metrics": {...}}
    
    -- 历史切换记录
    context_history JSONB[] DEFAULT '{}',
    
    is_archived BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 消息记录
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    content_type VARCHAR(20) DEFAULT 'text',  -- text, sql, chart, report
    
    -- 执行元数据
    execution_metadata JSONB,
    -- 示例:
    -- {
    --   "agent_id": "store_analyst",
    --   "sql": "SELECT ...",
    --   "sql_params": {...},
    --   "query_result_summary": {"rows": 5, "duration_ms": 120},
    --   "verification_steps": [...],
    --   "data_sources": ["retail_dw"],
    --   "ai_reasoning": "..."
    -- }
    
    -- 用于流式响应
    is_streaming BOOLEAN DEFAULT false,
    streaming_completed_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 查询历史（用于缓存和审计）
CREATE TABLE query_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 查询指纹（规范化后的 SQL）
    query_fingerprint VARCHAR(64) NOT NULL,
    
    -- 原始查询信息
    original_sql TEXT NOT NULL,
    normalized_sql TEXT NOT NULL,
    query_params JSONB DEFAULT '{}',
    data_source_id UUID REFERENCES data_sources(id),
    
    -- 执行信息
    execution_time_ms INTEGER,
    rows_returned INTEGER,
    is_cached BOOLEAN DEFAULT false,
    
    -- 结果摘要（用于快速判断是否可复用）
    result_summary JSONB,
    
    -- 过期时间
    expires_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_agents_code ON agents(code);
CREATE INDEX idx_agents_is_builtin ON agents(is_builtin);
CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX idx_term_embedding ON term_dictionary USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_query_fingerprint ON query_history(query_fingerprint);
```

---

## 8. 技术选型

| 层级 | 选型 | 说明 |
|------|------|------|
| **后端框架** | Python FastAPI | 异步支持好，AI 生态丰富 |
| **前端框架** | React 18 + TypeScript | 类型安全，生态成熟 |
| **UI 组件** | Tailwind CSS + Headless UI | 定制化能力强 |
| **可视化** | ECharts / D3.js | 图表丰富，支持自定义 |
| **画布编排** | ReactFlow | 节点编排交互 |
| **数据库** | PostgreSQL 15+ | 元数据存储，支持 pgvector |
| **缓存** | Redis 7 | 查询缓存、会话状态 |
| **消息队列** | RabbitMQ | 异步任务、报告生成 |
| **AI 模型** | Claude API (初期) | 复杂推理能力强 |
| **向量化** | pgvector | 术语相似匹配 |
| **流程编排** | Temporal (可选) | 长时间运行工作流 |
| **部署** | Docker Compose / K8s | 容器化部署 |

---

## 9. 实现计划

### Phase 1: 核心闭环（4-6 周）

**目标**: 跑通自然语言 → SQL → 结果的完整流程

- [ ] 项目脚手架搭建（FastAPI + React + PostgreSQL + Redis）
- [ ] 数据源连接管理（支持 MySQL、PostgreSQL）
- [ ] AI Engine 基础能力（Text-to-SQL）
- [ ] 基础智能体（通用数据分析师）
- [ ] Web 对话界面（消息流、SQL 展示、结果表格）
- [ ] 准确性保障（SQL 自检、基础校验）

### Phase 2: 智能体系统（3-4 周）

- [ ] 多智能体框架（角色、权限、风格配置）
- [ ] 内置智能体实现（5+ 个专业分析师）
- [ ] 智能体切换机制
- [ ] 自定义智能体（基础配置）
- [ ] 业务术语词典
- [ ] 时间解析模块

### Phase 3: 报告与 IM（3-4 周）

- [ ] AI 分析报告生成
- [ ] 可视化图表组件
- [ ] 报告导出（PDF、图片）
- [ ] 钉钉/飞书机器人接入
- [ ] 消息模板与格式化

### Phase 4: 高级功能（持续迭代）

- [ ] AI Canvas 流程编排（可视化画布）
- [ ] 自定义分析工作流
- [ ] 数据监控预警
- [ ] 更多数据源支持（ClickHouse、Doris、API）
- [ ] 性能优化（查询缓存、预计算）

---

## 10. 非功能性需求

### 10.1 性能指标

| 指标 | 目标 | 说明 |
|------|------|------|
| 查询响应时间 | < 3s (P95) | 简单查询 < 1s，复杂查询 < 5s |
| SQL 生成时间 | < 2s | 包含自检和校验 |
| 并发用户 | 100+ | 初期目标 |
| 报告生成 | < 30s | 复杂报告允许异步 |

### 10.2 安全要求

- 所有数据源凭据加密存储
- SQL 注入防护（参数化查询）
- 敏感操作二次确认
- 操作审计日志
- 数据访问权限严格控制

### 10.3 可靠性

- 查询超时保护（防止慢 SQL 拖垮）
- AI 调用失败降级
- 服务健康检查
- 关键数据定期备份

---

## 11. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| AI SQL 生成不准确 | 高 | 多层校验、人工确认机制、持续优化提示词 |
| 数据源连接安全 | 高 | 只读账号、网络隔离、敏感数据脱敏 |
| 查询性能问题 | 中 | 查询超时、结果缓存、慢查询监控 |
| 大模型 API 成本 | 中 | 结果缓存、提示词优化、批量处理 |

---

## 12. 附录

### 12.1 术语表

| 术语 | 说明 |
|------|------|
| 智能体 (Agent) | 具有特定角色、权限和分析风格的 AI 助手 |
| Text-to-SQL | 自然语言转 SQL 的技术 |
| AI Canvas | 可视化分析流程编排界面 |
| 行级权限 | 用户只能看到符合特定条件的数据行 |

### 12.2 参考资源

- [AskTable 技术架构](https://www.asktable.com/blog/2025-12-17/asktable-ai-tech-arch-and-capabilities)
- [Text-to-SQL 最佳实践](https://arxiv.org/abs/2306.00739)

---

**文档版本历史**

| 版本 | 日期 | 修改内容 | 作者 |
|------|------|----------|------|
| v1.0 | 2026-04-08 | 初始版本 | - |
