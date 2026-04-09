# Phase 2: Skill-Based 智能体系统（基于技能组合）

## 核心概念

### Skill（技能）
预定义的可复用分析能力，每个 Skill 包含：
- 系统提示词片段
- 输入/输出定义
- 执行逻辑

### 内置 Skills（6个核心技能）
1. **数据查询** (data_query) - 自然语言转 SQL
2. **归因分析** (attribution) - 分析指标变化原因
3. **异常检测** (anomaly) - 识别数据异常点
4. **预测分析** (forecast) - 基于历史预测趋势
5. **报告生成** (report) - 生成综合分析报告
6. **可视化** (visualization) - 图表推荐与生成

### Agent（智能体）
由 1-N 个 Skill 组合而成，加上角色定义：
- 角色名称/描述
- 选择的 Skills
- 专属系统提示词（可选）
- 数据权限范围

## 示例智能体配置

```yaml
# 门店经营分析师
agent:
  name: "门店经营分析师"
  skills: [data_query, attribution, anomaly]
  persona: "专注门店坪效、客流、库存分析"
  
# 财务数据分析师  
agent:
  name: "财务数据分析师"
  skills: [data_query, forecast, report]
  persona: "专注现金流、成本、利润分析"
```

## 实施任务

### Task 1: Skill 框架
- Skill 基类/接口设计
- 6个内置 Skill 实现
- Skill 注册与发现机制

### Task 2: Agent 重构
- Agent 关联 Skill（多对多）
- 动态提示词组装（基础提示词 + 选中 Skills 提示词）
- Agent 运行时 Skill 调度

### Task 3: Agent 市场
- 预设 Agent 模板（9个场景）
- 自定义 Agent 创建（选择 Skills 组合）
- Agent 列表/详情/编辑

### Task 4: 对话中 Skill 调用
- 意图识别 → 路由到对应 Skill
- 多 Skill 协作（如：先查询→再归因）
- Skill 切换与上下文保持
