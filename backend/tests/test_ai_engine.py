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
