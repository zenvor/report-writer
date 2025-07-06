#!/usr/bin/env python3
"""
ReportWriter - 自动化日报写入工具

参考 webrtc-streamer 的设计理念，提供简洁而强大的命令行界面。
"""

import argparse
import sys
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from config_manager import config, ConfigurationError
from updater import ReportUpdater, ReportUpdaterError
from scheduler import ReportScheduler, SchedulerError

# 版本信息
__version__ = "1.0.0"

# 程序信息
PROGRAM_NAME = "ReportWriter"
PROGRAM_DESC = "自动化日报写入工具"

# 默认配置
DEFAULT_CONFIG_FILE = "config.json"
DEFAULT_DATA_DIR = "data"
DEFAULT_EXCEL_FILE = "月报.xlsx"

logger = logging.getLogger(__name__)


class ReportWriterError(Exception):
    """ReportWriter 主程序异常"""
    pass


def find_excel_file(data_dir: str = DEFAULT_DATA_DIR) -> Optional[str]:
    """自动查找Excel文件"""
    data_path = Path(data_dir)
    
    if not data_path.exists():
        return None
    
    # 查找.xlsx文件
    excel_files = list(data_path.glob("*.xlsx"))
    
    if not excel_files:
        return None
    
    # 优先返回包含"月报"的文件
    for file in excel_files:
        if "月报" in file.name:
            return str(file)
    
    # 返回第一个找到的Excel文件
    return str(excel_files[0])


def print_version():
    """打印版本信息"""
    print(f"{PROGRAM_NAME} v{__version__}")
    print(f"{PROGRAM_DESC}")
    print()
    print("构建信息:")
    print(f"  Python版本: {sys.version.split()[0]}")
    print(f"  配置文件: {DEFAULT_CONFIG_FILE}")
    print(f"  数据目录: {DEFAULT_DATA_DIR}")


def print_help():
    """打印帮助信息"""
    print(f"./report-writer [-f Excel文件] [-d YYYY-MM-DD] [-w 工时] [-v[v[v]]] [--daemon|--run-once|--health-check|--status]")
    print(f"./report-writer [-C config.json] [--gitlab-url URL] [--gitlab-token TOKEN] [--gitlab-project ID] [--gitlab-branch BRANCH] [--deepseek-key KEY]")
    print(f"./report-writer -V")
    print()
    print("  -v[v[v]]           : 日志详细程度 (v=INFO, vv=DEBUG, vvv=TRACE)")
    print("  -V                 : 显示版本信息")
    print("  -C config.json     : 加载配置文件 (默认: config.json)")
    print("  -f Excel文件       : 指定Excel文件路径")
    print("  -d YYYY-MM-DD      : 指定日期 (默认: 今天)")
    print("  -w 工时            : 指定工作小时数 (默认: 8)")
    print("  [Excel文件路径]    : 要处理的Excel文件路径")
    print()
    print("  --run-once         : 执行一次更新后退出")
    print("  --daemon           : 启动守护进程模式 (定时调度)")
    print("  --health-check     : 执行健康检查")
    print("  --status           : 显示调度器状态")
    print()
    print("  --gitlab-url URL   : GitLab服务器地址")
    print("  --gitlab-token TOKEN : GitLab访问令牌")
    print("  --gitlab-project ID : 项目ID")
    print("  --gitlab-branch BRANCH : 分支名称 (默认: dev)")
    print()
    print("  --deepseek-key KEY : Deepseek API密钥")
    print()
    print("示例:")
    print(f"  {PROGRAM_NAME}                    # 自动查找Excel文件并执行一次更新")
    print(f"  {PROGRAM_NAME} --daemon           # 启动定时调度模式")
    print(f"  {PROGRAM_NAME} -f data/月报.xlsx  # 指定Excel文件")
    print(f"  {PROGRAM_NAME} -d 2025-01-15      # 指定日期")
    print(f"  {PROGRAM_NAME} --health-check     # 健康检查")
    print(f"  {PROGRAM_NAME} -V                 # 显示版本")


