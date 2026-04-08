import time
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass
class QueryResult:
    """查询结果"""
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_rows: int
    execution_time_ms: int
    sql: str
    is_cached: bool = False


class QueryExecutor:
    """
    SQL 执行器：负责安全执行查询和结果处理
    """

    # 禁止的关键字（只允许 SELECT）
    FORBIDDEN_KEYWORDS = [
        r'\bDELETE\b',
        r'\bUPDATE\b',
        r'\bINSERT\b',
        r'\bDROP\b',
        r'\bCREATE\b',
        r'\bALTER\b',
        r'\bTRUNCATE\b',
        r'\bGRANT\b',
        r'\bREVOKE\b',
    ]

    def __init__(self, db_session: Session):
        self.db = db_session

    def execute(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        max_rows: int = 1000
    ) -> Optional[QueryResult]:
        """
        执行 SQL 查询

        Args:
            sql: SQL 语句
            params: 查询参数
            max_rows: 最大返回行数

        Returns:
            QueryResult 或 None（执行失败）
        """
        # 安全检查
        if not self._is_safe_sql(sql):
            raise ValueError("不安全的 SQL：只允许 SELECT 查询")

        # 限制返回数量
        if "LIMIT" not in sql.upper():
            sql = f"{sql} LIMIT {max_rows}"

        start_time = time.time()

        try:
            # 执行查询
            result = self.db.execute(text(sql), params or {})

            # 获取列名
            columns = list(result.keys())

            # 获取结果
            rows = []
            for row in result.fetchall():
                rows.append(dict(zip(columns, row)))

            execution_time = int((time.time() - start_time) * 1000)

            return QueryResult(
                columns=columns,
                rows=rows,
                total_rows=len(rows),
                execution_time_ms=execution_time,
                sql=sql
            )

        except Exception as e:
            raise RuntimeError(f"查询执行失败: {str(e)}")

    def _is_safe_sql(self, sql: str) -> bool:
        """检查 SQL 是否安全（只允许 SELECT）"""
        upper_sql = sql.upper().strip()

        # 必须以 SELECT 开头
        if not upper_sql.startswith('SELECT'):
            return False

        # 检查禁止的关键字
        for pattern in self.FORBIDDEN_KEYWORDS:
            if re.search(pattern, upper_sql, re.IGNORECASE):
                return False

        return True

    def validate_syntax(self, sql: str) -> tuple[bool, Optional[str]]:
        """
        验证 SQL 语法（使用 EXPLAIN）

        Returns:
            (是否有效, 错误信息)
        """
        try:
            explain_sql = f"EXPLAIN {sql}"
            self.db.execute(text(explain_sql))
            return True, None
        except Exception as e:
            return False, str(e)
