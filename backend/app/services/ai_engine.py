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
