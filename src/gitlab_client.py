import os
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib.parse

from config_manager import config, ConfigurationError

# 设置默认编码
import sys
if hasattr(sys, 'set_default_encoding'):
    sys.set_default_encoding('utf-8')

logger = logging.getLogger(__name__)

# 常量定义
DEFAULT_PER_PAGE = 100
MAX_PAGES = 10
DEFAULT_TIMEOUT = 10
API_VERSION = "v4"

class GitLabClientError(Exception):
    """GitLab客户端异常"""
    pass

class GitLabClient:
    """GitLab API 客户端，负责获取提交信息"""
    
    def __init__(self):
        self.base_url = self._get_base_url()
        self.project_id = self._get_project_id()
        self.token = self._get_token()
        self.default_branch = self._get_default_branch()
        
        if not all([self.base_url, self.project_id, self.token]):
            logger.warning("GitLab 配置不完整，某些功能可能无法使用")
        
        # 确保所有配置值都是字符串且去除可能的注释
        if self.project_id:
            self.project_id = str(self.project_id).split('#')[0].strip()
        if self.default_branch:
            self.default_branch = str(self.default_branch).split('#')[0].strip()
        
        logger.info(f"GitLab 客户端初始化 - 项目ID: {self.project_id}, 分支: {self.default_branch}")
        self.session = self._create_session()
    
    def _get_base_url(self) -> Optional[str]:
        """获取GitLab基础URL"""
        url = config.get_env_or_config("GITLAB_URL", "gitlab.url")
        if url and not url.endswith('/'):
            url = url.rstrip('/')
        return url
    
    def _get_project_id(self) -> Optional[str]:
        """获取项目ID"""
        return config.get_env_or_config("GITLAB_PROJECT_ID", "gitlab.project_id")
    
    def _get_token(self) -> Optional[str]:
        """获取访问令牌"""
        return config.get_env_or_config("GITLAB_TOKEN", "gitlab.token")
    
    def _get_default_branch(self) -> str:
        """获取默认分支"""
        return config.get_env_or_config("GITLAB_BRANCH", "gitlab.default_branch", "dev")
    
    def _create_session(self) -> requests.Session:
        """创建带有重试机制的会话"""
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=config.get("retry_config.max_retries", 3),
            backoff_factor=config.get("retry_config.backoff_factor", 2),
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 设置默认超时
        session.timeout = config.get("retry_config.timeout", DEFAULT_TIMEOUT)
        
        return session
    
    def fetch_commits(self, date_obj: datetime, branch: Optional[str] = None) -> List[str]:
        """获取指定日期的提交信息"""
        if not self._validate_configuration():
            logger.error("GitLab 配置不完整，无法获取提交信息")
            return []
        
        target_branch = branch or self.default_branch
        logger.info(f"正在获取 {date_obj.strftime('%Y-%m-%d')} 在分支 {target_branch} 的提交信息")
        
        try:
            commits = self._fetch_commits_with_pagination(date_obj, target_branch)
            logger.info(f"成功获取 {len(commits)} 条提交信息")
            return commits
        except Exception as e:
            logger.error(f"获取提交信息失败: {e}")
            return []
    
    def _validate_configuration(self) -> bool:
        """验证配置的完整性"""
        return all([self.base_url, self.project_id, self.token])
    
    def _fetch_commits_with_pagination(self, date_obj: datetime, branch: str) -> List[str]:
        """使用分页获取提交信息"""
        since, until = self._get_date_range(date_obj)
        
        headers = self._get_headers()
        params = self._get_base_params(since, until, branch)
        
        commits = []
        
        for page in range(1, MAX_PAGES + 1):
            params["page"] = page
            
            try:
                data = self._make_api_request(params, headers)
                if not data:
                    logger.debug(f"第 {page} 页没有更多数据")
                    break
                
                page_commits = self._extract_commit_titles(data)
                commits.extend(page_commits)
                
                logger.debug(f"第 {page} 页获取到 {len(page_commits)} 条提交")
                
                # 如果返回的数据少于每页限制，说明已经是最后一页
                if len(data) < DEFAULT_PER_PAGE:
                    break
                    
            except GitLabClientError as e:
                logger.error(f"获取第 {page} 页数据失败: {e}")
                break
        
        return commits
    
    def _get_date_range(self, date_obj: datetime) -> tuple[str, str]:
        """获取日期范围"""
        since = date_obj.strftime("%Y-%m-%dT00:00:00Z")
        until = date_obj.strftime("%Y-%m-%dT23:59:59Z")
        return since, until
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        # 确保token不包含注释或特殊字符
        clean_token = str(self.token).split('#')[0].strip()
        return {
            "PRIVATE-TOKEN": clean_token,
            "Content-Type": "application/json; charset=utf-8"
        }
    
    def _get_base_params(self, since: str, until: str, branch: str) -> Dict[str, Any]:
        """获取基础请求参数"""
        return {
            "since": since,
            "until": until,
            "per_page": DEFAULT_PER_PAGE,
            "page": 1,
            "ref_name": branch
        }
    
    def _make_api_request(self, params: Dict[str, Any], headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """发起API请求"""
        # 确保项目ID不包含注释
        clean_project_id = str(self.project_id).split('#')[0].strip()
        url = f"{self.base_url}/api/{API_VERSION}/projects/{clean_project_id}/repository/commits"
        
        # 确保所有参数都是UTF-8编码的字符串
        clean_params = {}
        for key, value in params.items():
            if isinstance(value, str):
                clean_params[key] = str(value).split('#')[0].strip()
            else:
                clean_params[key] = value
        
        try:
            response = self.session.get(url, headers=headers, params=clean_params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            self._handle_http_error(e)
        except requests.exceptions.ConnectionError:
            raise GitLabClientError("连接 GitLab 服务器失败")
        except requests.exceptions.Timeout:
            raise GitLabClientError("请求超时")
        except requests.exceptions.RequestException as e:
            raise GitLabClientError(f"请求异常: {e}")
    
    def _handle_http_error(self, error: requests.exceptions.HTTPError) -> None:
        """处理HTTP错误"""
        status_code = error.response.status_code
        
        if status_code == 401:
            raise GitLabClientError("GitLab Token 无效或已过期")
        elif status_code == 403:
            raise GitLabClientError("权限不足，无法访问项目")
        elif status_code == 404:
            raise GitLabClientError("项目不存在或无权限访问")
        elif status_code == 429:
            raise GitLabClientError("请求过于频繁，请稍后重试")
        else:
            raise GitLabClientError(f"HTTP 错误 {status_code}: {error}")
    
    def _extract_commit_titles(self, commits_data: List[Dict[str, Any]]) -> List[str]:
        """提取提交标题"""
        return [commit.get("title", "").strip() for commit in commits_data if commit.get("title")]
    
    def validate_connection(self) -> bool:
        """验证 GitLab 连接是否正常"""
        if not self._validate_configuration():
            logger.warning("GitLab 配置不完整")
            return False
        
        try:
            # 确保项目ID不包含注释
            clean_project_id = str(self.project_id).split('#')[0].strip()
            url = f"{self.base_url}/api/{API_VERSION}/projects/{clean_project_id}"
            headers = self._get_headers()
            
            response = self.session.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            
            project_info = response.json()
            project_name = project_info.get('name', 'Unknown')
            logger.info(f"GitLab 连接验证成功，项目名称: {project_name}")
            return True
            
        except Exception as e:
            logger.error(f"GitLab 连接验证失败: {e}")
            return False
    
    def get_project_info(self) -> Optional[Dict[str, Any]]:
        """获取项目信息"""
        if not self._validate_configuration():
            return None
        
        try:
            # 确保项目ID不包含注释
            clean_project_id = str(self.project_id).split('#')[0].strip()
            url = f"{self.base_url}/api/{API_VERSION}/projects/{clean_project_id}"
            headers = self._get_headers()
            
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"获取项目信息失败: {e}")
            return None
    
    def get_branches(self) -> List[str]:
        """获取项目的所有分支"""
        if not self._validate_configuration():
            return []
        
        try:
            # 确保项目ID不包含注释
            clean_project_id = str(self.project_id).split('#')[0].strip()
            url = f"{self.base_url}/api/{API_VERSION}/projects/{clean_project_id}/repository/branches"
            headers = self._get_headers()
            
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            
            branches_data = response.json()
            return [branch["name"] for branch in branches_data]
            
        except Exception as e:
            logger.error(f"获取分支列表失败: {e}")
            return []

# 便捷函数，保持向后兼容
def fetch_commits(date_obj: datetime) -> List[str]:
    """获取指定日期的提交信息（向后兼容）"""
    client = GitLabClient()
    return client.fetch_commits(date_obj) 