def setup_logging(verbosity: int):
    """设置日志级别"""
    if verbosity == 0:
        level = logging.WARNING
    elif verbosity == 1:
        level = logging.INFO
    elif verbosity == 2:
        level = logging.DEBUG
    else:
        level = logging.DEBUG
    
    # 更新配置中的日志级别
    logging.getLogger().setLevel(level)
    
    # 为控制台输出设置更简洁的格式
    console_handler = None
    for handler in logging.getLogger().handlers:
        if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stderr:
            console_handler = handler
            break
    
    if console_handler and verbosity > 0:
        console_handler.setFormatter(
            logging.Formatter('%(levelname)s: %(message)s')
        )


def validate_date(date_str: str) -> datetime:
    """验证并解析日期字符串"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ReportWriterError(f"日期格式错误: {date_str}，应为 YYYY-MM-DD")


def validate_hours(hours_str: str) -> int:
    """验证并解析工作小时数"""
    try:
        hours = int(hours_str)
        if hours < 0 or hours > 24:
            raise ReportWriterError(f"工作小时数必须在 0-24 范围内: {hours}")
        return hours
    except ValueError:
        raise ReportWriterError(f"工作小时数必须是整数: {hours_str}")


def run_once_mode(excel_file: str, date_obj: datetime, hours: int) -> bool:
    """执行一次更新模式"""
    logger.info(f"执行一次更新: {excel_file}, 日期: {date_obj.strftime('%Y-%m-%d')}, 工时: {hours}")
    
    try:
        updater = ReportUpdater()
        success = updater.update_daily_report(excel_file, date_obj, hours)
        
        if success:
            print(f"✅ 日报更新成功: {date_obj.strftime('%Y-%m-%d')}")
            return True
        else:
            print(f"❌ 日报更新失败: {date_obj.strftime('%Y-%m-%d')}")
            return False
            
    except ReportUpdaterError as e:
        logger.error(f"更新失败: {e}")
        print(f"❌ 更新失败: {e}")
        return False
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"❌ 程序执行失败: {e}")
        return False


def daemon_mode(excel_file: str) -> bool:
    """守护进程模式"""
    logger.info(f"启动守护进程模式: {excel_file}")
    
    try:
        scheduler = ReportScheduler(excel_file)
        
        print(f"🚀 启动日报调度器")
        print(f"📁 Excel文件: {excel_file}")
        
        # 显示调度信息
        next_run = scheduler.get_next_run_time()
        if next_run:
            print(f"⏰ 下次执行时间: {next_run}")
        
        print("按 Ctrl+C 停止调度器")
        print()
        
        scheduler.start()
        return True
        
    except SchedulerError as e:
        logger.error(f"调度器错误: {e}")
        print(f"❌ 调度器错误: {e}")
        return False
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"❌ 程序执行失败: {e}")
        return False


def health_check_mode() -> bool:
    """健康检查模式"""
    logger.info("执行健康检查")
    
    try:
        updater = ReportUpdater()
        status = updater.health_check()
        
        print("🔍 健康检查结果:")
        print(f"  GitLab连接: {'✅' if status.get('gitlab_connection') else '❌'}")
        print(f"  Deepseek API: {'✅' if status.get('deepseek_api_key') else '❌'}")
        print(f"  配置加载: {'✅' if status.get('config_loaded') else '❌'}")
        
        all_good = all(status.values())
        if all_good:
            print("✅ 所有检查项目正常")
        else:
            print("⚠️  部分检查项目异常，请检查配置")
        
        return all_good
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        print(f"❌ 健康检查失败: {e}")
        return False


def status_mode(excel_file: str) -> bool:
    """状态查看模式"""
    logger.info("查看调度器状态")
    
    try:
        scheduler = ReportScheduler(excel_file)
        status = scheduler.get_job_status()
        
        print("📊 调度器状态:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        logger.error(f"查看状态失败: {e}")
        print(f"❌ 查看状态失败: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description=f"{PROGRAM_NAME} - {PROGRAM_DESC}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                    # 自动查找Excel文件并执行一次更新
  %(prog)s --daemon           # 启动定时调度模式
  %(prog)s -f data/月报.xlsx  # 指定Excel文件
  %(prog)s -d 2025-01-15      # 指定日期
  %(prog)s --health-check     # 健康检查
  %(prog)s -V                 # 显示版本

环境变量:
  GITLAB_URL                  # GitLab服务器地址
  GITLAB_TOKEN                # GitLab访问令牌
  GITLAB_PROJECT_ID           # 项目ID
  GITLAB_BRANCH               # 分支名称
  DEEPSEEK_API_KEY            # Deepseek API密钥
        """,
        add_help=False
    )
    
    # 基本选项
    parser.add_argument("-h", "--help", action="store_true", help="显示帮助信息")
    parser.add_argument("-V", "--version", action="store_true", help="显示版本信息")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="增加日志详细程度")
    parser.add_argument("-C", "--config", default=DEFAULT_CONFIG_FILE, help="配置文件路径")
    
    # 文件和日期选项
    parser.add_argument("-f", "--file", help="Excel文件路径")
    parser.add_argument("-d", "--date", help="日期 YYYY-MM-DD")
    parser.add_argument("-w", "--hours", type=int, default=8, help="工作小时数")
    parser.add_argument("excel_file", nargs="?", help="Excel文件路径")
    
    # 模式选项
    parser.add_argument("--run-once", action="store_true", help="执行一次更新后退出")
    parser.add_argument("--daemon", action="store_true", help="启动守护进程模式")
    parser.add_argument("--health-check", action="store_true", help="执行健康检查")
    parser.add_argument("--status", action="store_true", help="显示调度器状态")
    
    # GitLab选项
    parser.add_argument("--gitlab-url", help="GitLab服务器地址")
    parser.add_argument("--gitlab-token", help="GitLab访问令牌")
    parser.add_argument("--gitlab-project", help="项目ID")
    parser.add_argument("--gitlab-branch", help="分支名称")
    
    # AI选项
    parser.add_argument("--deepseek-key", help="Deepseek API密钥")
    
    args = parser.parse_args()
    
    # 处理帮助和版本
    if args.help:
        print_help()
        return 0
    
    if args.version:
        print_version()
        return 0
    
    # 设置日志级别
    setup_logging(args.verbose)
    
    try:
        # 临时设置环境变量（如果通过命令行提供）
        if args.gitlab_url:
            os.environ["GITLAB_URL"] = args.gitlab_url
        if args.gitlab_token:
            os.environ["GITLAB_TOKEN"] = args.gitlab_token
        if args.gitlab_project:
            os.environ["GITLAB_PROJECT_ID"] = args.gitlab_project
        if args.gitlab_branch:
            os.environ["GITLAB_BRANCH"] = args.gitlab_branch
        if args.deepseek_key:
            os.environ["DEEPSEEK_API_KEY"] = args.deepseek_key
        
        # 健康检查模式
        if args.health_check:
            success = health_check_mode()
            return 0 if success else 1
        
        # 确定Excel文件路径
        excel_file = args.file or args.excel_file
        if not excel_file:
            excel_file = find_excel_file()
            if not excel_file:
                print("❌ 未找到Excel文件，请使用 -f 选项指定文件路径")
                return 1
            print(f"📁 自动找到Excel文件: {excel_file}")
        
        # 验证Excel文件存在
        if not os.path.exists(excel_file):
            print(f"❌ Excel文件不存在: {excel_file}")
            return 1
        
        # 状态查看模式
        if args.status:
            success = status_mode(excel_file)
            return 0 if success else 1
        
        # 守护进程模式
        if args.daemon:
            success = daemon_mode(excel_file)
            return 0 if success else 1
        
        # 默认或指定的一次性运行模式
        date_obj = validate_date(args.date) if args.date else datetime.now()
        hours = args.hours
        
        success = run_once_mode(excel_file, date_obj, hours)
        return 0 if success else 1
        
    except ReportWriterError as e:
        print(f"❌ {e}")
        return 1
    except ConfigurationError as e:
        print(f"❌ 配置错误: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n👋 用户中断，程序退出")
        return 0
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"❌ 程序执行失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 