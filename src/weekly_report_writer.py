"""
周报生成器模块

从月报文件中读取本周日报内容并自动填入周报表格
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

from date_utils import get_week_start, get_week_dates, is_date_match, format_date_chinese, get_week_range_str

logger = logging.getLogger(__name__)

# 常量定义
MONTHLY_DATE_COLUMN = 6     # 月报中的日期列（F列）
MONTHLY_CONTENT_COLUMN = 7  # 月报中的内容列（G列）
MONTHLY_START_ROW = 3       # 月报数据起始行

WEEKLY_CONTENT_COLUMN = 2   # 周报中的事项列（B列）
WEEKLY_START_ROW = 3        # 周报数据起始行（序号1对应第3行）


class WeeklyReportWriterError(Exception):
    """周报生成器异常"""
    pass


class WeeklyReportWriter:
    """
    周报生成器

    从月报文件中读取本周一到周五的日报内容，
    按时间顺序填入周报Excel的"完成重点工作"表格
    """

    def __init__(self, monthly_report_path: str, weekly_report_path: str):
        """
        初始化周报生成器

        Args:
            monthly_report_path: 月报文件路径
            weekly_report_path: 周报文件路径
        """
        self.monthly_report_path = Path(monthly_report_path)
        self.weekly_report_path = Path(weekly_report_path)

        # 验证文件存在
        if not self.monthly_report_path.exists():
            raise WeeklyReportWriterError(f"月报文件不存在: {monthly_report_path}")

        if not self.weekly_report_path.exists():
            raise WeeklyReportWriterError(f"周报文件不存在: {weekly_report_path}")

        logger.info(f"周报生成器初始化 - 月报: {self.monthly_report_path.name}, 周报: {self.weekly_report_path.name}")

    def generate_weekly_report(self, week_start_date: Optional[datetime] = None) -> bool:
        """
        生成周报

        Args:
            week_start_date: 周一日期，默认为本周一

        Returns:
            是否成功
        """
        try:
            # 计算本周一
            if week_start_date is None:
                week_start_date = get_week_start()
            else:
                # 确保传入的日期是周一
                week_start_date = get_week_start(week_start_date)

            week_range = get_week_range_str(week_start_date)
            logger.info(f"开始生成周报 - 周期: {week_range}")

            # 读取本周日报内容
            weekly_contents = self._read_weekly_reports(week_start_date)

            # 统计读取结果
            found_count = sum(1 for content in weekly_contents if content is not None)
            logger.info(f"从月报中读取到 {found_count}/5 天的日报内容")

            if found_count == 0:
                logger.warning("未找到任何日报内容，请检查月报文件")
                return False

            # 写入周报
            self._write_to_weekly_report(weekly_contents)

            logger.info("✅ 周报生成成功")
            return True

        except Exception as e:
            logger.error(f"❌ 生成周报失败: {e}", exc_info=True)
            return False

    def _read_weekly_reports(self, monday: datetime) -> List[Optional[str]]:
        """
        从月报中读取本周一到周五的日报内容

        Args:
            monday: 周一日期

        Returns:
            包含5个元素的列表，对应周一到周五的日报内容，未找到的为None
        """
        try:
            workbook = load_workbook(self.monthly_report_path, data_only=True)
            worksheet = workbook.active

            weekly_contents = []
            weekday_names = ["周一", "周二", "周三", "周四", "周五"]

            # 获取本周一到周五的日期
            week_dates = get_week_dates(monday)

            for i, target_date in enumerate(week_dates):
                weekday_name = weekday_names[i]
                date_str = format_date_chinese(target_date)

                # 在月报中查找对应日期
                content = None
                for row_idx in range(MONTHLY_START_ROW, worksheet.max_row + 1):
                    cell_date = worksheet.cell(row=row_idx, column=MONTHLY_DATE_COLUMN).value

                    if is_date_match(cell_date, target_date):
                        content = worksheet.cell(row=row_idx, column=MONTHLY_CONTENT_COLUMN).value

                        if content:
                            content = str(content).strip()  # 清理空白字符
                            logger.info(f"  ✓ {date_str}: 找到日报内容 (月报第{row_idx}行)")
                        else:
                            logger.warning(f"  ⚠ {date_str}: 日报内容为空 (月报第{row_idx}行)")
                            content = None
                        break

                if content is None:
                    logger.warning(f"  ✗ {date_str}: 未找到日报")

                weekly_contents.append(content)

            workbook.close()
            return weekly_contents

        except InvalidFileException as e:
            raise WeeklyReportWriterError(f"无法打开月报文件，可能格式不正确: {e}")
        except Exception as e:
            raise WeeklyReportWriterError(f"读取月报文件失败: {e}")

    def _write_to_weekly_report(self, contents: List[Optional[str]]) -> None:
        """
        将日报内容写入周报

        Args:
            contents: 包含5个元素的列表，对应周一到周五的日报内容
        """
        try:
            workbook = load_workbook(self.weekly_report_path)
            worksheet = workbook.active

            weekday_names = ["周一", "周二", "周三", "周四", "周五"]
            write_count = 0

            # 填写内容到对应序号（保持序号1-5对应周一到周五）
            for i, content in enumerate(contents):
                sequence_number = i + 1  # 序号1-5
                target_row = WEEKLY_START_ROW + i  # B3-B7行

                if content:
                    # 写入内容
                    cell = worksheet.cell(row=target_row, column=WEEKLY_CONTENT_COLUMN)
                    cell.value = content

                    # 设置自动换行（与日报保持一致）
                    from openpyxl.styles import Alignment
                    cell.alignment = Alignment(wrap_text=True, vertical='top')

                    logger.info(f"  ✓ 序号{sequence_number}({weekday_names[i]}): 写入周报第{target_row}行")
                    write_count += 1
                else:
                    # 保持该行为空（不覆盖已有内容）
                    logger.debug(f"  - 序号{sequence_number}({weekday_names[i]}): 无内容，跳过")

            # 保存文件
            workbook.save(self.weekly_report_path)
            workbook.close()

            logger.info(f"成功写入 {write_count}/5 天的日报到周报文件")

        except PermissionError:
            raise WeeklyReportWriterError(f"无法写入周报文件，文件可能被占用: {self.weekly_report_path}")
        except Exception as e:
            raise WeeklyReportWriterError(f"写入周报文件失败: {e}")

    def preview_weekly_report(self, week_start_date: Optional[datetime] = None) -> Dict[str, Optional[str]]:
        """
        预览周报内容（不写入文件）

        Args:
            week_start_date: 周一日期，默认为本周一

        Returns:
            字典，键为"周一"到"周五"，值为对应的日报内容
        """
        if week_start_date is None:
            week_start_date = get_week_start()
        else:
            week_start_date = get_week_start(week_start_date)

        weekly_contents = self._read_weekly_reports(week_start_date)
        weekday_names = ["周一", "周二", "周三", "周四", "周五"]

        return {
            weekday_names[i]: content
            for i, content in enumerate(weekly_contents)
        }
