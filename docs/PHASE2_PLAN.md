# Phase 2: 智能体系统实施计划

## 目标
构建多智能体框架，实现 9 个内置专业分析师，支持智能体切换和自定义配置。

## 任务分解

### Task 1: 智能体模型扩展
- 扩展 Agent 数据模型，支持 persona、data_scope、output、workflow 配置
- 创建 AgentConfig 配置管理类
- 数据库迁移

### Task 2: 内置智能体实现（9个）
1. 通用数据分析师 (default_analyst) - 已有
2. 门店经营分析师 (store_analyst)
3. 电商数据盯盘助手 (ecommerce_monitor)
4. 财务数据分析师 (finance_analyst)
5. 市场洞察分析师 (market_analyst)
6. 用户增长分析师 (growth_analyst)
7. 供应链监控官 (supply_chain)
8. 高管数据助手 (executive_assistant)
9. 经营红黄灯分析师 (alert_analyst)

### Task 3: 智能体切换机制
- API: 获取智能体列表
- API: 对话中切换智能体
- 前端: 智能体选择器组件
- 前端: 显示当前智能体信息

### Task 4: 自定义智能体（基础）
- API: 创建自定义智能体
- API: 更新/删除智能体
- 前端: 智能体配置表单
- 前端: 我的智能体列表

### Task 5: 业务术语词典
- Term 数据模型
- 术语 CRUD API
- 术语解析服务集成
- 前端术语管理界面

### Task 6: 智能体初始化数据
- 创建 9 个内置智能体的初始化脚本
- 每个智能体的系统提示词、专长、风格配置

## 技术要点
- 智能体配置使用 JSON 字段灵活存储
- 系统提示词需要精心设计（Prompt Engineering）
- 权限控制与数据范围过滤
