# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

ReportWriter 是一个自动化日报生成工具，从 GitLab 获取提交记录，通过 Deepseek API 生成中文日报摘要，支持写入 Excel 月报、文本文件或终端输出。

## 核心架构

### 模块职责划分
- `report_writer.py`: 主入口和命令行接口，负责参数解析和流程协调
- `updater.py`: 核心业务逻辑，处理提交获取、AI 摘要生成、Excel/文本写入
- `gitlab_client.py`: GitLab API 客户端封装，负责提交记录获取
- `config_manager.py`: 配置管理，统一处理环境变量、config.json 和默认值
- `scheduler.py`: 定时任务调度器，支持守护进程模式

### 配置优先级
命令行参数 > 环境变量 (.env) > config.json > 内置默认值

### 多项目模式
- 当 `config.json` 中 `gitlab.projects` 数组非空时，启用多项目模式
- 多项目模式下会为每个项目创建独立的 `GitLabClient` 实例
- 提交记录会合并后统一生成摘要
- 单项目模式下直接使用环境变量中的 `GITLAB_PROJECT_ID` 和 `GITLAB_BRANCH`

### AI 摘要降级策略
- 优先使用 Deepseek API 生成智能摘要
- 如果 API 失败或未配置，自动降级为简单列举提交信息
- 摘要生成由 `updater.py` 中的 `_generate_summary_with_ai()` 和 `_generate_simple_summary()` 处理

## 开发命令

### 环境初始化
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

### 常用开发命令
```bash
# 执行单次日报写入（自动查找 Excel/文本文件）
./report-writer --run-once

# 指定文件和工时
./report-writer --run-once -f data/月报.xlsx -w 6

# 详细调试日志
./report-writer --run-once -vv

# 健康检查（验证 GitLab、AI、配置状态）
./report-writer --health-check

# 启动守护进程（定时任务模式）
./report-writer --daemon

# 区间摘要（输出指定日期范围的提交汇总）
./report-writer --range-summary --start-date 2025-01-01 --end-date 2025-01-31

# 直接运行 Python 模块（调试用）
python -m src.report_writer --run-once
```

### 日志级别
- 默认: 仅输出关键结果
- `-v`: INFO 级别
- `-vv`: DEBUG 级别
- `-vvv`: TRACE 级别

## 文件模式说明

### Excel 模式
- 自动查找 `data/` 目录下的 `.xlsx` 文件（优先匹配包含"月报"的文件）
- 写入位置由 `config.json` 中的 `excel_columns` 配置决定（日期列、内容列、工时列）
- 支持自动备份（最多保留 5 个备份文件）
- 起始行为第 3 行（常量 `EXCEL_START_ROW`）

### 文本模式
- 如果未找到 Excel 文件，自动创建 `data/日报.txt`
- 以追加模式写入，格式为：`日期 - 摘要内容`
- 不支持守护进程模式

## 配置要点

### 必需的环境变量 (.env)
```bash
GITLAB_URL=http://your-gitlab-url
GITLAB_TOKEN=your-access-token
DEEPSEEK_API_KEY=your-api-key  # 可选，未配置时使用简单摘要

# 单项目模式（config.json 中 projects 为空时）
GITLAB_PROJECT_ID=your-project-id
GITLAB_BRANCH=dev
```

### config.json 关键配置
- `gitlab.projects`: 多项目配置数组，每项包含 `id` 和可选的 `branch`
- `excel_columns`: Excel 列位置映射（date, content, hours）
- `schedule`: 定时任务配置（hour, minute, timezone）
- `deepseek_config`: AI 模型参数（temperature, max_tokens, system_prompt）

## 错误处理与重试

### GitLab API 重试机制
- 配置位于 `retry_config`：max_retries=3, backoff_factor=2
- 自动重试状态码：429, 500, 502, 503, 504
- 使用 `requests.Session` 和 `urllib3.Retry` 实现

### 备份与恢复
- Excel 写入前自动创建带时间戳的备份文件
- 备份文件命名格式：`原文件名_backup_YYYYMMDD_HHMMSS.xlsx`
- 最多保留 5 个备份（由 `backup.max_backups` 配置）

## 代码规范补充

### 异常层次结构
- `ConfigurationError`: 配置相关异常
- `GitLabClientError`: GitLab API 异常
- `ReportUpdaterError`: 报告更新异常（包含 ExcelOperationError、AIServiceError、BackupError 子类）
- `SchedulerError`: 调度器异常

### 关键常量
- `DEFAULT_WORK_HOURS = 8`: 默认工时
- `MAX_COMMIT_DISPLAY = 10`: 摘要中最多显示的提交数
- `DEFAULT_PER_PAGE = 100`: GitLab API 分页大小
- `DEEPSEEK_BASE_URL = "https://api.deepseek.com"`

## 注意事项

### 安全性
- 绝不将 `.env` 文件提交到版本控制
- `data/` 目录中的真实日报文件应被 `.gitignore` 排除
- 提交前检查日志文件，避免泄露敏感信息

### Excel 操作注意
- 使用 `openpyxl` 库，确保文件未被其他程序占用
- 写入前验证文件存在性和可写性
- 行号从 1 开始（Excel 规范），列号也从 1 开始

### 区间摘要模式特性
- 通过 `--range-summary` 启用
- 必需参数：`--start-date` 和 `--end-date`
- 输出格式包含：项目信息、分支、日期范围、提交总数、详细提交列表、AI 总结
- 仅支持终端输出，不写入文件
