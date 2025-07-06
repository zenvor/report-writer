import logging
import os
import signal
import sys
from datetime import datetime
from typing import Optional, Dict, Any

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from config_manager import config, ConfigurationError
from updater import ReportUpdater, ReportUpdaterError

logger = logging.getLogger(__name__)

# 常量定义
DEFAULT_SCHEDULE_HOUR = 18
DEFAULT_SCHEDULE_MINUTE = 0
DEFAULT_TIMEZONE = "Asia/Shanghai"
MISFIRE_GRACE_TIME = 3600  # 1小时

class SchedulerError(Exception):
    """调度器异常"""
    pass

class ReportScheduler:
    """日报调度器，负责定时执行日报更新任务"""
    
    def __init__(self, excel_path: str):
        self.excel_path = self._validate_excel_path(excel_path)
        self.updater = ReportUpdater()
        self.scheduler = BlockingScheduler()
        self.is_running = False
        
        # 设置信号处理
        self._setup_signal_handlers()
        
        # 设置调度器
        self._setup_scheduler()
        
        # 添加事件监听器
        self._setup_event_listeners()
    
    def _validate_excel_path(self, excel_path: str) -> str:
        """验证Excel文件路径"""
        if not os.path.exists(excel_path):
            raise SchedulerError(f"Excel 文件不存在: {excel_path}")
        
        if not excel_path.lower().endswith('.xlsx'):
            raise SchedulerError(f"文件格式不正确，需要 .xlsx 文件: {excel_path}")
        
        return excel_path
    
    def _setup_signal_handlers(self) -> None:
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，正在优雅关闭...")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _setup_scheduler(self) -> None:
        """设置调度任务"""
        if not config.get("schedule.enabled", True):
            logger.info("调度功能已禁用")
            return
        
        # 从配置中获取调度时间
        schedule_config = self._get_schedule_config()
        
        logger.info(f"设置定时任务: 每天 {schedule_config['hour']:02d}:{schedule_config['minute']:02d} ({schedule_config['timezone']})")
        
        # 创建 cron 触发器
        trigger = CronTrigger(
            hour=schedule_config['hour'],
            minute=schedule_config['minute'],
            timezone=schedule_config['timezone']
        )
        
        # 添加任务
        self.scheduler.add_job(
            func=self._run_daily_update,
            trigger=trigger,
            id="daily_report_update",
            name="每日日报更新",
            max_instances=1,  # 防止重复执行
            coalesce=True,    # 如果错过了执行时间，只执行一次
            misfire_grace_time=MISFIRE_GRACE_TIME  # 允许1小时的延迟执行
        )
    
    def _get_schedule_config(self) -> Dict[str, Any]:
        """获取调度配置"""
        return {
            'hour': config.get("schedule.hour", DEFAULT_SCHEDULE_HOUR),
            'minute': config.get("schedule.minute", DEFAULT_SCHEDULE_MINUTE),
            'timezone': config.get("schedule.timezone", DEFAULT_TIMEZONE)
        }
    
    def _setup_event_listeners(self) -> None:
        """设置事件监听器"""
        def job_listener(event):
            if event.exception:
                logger.error(f"任务执行失败: {event.exception}")
            else:
                logger.info(f"任务执行成功: {event.job_id}")
        
        self.scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    
    def _run_daily_update(self) -> None:
        """执行每日更新任务"""
        logger.info("开始执行每日日报更新任务")
        
        try:
            # 执行健康检查
            health_status = self._perform_health_check()
            
            # 如果 GitLab 连接失败，记录错误但继续执行
            if not health_status.get("gitlab_connection", False):
                logger.warning("GitLab 连接异常，可能影响日报生成质量")
            
            # 执行日报更新
            success = self._execute_daily_update()
            
            if success:
                logger.info("每日日报更新成功")
            else:
                logger.error("每日日报更新失败")
                
        except Exception as e:
            logger.error(f"执行每日更新任务时发生错误: {e}")
            raise
    
    def _perform_health_check(self) -> Dict[str, bool]:
        """执行健康检查"""
        try:
            health_status = self.updater.health_check()
            logger.info(f"健康检查结果: {health_status}")
            return health_status
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {"gitlab_connection": False, "deepseek_api_key": False, "config_loaded": False}
    
    def _execute_daily_update(self) -> bool:
        """执行日报更新"""
        try:
            today = datetime.now()
            return self.updater.update_daily_report(self.excel_path, today)
        except ReportUpdaterError as e:
            logger.error(f"日报更新失败: {e}")
            return False
        except Exception as e:
            logger.error(f"日报更新时发生未知错误: {e}")
            return False
    
    def start(self) -> None:
        """启动调度器"""
        if self.is_running:
            logger.warning("调度器已经在运行")
            return
        
        logger.info("启动日报调度器")
        
        # 启动前执行一次健康检查
        health_status = self._perform_health_check()
        logger.info(f"启动时健康检查: {health_status}")
        
        # 显示下次执行时间
        next_run = self.get_next_run_time()
        if next_run:
            logger.info(f"下次执行时间: {next_run}")
        else:
            logger.warning("未设置调度任务或调度功能已禁用")
        
        try:
            self.is_running = True
            self.scheduler.start()
        except KeyboardInterrupt:
            logger.info("收到键盘中断信号")
            self.shutdown()
        except Exception as e:
            logger.error(f"启动调度器失败: {e}")
            self.is_running = False
            raise SchedulerError(f"启动调度器失败: {e}")
    
    def shutdown(self) -> None:
        """关闭调度器"""
        if not self.is_running:
            logger.info("调度器未运行，无需关闭")
            return
        
        logger.info("正在关闭调度器...")
        
        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("调度器已关闭")
        except Exception as e:
            logger.error(f"关闭调度器时发生错误: {e}")
    
    def run_once(self, date_obj: Optional[datetime] = None) -> bool:
        """手动执行一次更新"""
        if date_obj is None:
            date_obj = datetime.now()
        
        logger.info(f"手动执行日报更新: {date_obj.strftime('%Y-%m-%d')}")
        
        try:
            return self.updater.update_daily_report(self.excel_path, date_obj)
        except ReportUpdaterError as e:
            logger.error(f"手动执行日报更新失败: {e}")
            return False
        except Exception as e:
            logger.error(f"手动执行日报更新时发生未知错误: {e}")
            return False
    
    def get_next_run_time(self) -> Optional[datetime]:
        """获取下次执行时间"""
        jobs = self.scheduler.get_jobs()
        if jobs:
            job = jobs[0]
            return getattr(job, 'next_run_time', None)
        return None
    
    def get_job_status(self) -> Dict[str, Any]:
        """获取任务状态"""
        jobs = self.scheduler.get_jobs()
        
        if not jobs:
            return {"status": "no_jobs", "message": "未设置任务"}
        
        job = jobs[0]
        next_run_time = getattr(job, 'next_run_time', None)
        
        return {
            "status": "scheduled" if self.is_running else "not_started",
            "job_id": job.id,
            "job_name": job.name,
            "next_run_time": next_run_time,
            "trigger": str(job.trigger),
            "scheduler_running": self.is_running
        }
    
    def pause_job(self) -> bool:
        """暂停任务"""
        try:
            self.scheduler.pause_job("daily_report_update")
            logger.info("任务已暂停")
            return True
        except Exception as e:
            logger.error(f"暂停任务失败: {e}")
            return False
    
    def resume_job(self) -> bool:
        """恢复任务"""
        try:
            self.scheduler.resume_job("daily_report_update")
            logger.info("任务已恢复")
            return True
        except Exception as e:
            logger.error(f"恢复任务失败: {e}")
            return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="日报调度器")
    parser.add_argument("--file", required=True, help="月报 Excel 文件路径")
    parser.add_argument("--run-once", action="store_true", help="只执行一次，不启动调度器")
    parser.add_argument("--date", help="指定日期 YYYY-MM-DD（仅在 --run-once 时有效）")
    parser.add_argument("--status", action="store_true", help="显示任务状态")
    
    args = parser.parse_args()
    
    try:
        scheduler = ReportScheduler(args.file)
        
        if args.status:
            # 显示任务状态
            status = scheduler.get_job_status()
            print("任务状态:")
            for key, value in status.items():
                print(f"  {key}: {value}")
            return
        
        if args.run_once:
            # 手动执行一次
            date_obj = datetime.strptime(args.date, "%Y-%m-%d") if args.date else None
            success = scheduler.run_once(date_obj)
            exit(0 if success else 1)
        else:
            # 启动调度器
            scheduler.start()
            
    except SchedulerError as e:
        logger.error(f"调度器错误: {e}")
        print(f"❌ 调度器错误: {e}")
        exit(1)
    except ConfigurationError as e:
        logger.error(f"配置错误: {e}")
        print(f"❌ 配置错误: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"❌ 程序执行失败: {e}")
        exit(1)

if __name__ == "__main__":
    main() 