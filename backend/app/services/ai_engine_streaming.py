"""
AI 引擎 - 流式版本，支持思考模式
"""
import json
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, AsyncGenerator
from anthropic import Anthropic
from openai import AsyncOpenAI
from app.config import get_settings


@dataclass
class SQLGenerationResult:
    """SQL 生成结果"""
    sql: str
    explanation: str
    confidence: float
    needs_verification: bool = False
    reasoning: str = ""


class AIEngineStreaming:
    """
    AI 引擎流式版本：支持思考模式和流式输出
    """

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.provider = settings.AI_PROVIDER
        self.model = settings.AI_MODEL
        self.max_tokens = settings.AI_MAX_TOKENS
        self.temperature = settings.AI_TEMPERATURE
        self.enable_thinking = getattr(settings, 'QWEN_ENABLE_THINKING', True)

        if self.provider == "anthropic":
            self.client = Anthropic(api_key=api_key or settings.ANTHROPIC_API_KEY)
        elif self.provider == "qwen":
            # Qwen via OpenAI compatible API
            self.client = AsyncOpenAI(
                api_key=api_key or settings.QWEN_API_KEY,
                base_url=settings.QWEN_BASE_URL
            )
        else:
            raise ValueError(f"Unknown AI provider: {self.provider}")

    async def generate_sql_stream(
        self,
        question: str,
        schema: Dict[str, Any],
        resolved_time: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None,
        custom_system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式生成 SQL，实时返回思考过程和结果

        Yields:
            JSON 字符串，包含 type 和 content:
            - type: "thinking" - 思考过程
            - type: "sql" - 生成的 SQL
            - type: "explanation" - 解释说明
            - type: "complete" - 完成信号
        """
        system_prompt = custom_system_prompt or self._build_system_prompt(schema)
        user_prompt = self._build_user_prompt(question, resolved_time, schema)

        try:
            if self.provider == "qwen":
                # Qwen 流式调用
                extra_body = {}
                if self.enable_thinking:
                    extra_body["enable_search"] = True
                    extra_body["thinking"] = {"type": "enabled", "budget_tokens": 2000}

                stream = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    stream=True,
                    **extra_body
                )

                full_response = ""
                thinking_content = ""

                async for chunk in stream:
                    delta = chunk.choices[0].delta

                    # 处理思考内容（Qwen 思考模式）
                    if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                        thinking_content += delta.reasoning_content
                        yield json.dumps({
                            "type": "thinking",
                            "content": delta.reasoning_content
                        }, ensure_ascii=False) + "\n"

                    # 处理正式回复内容
                    if delta.content:
                        full_response += delta.content
                        # 尝试解析中间结果
                        if "SELECT" in full_response.upper() and full_response.count("{") > 0:
                            try:
                                result = self._parse_response(full_response)
                                if result.sql:
                                    yield json.dumps({
                                        "type": "sql",
                                        "content": result.sql,
                                        "confidence": result.confidence
                                    }, ensure_ascii=False) + "\n"
                            except:
                                pass

                # 最终解析
                result = self._parse_response(full_response)
                yield json.dumps({
                    "type": "complete",
                    "sql": result.sql,
                    "explanation": result.explanation,
                    "confidence": result.confidence,
                    "reasoning": result.reasoning or thinking_content
                }, ensure_ascii=False) + "\n"

            else:
                # Anthropic 流式调用
                async with self.client.messages.stream(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                ) as stream:
                    full_response = ""
                    async for text in stream.text_stream:
                        full_response += text
                        yield json.dumps({
                            "type": "thinking",
                            "content": text
                        }, ensure_ascii=False) + "\n"

                result = self._parse_response(full_response)
                yield json.dumps({
                    "type": "complete",
                    "sql": result.sql,
                    "explanation": result.explanation,
                    "confidence": result.confidence
                }, ensure_ascii=False) + "\n"

        except Exception as e:
            yield json.dumps({
                "type": "error",
                "message": str(e)
            }, ensure_ascii=False) + "\n"

    async def interpret_results_stream(
        self,
        question: str,
        sql: str,
        results: List[Dict],
        total_rows: int
    ) -> AsyncGenerator[str, None]:
        """流式解读查询结果"""
        prompt = f"""用户问题: {question}

执行的 SQL: {sql}

查询结果（共 {total_rows} 行，显示前 {len(results)} 行）:
{json.dumps(results, ensure_ascii=False, indent=2)}

请用 1-3 句话总结结果，直接回答用户的问题。"""

        try:
            if self.provider == "qwen":
                extra_body = {}
                if self.enable_thinking:
                    extra_body["enable_search"] = True

                stream = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.3,
                    stream=True,
                    **extra_body
                )

                full_text = ""
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        text = chunk.choices[0].delta.content
                        full_text += text
                        yield json.dumps({"type": "content", "text": text}, ensure_ascii=False) + "\n"

                yield json.dumps({"type": "complete", "content": full_text}, ensure_ascii=False) + "\n"

        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)}, ensure_ascii=False) + "\n"

    def _build_system_prompt(self, schema: Dict[str, Any]) -> str:
        """构建系统提示词"""
        schema_desc = "数据库 Schema:\n"
        for table in schema.get("tables", []):
            schema_desc += f"\n表: {table['name']}\n"
            for col in table.get("columns", []):
                schema_desc += f"  - {col['name']}: {col['type']}\n"

        prompt = f"""你是一个专业的 SQL 生成专家。根据用户的问题和数据库 Schema，生成准确、高效的 SQL 查询。

{schema_desc}

## 数据聚合规则（重要）

1. **默认汇总所有维度**：当用户查询商品/产品/品类时，**默认应该汇总所有门店/部门的数据**
   - ❌ 错误: `SELECT * FROM table WHERE 商品名称 = 'xxx' AND 部门名称 = '门店A'`
   - ✅ 正确: `SELECT 商品名称, SUM(销售数量) as 总销量, SUM(销售金额) as 总销售额 FROM table WHERE 商品名称 = 'xxx' GROUP BY 商品名称`

2. **区分汇总和明细**：
   - 用户问"xxx的销售情况/有多少"→ 返回汇总数据（SUM/COUNT）
   - 用户问"各门店/各部门/各区域的销售"→ 按该维度 GROUP BY
   - 用户问"明细/详情/列表"→ 返回明细行

3. **多门店数据处理**：
   - 同一商品在不同门店销售时，**必须汇总展示总数**
   - 只有用户明确要求"按门店查看"时才分开显示

## SQL 生成规则

1. 只生成 SELECT 查询，禁止生成 INSERT/UPDATE/DELETE/DROP 等修改性语句
2. 使用标准 SQL 语法，兼容 SQLite/PostgreSQL
3. 时间条件使用 WHERE 子句，格式: column >= 'YYYY-MM-DD HH:MM:SS' AND column <= 'YYYY-MM-DD HH:MM:SS'
4. 聚合查询使用 GROUP BY，并为聚合列设置别名（如 SUM(销售数量) as 总销量）
5. 排序使用 ORDER BY，限制返回数量使用 LIMIT
6. 如果问题不明确，生成最可能的 SQL 并标记需要验证

输出格式（JSON）:
{{
    "sql": "生成的 SQL 语句",
    "explanation": "SQL 的作用解释（中文）",
    "confidence": 0.95,
    "reasoning": "生成思路，包括如何处理多门店数据聚合"
}}

注意: 只输出 JSON，不要有其他内容。"""

        return prompt

    def _build_user_prompt(
        self,
        question: str,
        resolved_time: Optional[Dict[str, Any]] = None,
        schema: Optional[Dict[str, Any]] = None
    ) -> str:
        """构建用户提示词"""
        prompt = f"用户问题: {question}\n"

        if resolved_time:
            prompt += f"\n已解析的时间范围:\n"
            for expr, time_range in resolved_time.items():
                prompt += f"  - {expr}: {time_range['start']} 至 {time_range['end']}\n"

        if schema:
            prompt += f"\n数据库 Schema:\n"
            for table in schema.get("tables", []):
                prompt += f"\n表: {table['name']}\n"
                for col in table.get("columns", []):
                    prompt += f"  - {col['name']}: {col['type']}\n"

        prompt += "\n请生成 SQL 查询。"

        return prompt

    def _parse_response(self, response_text: str) -> SQLGenerationResult:
        """解析 AI 响应"""
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
