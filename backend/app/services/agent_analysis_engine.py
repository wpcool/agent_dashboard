"""
智能分析引擎 - 支持复杂任务的多步骤分析
"""
import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, AsyncGenerator
from enum import Enum
from anthropic import Anthropic
from app.config import get_settings
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
import os
import time


class TaskType(Enum):
    """任务类型"""
    SINGLE_QUERY = "single_query"      # 简单单表查询
    MULTI_QUERY = "multi_query"        # 多表/多维度查询
    ATTRIBUTION = "attribution"        # 归因分析
    COMPARISON = "comparison"          # 对比分析
    TREND = "trend"                    # 趋势分析
    COMPREHENSIVE = "comprehensive"    # 综合分析


@dataclass
class ValidationResult:
    """SQL验证结果"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    fixed_sql: Optional[str] = None
    validation_details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisStep:
    """分析步骤"""
    step_id: str
    description: str          # 步骤描述
    purpose: str              # 目的说明
    sql: str = ""            # SQL 查询
    result: Any = None        # 查询结果
    insight: str = ""        # 该步骤的发现
    depends_on: List[str] = field(default_factory=list)  # 依赖的步骤
    validation: Optional[ValidationResult] = None  # SQL验证结果


@dataclass
class AnalysisPlan:
    """分析计划"""
    task_type: TaskType
    user_intent: str          # 用户意图理解
    overall_strategy: str     # 整体分析策略
    steps: List[AnalysisStep]
    expected_insights: List[str]  # 预期能得出的洞察


@dataclass
class AnalysisResult:
    """分析结果"""
    success: bool
    plan: AnalysisPlan
    steps_completed: int
    final_analysis: str       # 最终综合分析
    data_points: List[Dict]   # 关键数据点
    recommendations: List[str]  # 行动建议
    confidence: float


class AgentAnalysisEngine:
    """
    智能分析引擎

    核心能力：
    1. 需求理解 - 分析用户真实意图和问题的复杂度
    2. 任务规划 - 将复杂问题拆解为多个分析步骤
    3. 多轮查询 - 按需执行多个 SQL 查询
    4. 综合分析 - 整合多维度数据给出深度洞察
    """

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.client = Anthropic(api_key=api_key or settings.ANTHROPIC_API_KEY)
        self.model = settings.AI_MODEL
        self.max_tokens = settings.AI_MAX_TOKENS
        self.temperature = settings.AI_TEMPERATURE

    async def analyze(
        self,
        question: str,
        schema: Dict[str, Any],
        data_source: Any,
        system_prompt: Optional[str] = None
    ) -> AnalysisResult:
        """
        执行完整分析流程

        Args:
            question: 用户问题
            schema: 数据库 Schema
            data_source: 数据源对象
            system_prompt: Agent 系统提示词

        Returns:
            AnalysisResult
        """
        # 第一步：需求理解和任务规划
        plan = await self._create_analysis_plan(question, schema, system_prompt)

        # 第二步：执行分析步骤
        completed_steps = 0
        for step in plan.steps:
            success = await self._execute_step(step, schema, data_source, plan)
            if success:
                completed_steps += 1

        # 第三步：综合分析
        final_analysis = await self._synthesize_analysis(plan, question)

        return AnalysisResult(
            success=completed_steps > 0,
            plan=plan,
            steps_completed=completed_steps,
            final_analysis=final_analysis["analysis"],
            data_points=final_analysis["data_points"],
            recommendations=final_analysis["recommendations"],
            confidence=final_analysis["confidence"]
        )

    async def _create_analysis_plan(
        self,
        question: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None
    ) -> AnalysisPlan:
        """
        创建分析计划 - 理解需求并拆解任务
        """
        schema_desc = self._format_schema(schema)

        prompt = f"""作为数据分析专家，请分析以下用户需求并制定分析计划。

## 用户需求
{question}

## 数据库 Schema
{schema_desc}

## 任务
请完成以下分析：

1. **判断任务类型**：这是简单查询还是复杂分析？
   - single_query: 简单单表查询
   - multi_query: 多表关联或多维度查询
   - attribution: 归因分析（找原因）
   - comparison: 对比分析
   - trend: 趋势分析
   - comprehensive: 综合分析

