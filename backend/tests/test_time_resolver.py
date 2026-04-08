import pytest
from datetime import datetime
from app.services.time_resolver import TimeResolver, TimeRange


class TestTimeResolver:
    def test_resolve_yesterday(self):
        """测试解析昨天"""
        resolver = TimeResolver()
        query_time = datetime(2026, 4, 8, 15, 30, 0)

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
        query_time = datetime(2026, 4, 8)

        result = resolver.resolve("上周", query_time)

        assert result.start == datetime(2026, 3, 30)
        assert result.end == datetime(2026, 4, 5, 23, 59, 59)

    def test_resolve_last_n_days(self):
        """测试解析最近N天"""
        resolver = TimeResolver()
        query_time = datetime(2026, 4, 8, 15, 30, 0)

        result = resolver.resolve("最近3天", query_time)

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

    def test_to_sql_condition(self):
        """测试生成 SQL 条件"""
        time_range = TimeRange(
            start=datetime(2026, 4, 7, 0, 0, 0),
            end=datetime(2026, 4, 7, 23, 59, 59)
        )

        sql = time_range.to_sql_condition("created_at")

        assert "created_at >= '2026-04-07 00:00:00'" in sql
        assert "created_at <= '2026-04-07 23:59:59'" in sql
