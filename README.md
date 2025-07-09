# 日报写入器 (ReportWriter)

一个自动化的日报写入工具，能够读取 GitLab 提交信息，使用 AI 生成日报摘要，并自动写入 Excel 文件。

## ✨ 特性

- **自动化调度**：支持定时任务，每天自动生成日报
- **GitLab 集成**：自动获取指定项目的提交信息
- **AI 生成摘要**：使用 Deepseek API 生成精炼的中文日报
- **多项目支持**：可同时从多个 GitLab 项目获取提交，生成合并日报
- **Excel 操作**：自动写入月报表格的对应日期行
- **文本文件支持**：如果没有 Excel 文件，自动创建文本文件记录日报
- **错误处理**：完善的错误处理和重试机制

## 🚀 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装依赖
pip3 install -r requirements.txt
```

### 2. 配置

```bash
# 复制配置模板
cp env.template .env

# 编辑 .env 文件
# GITLAB_URL=http://your-gitlab-url
# GITLAB_PROJECT_ID=your-project-id
# GITLAB_TOKEN=your-access-token
# GITLAB_BRANCH=dev
# DEEPSEEK_API_KEY=your-api-key
```

## 📊 使用方式

```bash
./report-writer [-V] [-v[v[v]]] [-f Excel文件|文本文件] [-d YYYY-MM-DD] [-w 工时] [-C config.json] [--daemon|--run-once|--health-check|--status]
./report-writer [--gitlab-url URL] [--gitlab-token TOKEN] [--gitlab-project ID] [--gitlab-branch BRANCH] [--deepseek-key KEY]
./report-writer -V
	-V                 : 显示版本信息
	-v[v[v]]           : 日志详细程度 (v=INFO, vv=DEBUG, vvv=TRACE)
	
	-f 文件路径        : 指定Excel文件或文本文件路径
	-d YYYY-MM-DD      : 指定日期 (默认: 今天)
	-w 工时            : 指定工作小时数 (默认: 8，仅Excel模式)
	[文件路径]         : 要处理的Excel文件或文本文件路径
	
	-C config.json     : 加载配置文件 (默认: config.json)
	
	--run-once         : 执行一次更新后退出
	--daemon           : 启动守护进程模式 (定时调度，仅Excel模式)
	--health-check     : 执行健康检查
	--status           : 显示调度器状态 (仅Excel模式)

	--gitlab-url URL   : GitLab服务器地址
	--gitlab-token TOKEN : GitLab访问令牌
	--gitlab-project ID : 项目ID
	--gitlab-branch BRANCH : 分支名称 (默认: dev)

	--deepseek-key KEY : Deepseek API密钥

文件模式:
	Excel模式 (.xlsx)  : 完整功能，支持守护进程调度
	文本模式 (.txt)    : 简单日报记录，不支持守护进程
	自动模式           : 如果data目录中没有.xlsx文件，自动创建.txt文件
```

### 使用示例

```bash
# 基本用法
./report-writer                    # 自动查找Excel文件并执行一次更新
./report-writer --daemon           # 启动定时调度模式
./report-writer -f data/月报.xlsx  # 指定Excel文件
./report-writer -f data/日报.txt   # 指定文本文件
./report-writer -d 2025-01-15      # 指定日期
./report-writer --health-check     # 健康检查
./report-writer -V                 # 显示版本

# 高级用法
./report-writer -vv -d 2025-01-15 -w 6                    # 详细日志，指定日期和工时
./report-writer -C custom.json --gitlab-branch main       # 自定义配置文件和分支
./report-writer --gitlab-url http://gitlab.example.com --gitlab-project 123  # 命令行覆盖配置
```

### 实际效果

**原始提交信息：**
```
- fix(venue): 调整场地表格创建时间列宽度
- feat(order): 调整订单模块状态管理和UI展示
- refactor(match): 优化球局详情组件结构和UI
```

**生成的日报摘要：**
```
优化场地表格和订单模块状态管理。新增播放器组件并集成阿里云SDK。
```

## 📋 配置说明

项目使用两种配置文件：

### 🔐 环境变量 (`.env`)
存储敏感信息，不提交到版本控制：

```bash
# GitLab 连接信息
GITLAB_URL=http://your-gitlab-url
GITLAB_TOKEN=your-access-token

# AI 服务连接信息
DEEPSEEK_API_KEY=your-api-key

# 单项目模式（可选，如果使用多项目配置则无需填写）
# 当 config.json 中的 "projects" 列表为空时，将使用这里的配置
GITLAB_PROJECT_ID=your-project-id
GITLAB_BRANCH=dev

# 可选配置
HTTP_PROXY=http://proxy:8080
HTTPS_PROXY=https://proxy:8080
TZ=Asia/Shanghai
```

### ⚙️ 应用配置 (`config.json`)
控制应用行为，可提交到版本控制：

```json
{
  "gitlab": {
    "default_branch": "main",
    "projects": [
      { "id": "123", "branch": "dev" },
      { "id": "456" }
    ]
  },
  "excel_columns": {
    "date": 6,      // 日期列位置
    "content": 7,   // 内容列位置
    "hours": 8      // 工时列位置
  },
  "schedule": {
    "hour": 18,     // 每天执行时间
    "minute": 0,
    "timezone": "Asia/Shanghai"
  },
  "deepseek_config": {
    "temperature": 0.4,
    "max_tokens": 100,
    "system_prompt": "你是一名中国程序员，擅长写精炼的技术日报。请将提交信息总结为最多2句话，每句话不超过30字。"
  }
}
```

> 💡 **多项目配置说明**:
> - `gitlab.projects` 是一个项目列表，如果此列表不为空，程序将进入多项目模式。
> - 每个项目对象必须包含 `id`。
> - `branch` 是可选的，如果未提供，将使用顶层的 `default_branch`。
> - 如果 `projects` 列表为空，程序将回退到单项目模式，使用环境变量 `GITLAB_PROJECT_ID` 和 `GITLAB_BRANCH`。

> 💡 **配置优先级**：环境变量 > `config.json` > 默认值

## 🐛 故障排除

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| GitLab 连接失败 | 检查 `.env` 中的 `GITLAB_URL`、`GITLAB_TOKEN`、`GITLAB_PROJECT_ID` |
| AI 摘要生成失败 | 验证 `DEEPSEEK_API_KEY` 和网络连接 |
| Excel 写入失败 | 检查文件权限和 `config.json` 中的列配置 |
| 调度器未运行 | 确认 `config.json` 中的 `schedule` 配置 |

### 调试模式

```bash
# 详细日志
./report-writer -vv

# 健康检查
./report-writer --health-check

# 查看日志文件
tail -f logs/report_writer.log
```

## 🏗️ 部署

### 系统服务

```ini
# /etc/systemd/system/report-writer.service
[Unit]
Description=Report Writer Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/ReportWriter
ExecStart=/path/to/ReportWriter/venv/bin/python3 src/scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl enable report-writer
sudo systemctl start report-writer
```

## 📖 更多文档

- [详细使用指南](USAGE.md) - 完整的命令行参数说明
- [更新日志](CHANGELOG.md) - 版本更新记录