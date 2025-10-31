"""
日期工具函数模块

提供日期计算、格式化、解析等工具函数
"""

from datetime import datetime, timedelta
from typing import List, Optional, Union
import logging

logger = logging.getLogger(__name__)


def get_week_start(date_obj: Optional[datetime] = None) -> datetime:
    """
    获取给定日期所在周的周一日期

    Args:
        date_obj: 任意日期，默认为今天

    Returns:
        周一的日期对象（时间部分为00:00:00）
    """
    if date_obj is None:
        date_obj = datetime.now()

    # weekday() 返回 0-6，其中0是周一，6是周日
    days_since_monday = date_obj.weekday()
    monday = date_obj - timedelta(days=days_since_monday)

    # 清除时间部分，只保留日期
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)

    return monday


def get_week_dates(week_start: Optional[datetime] = None) -> List[datetime]:
    """
    获取一周（周一到周五）的日期列表

    Args:
        week_start: 周一日期，默认为本周一

    Returns:
        包含周一到周五的日期列表
    """
    if week_start is None:
        week_start = get_week_start()

    # 生成周一到周五的日期
    week_dates = [week_start + timedelta(days=i) for i in range(5)]

    return week_dates


def get_week_number(date_obj: Optional[datetime] = None) -> int:
    """
    获取给定日期是当年第几周（ISO 8601标准）

    Args:
        date_obj: 任意日期，默认为今天

    Returns:
        周数（1-53）
    """
    if date_obj is None:
        date_obj = datetime.now()

    # isocalendar() 返回 (year, week, weekday)
    return date_obj.isocalendar()[1]


def parse_date_flexible(date_value: Union[datetime, str, None]) -> Optional[datetime]:
    """
    灵活解析多种日期格式

    支持的格式：
    - datetime对象：直接返回
    - "2025/10/31"：斜杠分隔
    - "2025-10-31"：横杠分隔
    - "2025/1/5"：单数字月日

    Args:
        date_value: 日期值（可能是多种类型）

    Returns:
        解析后的datetime对象，解析失败返回None
    """
    if date_value is None:
        return None

    # 已经是datetime对象
    if isinstance(date_value, datetime):
        return date_value

    # 字符串格式
    if isinstance(date_value, str):
        # 尝试多种日期格式
        date_formats = [
            "%Y/%m/%d",      # 2025/10/31
            "%Y-%m-%d",      # 2025-10-31
            "%Y/%m/%-d",     # 2025/10/5 (Linux/macOS)
            "%Y/%-m/%d",     # 2025/1/31 (Linux/macOS)
            "%Y/%-m/%-d",    # 2025/1/5 (Linux/macOS)
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_value, fmt)
            except ValueError:
                continue

        logger.warning(f"无法解析日期字符串: {date_value}")
        return None

    logger.warning(f"不支持的日期类型: {type(date_value)}")
    return None


def is_date_match(date1: Union[datetime, str, None], date2: Union[datetime, str, None]) -> bool:
    """
    判断两个日期是否相同（只比较年月日，忽略时间）

    Args:
        date1: 第一个日期
        date2: 第二个日期

    Returns:
        是否相同
    """
    parsed1 = parse_date_flexible(date1)
    parsed2 = parse_date_flexible(date2)

    if parsed1 is None or parsed2 is None:
        return False

    return parsed1.date() == parsed2.date()


def format_date_chinese(date_obj: datetime) -> str:
    """
    将日期格式化为中文格式

    Args:
        date_obj: 日期对象

    Returns:
        "2025年10月31日 周五" 格式
    """
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekday_names[date_obj.weekday()]

    return f"{date_obj.year}年{date_obj.month}月{date_obj.day}日 {weekday}"


def get_week_range_str(week_start: Optional[datetime] = None) -> str:
    """
    获取一周的日期范围字符串

    Args:
        week_start: 周一日期，默认为本周一

    Returns:
        "2025-10-27 至 2025-10-31" 格式
    """
    if week_start is None:
        week_start = get_week_start()

    week_end = week_start + timedelta(days=4)  # 周五

    return f"{week_start.strftime('%Y-%m-%d')} 至 {week_end.strftime('%Y-%m-%d')}"