2. **理解用户意图**：用户真正想解决什么问题？

3. **制定分析策略**：需要哪些步骤来获取答案？

4. **拆解分析步骤**：将分析拆成 1-5 个具体步骤，每个步骤包括：
   - 步骤描述
   - 目的说明
   - **数据查询策略（重要）**：
     * 是否需要汇总多门店/多部门数据？→ 使用 SUM/COUNT + GROUP BY
     * 是否需要按维度拆分查看？→ 在 GROUP BY 中包含该维度
     * 只需明细？→ 使用简单 SELECT
   - 该步骤能得出什么洞察

5. **预期洞察**：完成分析后能得出哪些关键发现？

请以 JSON 格式输出：
```json
{{
    "task_type": "任务类型",
    "user_intent": "用户真实意图",
    "overall_strategy": "整体策略",
    "steps": [
        {{
            "step_id": "step_1",
            "description": "步骤描述",
            "purpose": "目的",
            "sql": "SQL查询",
            "expected_insight": "预期洞察"
        }}
    ],
    "expected_insights": ["洞察1", "洞察2"]
}}
```"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.3,
                system=system_prompt or "你是一位资深数据分析师，擅长将复杂业务问题拆解为可执行的分析步骤。",
                messages=[{"role": "user", "content": prompt}]
            )

            result = self._parse_json_response(response.content[0].text)

            steps = []
            for i, step_data in enumerate(result.get("steps", [])):
                steps.append(AnalysisStep(
                    step_id=step_data.get("step_id", f"step_{i+1}"),
                    description=step_data.get("description", ""),
                    purpose=step_data.get("purpose", ""),
                    sql=step_data.get("sql", ""),
                    insight=step_data.get("expected_insight", "")
                ))

            return AnalysisPlan(
                task_type=TaskType(result.get("task_type", "single_query")),
                user_intent=result.get("user_intent", ""),
                overall_strategy=result.get("overall_strategy", ""),
                steps=steps,
                expected_insights=result.get("expected_insights", [])
            )

        except Exception as e:
            # 如果规划失败，回退到简单单步分析
            return AnalysisPlan(
                task_type=TaskType.SINGLE_QUERY,
                user_intent=question,
                overall_strategy="直接查询",
                steps=[AnalysisStep(
                    step_id="step_1",
                    description="执行查询",
                    purpose="获取所需数据",
                    sql=""
                )],
                expected_insights=[]
            )

    async def _execute_step(
        self,
        step: AnalysisStep,
        schema: Dict[str, Any],
        data_source: Any,
        plan: AnalysisPlan
    ) -> bool:
        """
        执行单个分析步骤（包含Schema校验）
        """
        try:
            # 1. 如果没有 SQL，先生成 SQL
            if not step.sql or step.sql.strip() == "":
                step.sql = await self._generate_step_sql(step, schema, plan)

            # 2. Schema 校验与修正
            validation = self._validate_sql_schema(step.sql, schema)
            step.validation = validation

            if not validation.is_valid:
                # 尝试自动修正SQL
                fixed_sql = await self._fix_sql_schema(
                    step.sql, schema, validation.errors, plan
                )
                if fixed_sql and fixed_sql != step.sql:
                    step.sql = fixed_sql
                    # 重新验证
                    validation = self._validate_sql_schema(step.sql, schema)
                    step.validation = validation

                if not validation.is_valid:
                    step.insight = f"SQL校验失败: {'; '.join(validation.errors)}"
                    step.result = {"error": "Schema validation failed", "details": validation.errors}
                    return False

            # 3. 执行 SQL 查询
            if data_source.type == 'sqlite':
                result = self._execute_sqlite_query(step.sql, data_source.host)
            else:
                result = self._execute_db_query(step.sql, data_source)

            step.result = result

            # 4. 分析该步骤的结果
            step.insight = await self._analyze_step_result(step, plan)

            return True

        except Exception as e:
            step.insight = f"查询执行失败: {str(e)}"
            step.result = {"error": str(e)}
            return False

    def _validate_sql_schema(self, sql: str, schema: Dict[str, Any]) -> ValidationResult:
        """
        验证SQL中的表名和列名是否存在于Schema中

        Returns:
            ValidationResult: 验证结果，包含错误列表和修正建议
        """
        errors = []
        warnings = []
        validation_details = {
            "tables_checked": [],
            "columns_checked": [],
            "missing_tables": [],
            "missing_columns": []
        }

        # 提取schema中的有效表和列
        valid_tables = {}
        for table in schema.get("tables", []):
            table_name = table["name"].lower()
            valid_tables[table_name] = {
                "columns": [col["name"].lower() for col in table.get("columns", [])],
                "original_name": table["name"]
            }

        # 从SQL中提取表名（简化版，使用正则）
        # 匹配 FROM 和 JOIN 后面的表名
        from_pattern = re.compile(r'\bFROM\s+(\w+)', re.IGNORECASE)
        join_pattern = re.compile(r'\bJOIN\s+(\w+)', re.IGNORECASE)

        tables_in_sql = set()
        for match in from_pattern.finditer(sql):
            tables_in_sql.add(match.group(1).lower())
        for match in join_pattern.finditer(sql):
            tables_in_sql.add(match.group(1).lower())

        # 验证表名
        for table_name in tables_in_sql:
            validation_details["tables_checked"].append(table_name)
            if table_name not in valid_tables:
                errors.append(f"表 '{table_name}' 不存在于数据库中")
                validation_details["missing_tables"].append(table_name)
                # 尝试找相似的表名
                similar_tables = self._find_similar_names(table_name, list(valid_tables.keys()))
                if similar_tables:
                    warnings.append(f"您是否想查询表: {', '.join(similar_tables)}?")

        # 验证列名（只在表名正确的情况下）
        # 提取SELECT和WHERE中的列名
        column_pattern = re.compile(r'([a-zA-Z_]\w*)\s*[!=<>]+', re.IGNORECASE)
        select_pattern = re.compile(r'SELECT\s+(.+?)\s+FROM', re.IGNORECASE | re.DOTALL)

        columns_in_sql = set()

        # 从SELECT提取
        select_match = select_pattern.search(sql)
        if select_match:
            select_clause = select_match.group(1)
            # 分割多个列
            for col in select_clause.split(','):
                col = col.strip()
                # 处理别名和函数
                col = re.sub(r'\w+\(([^)]+)\)', r'\1', col)  # 去除函数包裹
                col = col.split()[-1]  # 取最后一部分（别名）
                col = col.split('.')[-1]  # 去除表名前缀
                if col and col != '*':
                    columns_in_sql.add(col.lower())

        # 从WHERE和条件提取
        for match in column_pattern.finditer(sql):
            col = match.group(1).lower()
            if col not in ['and', 'or', 'not', 'is', 'null', 'like', 'in', 'between']:
                columns_in_sql.add(col)

        # 验证列名（假设单表查询，简化处理）
        for table_name in tables_in_sql:
            if table_name in valid_tables:
                table_info = valid_tables[table_name]
                for col in columns_in_sql:
                    validation_details["columns_checked"].append(col)
                    if col not in table_info["columns"] and col != '*':
                        # 可能是别名或计算字段，先作为警告
                        similar_cols = self._find_similar_names(col, table_info["columns"])
                        if similar_cols:
                            warnings.append(f"列 '{col}' 在表 '{table_name}' 中不存在，您是否指: {', '.join(similar_cols)}?")
                        validation_details["missing_columns"].append({"table": table_name, "column": col})

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            validation_details=validation_details
        )

    def _find_similar_names(self, name: str, valid_names: List[str], threshold: float = 0.6) -> List[str]:
        """查找相似的名称（使用简单的编辑距离）"""
        similar = []
        name_lower = name.lower()

        for valid_name in valid_names:
            valid_lower = valid_name.lower()
            # 简单的相似度计算
            if name_lower in valid_lower or valid_lower in name_lower:
                similar.append(valid_name)
            elif self._levenshtein_ratio(name_lower, valid_lower) > threshold:
                similar.append(valid_name)

        return similar[:3]  # 最多返回3个建议

    def _levenshtein_ratio(self, s1: str, s2: str) -> float:
        """计算两个字符串的相似度（0-1）"""
        if len(s1) < len(s2):
            return self._levenshtein_ratio(s2, s1)

        if len(s2) == 0:
            return 0.0

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        distance = previous_row[-1]
        max_len = max(len(s1), len(s2))
        return 1 - (distance / max_len)

    async def _fix_sql_schema(
        self,
        sql: str,
        schema: Dict[str, Any],
        errors: List[str],
        plan: AnalysisPlan
    ) -> str:
        """
        使用AI自动修正SQL中的Schema错误
        """
        schema_desc = self._format_schema(schema)

        prompt = f"""请修正以下SQL查询中的Schema错误。

## 原始SQL
```sql
{sql}
```

## 检测到的错误
{chr(10).join(f"- {e}" for e in errors)}

## 正确的数据库Schema
{schema_desc}

## 分析背景
用户意图：{plan.user_intent}

## 任务
请根据正确的Schema修正SQL，确保：
1. 表名完全匹配Schema中的名称
2. 列名完全匹配Schema中的名称
3. 保持原始查询的意图不变

请以JSON格式输出：
```json
{{
    "fixed_sql": "修正后的SQL",
    "changes_made": ["修改1", "修改2"],
    "explanation": "修改说明"
}}
```"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )

            result = self._parse_json_response(response.content[0].text)
            fixed_sql = result.get("fixed_sql", sql)

            return fixed_sql

        except Exception as e:
            # 修正失败，返回原始SQL
            return sql

    async def _generate_step_sql(
        self,
        step: AnalysisStep,
        schema: Dict[str, Any],
        plan: AnalysisPlan
    ) -> str:
        """为步骤生成 SQL"""
        schema_desc = self._format_schema(schema)

        prompt = f"""基于以下分析步骤生成 SQL 查询。

