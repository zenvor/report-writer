import json
import os
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path

# 自动加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    # 如果没有安装 python-dotenv，跳过
    pass

class ConfigurationError(Exception):
    """配置相关的异常"""
    pass

class ConfigManager:
    """配置管理器，负责加载和管理所有配置"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._validate_config()
        self._setup_logging()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if not self.config_path.exists():
                logging.warning(f"配置文件 {self.config_path} 不存在，使用默认配置")
                return self._get_default_config()
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                logging.info(f"成功加载配置文件: {self.config_path}")
                return config_data
                
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"配置文件格式错误: {e}")
        except Exception as e:
            raise ConfigurationError(f"加载配置文件失败: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "excel_columns": {
                "date": 6, 
                "content": 7, 
                "hours": 8
            },
            "retry_config": {
                "max_retries": 3,
                "backoff_factor": 2,
                "timeout": 10
            },
            "deepseek_config": {
                "model": "deepseek-chat",
                "temperature": 0.4,
                "max_tokens": 300,
                "system_prompt": "你是一名中国程序员，擅长写精炼的技术日报。请将提交信息总结为最多2句话，每句话不超过30字。"
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/report_writer.log"
            },
            "schedule": {
                "enabled": True,
                "hour": 18,
                "minute": 0,
                "timezone": "Asia/Shanghai"
            },
            "backup": {
                "enabled": True,
                "max_backups": 5
            },
            "gitlab": {
                "default_branch": "dev",
                "projects": []
            }
        }
    
    def _validate_config(self) -> None:
        """验证配置项的有效性"""
        try:
            # 验证 Excel 列配置
            excel_cols = self.config.get("excel_columns", {})
            for col_name in ["date", "content", "hours"]:
                if col_name not in excel_cols or not isinstance(excel_cols[col_name], int):
                    raise ConfigurationError(f"Excel列配置错误: {col_name} 必须是整数")
            
            # 验证重试配置
            retry_config = self.config.get("retry_config", {})
            if "max_retries" in retry_config and retry_config["max_retries"] < 0:
                raise ConfigurationError("max_retries 必须是非负整数")
            
            # 验证调度配置
            schedule = self.config.get("schedule", {})
            if "hour" in schedule and not (0 <= schedule["hour"] <= 23):
                raise ConfigurationError("调度小时必须在 0-23 范围内")
            if "minute" in schedule and not (0 <= schedule["minute"] <= 59):
                raise ConfigurationError("调度分钟必须在 0-59 范围内")
            
            # 验证备份配置
            backup = self.config.get("backup", {})
            if "max_backups" in backup and backup["max_backups"] < 1:
                raise ConfigurationError("max_backups 必须是正整数")

            # 验证多项目配置
            projects = self.config.get("gitlab.projects", [])
            if not isinstance(projects, list):
                raise ConfigurationError("gitlab.projects 必须是一个列表")
            
            for i, project in enumerate(projects):
                if not isinstance(project, dict):
                    raise ConfigurationError(f"gitlab.projects 中第 {i+1} 个元素必须是字典")
                if "id" not in project:
                    raise ConfigurationError(f"gitlab.projects 中第 {i+1} 个项目缺少 'id' 字段")

        except Exception as e:
            raise ConfigurationError(f"配置验证失败: {e}")
    
    def _setup_logging(self) -> None:
        """设置日志记录"""
        log_config = self.config.get("logging", {})
        
        # 确保日志目录存在
        log_file = log_config.get("file", "logs/report_writer.log")
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 配置日志
        log_level = log_config.get("level", "INFO")
        log_format = log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        
        # 清除现有的处理器
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 设置新的日志配置
        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format=log_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        if not key:
            return default
        
        try:
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if not isinstance(value, dict) or k not in value:
                    return default
                value = value[k]
            
            return value if value is not None else default
            
        except Exception:
            return default
    
    def get_env_or_config(self, env_key: str, config_key: Optional[str] = None, default: Any = None) -> Any:
        """优先从环境变量获取，否则从配置文件获取"""
        # 优先从环境变量获取
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value
        
        # 从配置文件获取
        if config_key:
            return self.get(config_key, default)
        
        return default
    
    def get_required_env(self, env_key: str, config_key: Optional[str] = None) -> str:
        """获取必需的环境变量，如果不存在则抛出异常"""
        value = self.get_env_or_config(env_key, config_key)
        if not value:
            raise ConfigurationError(f"必需的配置项缺失: {env_key}")
        return value
    
    def reload_config(self) -> None:
        """重新加载配置文件"""
        try:
            self.config = self._load_config()
            self._validate_config()
            logging.info("配置文件重新加载成功")
        except Exception as e:
            logging.error(f"重新加载配置文件失败: {e}")
            raise
    
    def save_config(self, config_data: Dict[str, Any]) -> None:
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
            logging.info(f"配置已保存到: {self.config_path}")
        except Exception as e:
            raise ConfigurationError(f"保存配置文件失败: {e}")

# 全局配置实例
config = ConfigManager() 