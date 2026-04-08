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