## 分析背景
用户问题：{plan.user_intent}
整体策略：{plan.overall_strategy}

## 当前步骤
描述：{step.description}
目的：{step.purpose}

## 数据库 Schema
{schema_desc}

## 数据聚合规则（重要）

1. **默认汇总所有维度**：当查询商品/产品/品类时，**必须汇总所有门店/部门的数据**
   - ❌ 错误: `SELECT * FROM table WHERE 商品名称 = 'xxx'`（只返回部分数据）
   - ✅ 正确: `SELECT 商品名称, SUM(销售数量) as 总销量, SUM(销售金额) as 总销售额 FROM table WHERE 商品名称 = 'xxx' GROUP BY 商品名称`

2. **只有用户明确要求时才按维度拆分**：如"各门店销售情况"才使用 GROUP BY 部门名称

3. **使用聚合函数**：数量用 SUM()，金额用 SUM()，记录数用 COUNT()

## 要求
1. 只生成 SELECT 查询
2. 使用标准 SQL 语法（兼容 SQLite）
3. **必须使用适当的聚合和分组**
4. 为聚合列设置有意义的别名（如 总销量、总销售额）

请以 JSON 格式输出：
```json
{{
    "sql": "生成的 SQL",
    "explanation": "解释，包括如何处理多门店数据聚合"
}}
```"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}]
        )

        result = self._parse_json_response(response.content[0].text)
        return result.get("sql", "")

    def _execute_sqlite_query(self, sql: str, db_path: str) -> Dict:
        """执行 SQLite 查询"""
        if not os.path.isabs(db_path):
            db_path = os.path.abspath(db_path)

        engine = create_engine(f"sqlite:///{db_path}")
        with engine.connect() as conn:
            upper_sql = sql.upper().strip()
            if not upper_sql.startswith('SELECT'):
                raise ValueError("只允许 SELECT 查询")

            result = conn.execute(text(sql))
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]

            return {
                "columns": columns,
                "rows": rows,
                "total_rows": len(rows)
            }

    def _execute_db_query(self, sql: str, data_source: Any) -> Dict:
        """执行其他数据库查询"""
        # TODO: 实现其他数据库类型的查询
        return {"columns": [], "rows": [], "total_rows": 0}

    async def _analyze_step_result(
        self,
        step: AnalysisStep,
        plan: AnalysisPlan
    ) -> str:
        """分析步骤结果，提取洞察"""
        result_json = json.dumps(step.result, ensure_ascii=False, indent=2)

        prompt = f"""分析以下查询结果，提取关键洞察。

## 分析背景
用户问题：{plan.user_intent}
步骤描述：{step.description}
步骤目的：{step.purpose}

## 查询结果
```json
{result_json}
```

## 任务
1. 总结该步骤的关键发现（1-3 句话）
2. 指出数据中的异常或值得注意的点
3. 说明这个发现对回答用户问题的价值

请用简洁的中文回答。"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    async def _synthesize_analysis(
        self,
        plan: AnalysisPlan,
        original_question: str
    ) -> Dict:
        """
        综合分析所有步骤的结果
        """
        steps_analysis = []
        for step in plan.steps:
            steps_analysis.append({
                "step": step.description,
                "insight": step.insight,
                "data": step.result
            })

        # 收集验证信息
        validation_summary = []
        has_validation_issues = False
        for step in plan.steps:
            if step.validation:
                if not step.validation.is_valid:
                    has_validation_issues = True
                    validation_summary.append({
                        "step": step.description,
                        "errors": step.validation.errors,
                        "warnings": step.validation.warnings
                    })
                elif step.validation.warnings:
                    validation_summary.append({
                        "step": step.description,
                        "warnings": step.validation.warnings
                    })

        validation_context = ""
        if has_validation_issues:
            validation_context = f"""
