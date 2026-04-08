from dataclasses import dataclass
from datetime import datetime, timedelta
from calendar import monthrange
import re


@dataclass
class TimeRange:
    """时间范围"""
    start: datetime
    end: datetime

    def to_sql_condition(self, field: str) -> str:
        """转换为 SQL WHERE 条件"""
        start_str = self.start.strftime("%Y-%m-%d %H:%M:%S")
        end_str = self.end.strftime("%Y-%m-%d %H:%M:%S")
        return f"{field} >= '{start_str}' AND {field} <= '{end_str}'"


class TimeResolver:
    """
    解析自然语言中的相对时间为绝对时间范围
    基于查询时的真实当前时间
    """

    # 正则表达式模式
    PATTERNS = {
        'yesterday': r'^(昨天|昨日)$',
        'today': r'^(今天|今日)$',
        'last_week': r'^(上周|上星期|上个星期)$',
        'this_week': r'^(本周|这星期|这个星期)$',
        'last_month': r'^(上月|上个月|上月)$',
        'this_month': r'^(本月|这个月)$',
        'last_n_days': r'^(?:最近|近)(\d+)[天日]$',
        'this_year': r'^(今年|本年度)$',
        'last_year': r'^(去年|上年度)$',
    }

    def resolve(self, expression: str, query_time: datetime = None) -> TimeRange | None:
        """
        解析时间表达式

        Args:
            expression: 自然语言时间表达式，如 "昨天"
            query_time: 查询时的基准时间，默认为当前时间

        Returns:
            TimeRange 或 None（无法解析时）
        """
        if query_time is None:
            query_time = datetime.now()

        expression = expression.strip().lower()

        # 昨天
        if re.match(self.PATTERNS['yesterday'], expression):
            yesterday = query_time - timedelta(days=1)
            return TimeRange(
                start=yesterday.replace(hour=0, minute=0, second=0, microsecond=0),
                end=yesterday.replace(hour=23, minute=59, second=59, microsecond=0)
            )

        # 今天
        if re.match(self.PATTERNS['today'], expression):
            return TimeRange(
                start=query_time.replace(hour=0, minute=0, second=0, microsecond=0),
                end=query_time.replace(hour=23, minute=59, second=59, microsecond=0)
            )

        # 上周（自然周，上周一到上周日）
        if re.match(self.PATTERNS['last_week'], expression):
            # 获取本周一
            days_since_monday = query_time.weekday()
            this_monday = query_time - timedelta(days=days_since_monday)
            last_monday = this_monday - timedelta(days=7)
            last_sunday = last_monday + timedelta(days=6)
            return TimeRange(
                start=last_monday.replace(hour=0, minute=0, second=0, microsecond=0),
                end=last_sunday.replace(hour=23, minute=59, second=59, microsecond=0)
            )

        # 本周
        if re.match(self.PATTERNS['this_week'], expression):
            days_since_monday = query_time.weekday()
            this_monday = query_time - timedelta(days=days_since_monday)
            return TimeRange(
                start=this_monday.replace(hour=0, minute=0, second=0, microsecond=0),
                end=query_time.replace(hour=23, minute=59, second=59, microsecond=0)
            )

        # 上月
        if re.match(self.PATTERNS['last_month'], expression):
            first_day_this_month = query_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            first_day_last_month = last_day_last_month.replace(day=1)
            last_day = monthrange(first_day_last_month.year, first_day_last_month.month)[1]
            return TimeRange(
                start=first_day_last_month,
                end=first_day_last_month.replace(day=last_day, hour=23, minute=59, second=59)
            )

        # 本月
        if re.match(self.PATTERNS['this_month'], expression):
            first_day = query_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_day = monthrange(query_time.year, query_time.month)[1]
            return TimeRange(
                start=first_day,
                end=first_day.replace(day=last_day, hour=23, minute=59, second=59)
            )

        # 最近N天
        match = re.match(self.PATTERNS['last_n_days'], expression)
        if match:
            n = int(match.group(1))
            start_date = query_time - timedelta(days=n-1)
            return TimeRange(
                start=start_date.replace(hour=0, minute=0, second=0, microsecond=0),
                end=query_time.replace(hour=23, minute=59, second=59, microsecond=0)
            )

        # 去年
        if re.match(self.PATTERNS['last_year'], expression):
            last_year = query_time.year - 1
            return TimeRange(
                start=datetime(last_year, 1, 1, 0, 0, 0),
                end=datetime(last_year, 12, 31, 23, 59, 59)
            )

        # 今年
        if re.match(self.PATTERNS['this_year'], expression):
            return TimeRange(
                start=datetime(query_time.year, 1, 1, 0, 0, 0),
                end=query_time.replace(hour=23, minute=59, second=59, microsecond=0)
            )

        return None
