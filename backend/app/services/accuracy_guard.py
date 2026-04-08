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