## Schema验证警告
以下步骤在SQL生成过程中进行了自动修正：
```json
{json.dumps(validation_summary, ensure_ascii=False, indent=2)}
```
注意：分析结果基于修正后的查询，但仍需谨慎解读。
"""

        prompt = f"""基于多步骤分析的结果，给出综合结论和建议。

## 用户原始问题
{original_question}

## 用户意图
{plan.user_intent}

## 各步骤分析结果
```json
{json.dumps(steps_analysis, ensure_ascii=False, indent=2)}
```
{validation_context}

## 任务
请提供以下内容的 JSON 格式输出：

1. **综合分析** (analysis): 整合所有步骤的发现，给出完整回答（使用 Markdown 格式，包括表格）
2. **关键数据点** (data_points): 列出 3-5 个最重要的数据发现
3. **行动建议** (recommendations): 给出 2-4 条可执行的行动建议
4. **置信度** (confidence): 0-1 之间的数值，表示分析结论的可靠程度{" (考虑到验证警告，请适当降低置信度)" if has_validation_issues else ""}

```json
{{
    "analysis": "综合分析文本...",
    "data_points": [
        {{"metric": "指标名", "value": "值", "significance": "意义"}}
    ],
    "recommendations": ["建议1", "建议2"],
    "confidence": 0.85
}}
```"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.4,
                messages=[{"role": "user", "content": prompt}]
            )

            result = self._parse_json_response(response.content[0].text)

            return {
                "analysis": result.get("analysis", ""),
                "data_points": result.get("data_points", []),
                "recommendations": result.get("recommendations", []),
                "confidence": result.get("confidence", 0.5)
            }

        except Exception as e:
            # 如果综合分析失败，返回简单的汇总
            return {
                "analysis": f"分析完成，但综合报告生成失败: {str(e)}",
                "data_points": [],
                "recommendations": [],
                "confidence": 0.3
            }

    def _format_schema(self, schema: Dict[str, Any]) -> str:
        """格式化 Schema 描述"""
        desc = ""
        for table in schema.get("tables", []):
            desc += f"\n表: {table['name']}\n"
            for col in table.get("columns", []):
                desc += f"  - {col['name']}: {col['type']}\n"
        return desc

    def _parse_json_response(self, text: str) -> Dict:
        """从响应中提取 JSON"""
        # 尝试提取 markdown 中的 JSON
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试直接解析整个文本
            try:
                return json.loads(text)
            except:
                return {}
