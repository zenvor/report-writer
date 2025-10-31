# 日报写入器 (ReportWriter)

ReportWriter 是一个命令行工具，用于从 GitLab 获取提交信息，生成中文日报摘要，并支持写入 Excel、文本文件或直接在终端输出。

## 功能特性

- 自动按计划生成日报，可运行在守护进程模式
- 支持单项目或多项目提交记录汇总
- 集成 Deepseek，用于生成精简中文摘要（可降级为简单枚举）
- Excel 写入与备份机制，避免数据丢失
- 文本文件模式，适用于无 Excel / 无图形环境
- 区间摘要模式，可输出指定时间段的提交清单与总结
- **周报自动生成**，从月报中读取本周日报内容并填入周报表格

## 环境准备

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate      # Windows

# 安装依赖
pip3 install -r requirements.txt
```

## 配置

### 环境变量 `.env`

```bash
GITLAB_URL=http://your-gitlab-url
GITLAB_TOKEN=your-access-token
DEEPSEEK_API_KEY=your-api-key

# 单项目模式（config.json 未配置 projects 时生效）
GITLAB_PROJECT_ID=your-project-id
GITLAB_BRANCH=dev

# 可选
HTTP_PROXY=http://proxy:8080
HTTPS_PROXY=https://proxy:8080
TZ=Asia/Shanghai
```

### 应用配置 `config.json`

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
    "date": 6,
    "content": 7,
    "hours": 8
  },
  "schedule": {
    "hour": 18,
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

说明：
- `gitlab.projects` 非空时启用多项目模式；每个项目的 `branch` 可选，默认继承 `default_branch`
- `projects` 为空时退回单项目模式，使用环境变量中的项目配置
- 配置优先级：命令行参数 > 环境变量 > `config.json` > 内置默认值

## 使用

```
Usage:
  ./report-writer [OPTIONS] [文件]

常规选项:
  -h, --help                 显示帮助
  -V, --version              显示版本
  -v, --verbose              增加日志详细程度（可重复）
  -C, --config <path>        指定配置文件（默认 config.json）
  -f, --file <path>          指定 Excel 或文本文件
  -d, --date <YYYY-MM-DD>    指定日报日期（默认当天）
  -w, --hours <int>          指定工时（默认 8，仅 Excel 模式）

执行模式:
  --run-once                 执行一次写入后退出
  --daemon                   启动定时调度（仅 Excel 模式）
  --health-check             检查 GitLab、AI、配置状态
  --status                   查看调度器状态（仅 Excel 模式）

GitLab 相关:
  --gitlab-url <url>         覆盖 GitLab 服务器地址
  --gitlab-token <token>     覆盖访问令牌
  --gitlab-project <id>      覆盖默认项目 ID
  --gitlab-branch <name>     覆盖默认分支

AI 配置:
  --deepseek-key <key>       覆盖 Deepseek API 密钥

区间摘要:
  --range-summary            输出指定区间的提交摘要（终端模式）
  --start-date <YYYY-MM-DD>  区间开始日期
  --end-date <YYYY-MM-DD>    区间结束日期
  --range-project <id>       指定区间摘要使用的项目 ID
  --range-branch <name>      指定区间摘要使用的分支

周报生成:
  --generate-weekly          生成周报（从月报读取本周日报）
  --weekly-file <path>       周报文件路径（可选，默认自动查找）
  --week-start <YYYY-MM-DD>  周一日期（可选，默认本周一）

文件模式:
  Excel 模式                 自动写入月报，支持守护进程
  文本模式                   自动创建 data/日报.txt 并追加记录
  自动模式                   未检测到 Excel 时自动切换到文本模式
```

Windows 用户可在 PowerShell 或 CMD 中通过 `python report-writer ...` 执行同样的命令；若使用 Git Bash 或 WSL，也可以直接运行 `./report-writer ...`。

### 示例

```bash
# 自动查找文件并更新当日日报
./report-writer

# 指定 Excel 文件并写入 6 小时
./report-writer -f data/月报.xlsx -w 6

# 文本模式写入指定日期
./report-writer -f data/日报.txt -d 2025-01-15

# 启动守护进程
./report-writer --daemon

# 生成本周周报
./report-writer --generate-weekly

# 详细日志 + 自定义配置
./report-writer -vv -C custom.json --gitlab-branch main

# 健康检查
./report-writer --health-check
```

### 日志级别

```bash
./report-writer        # 默认仅输出结果
./report-writer -v     # INFO 级日志
./report-writer -vv    # DEBUG 级日志
./report-writer -vvv   # TRACE 级日志
```

### 配置覆盖示例

```bash
# 通过命令行覆盖 GitLab 与 AI 配置
./report-writer \
  --gitlab-url http://gitlab.example.com \
  --gitlab-token glpat-xxxxxxxx \
  --gitlab-project 173 \
  --gitlab-branch dev \
  --deepseek-key sk-xxxxxxxx

# 使用自定义配置文件并指定分支
./report-writer -C custom.json --gitlab-branch main
```

### 区间提交摘要

```bash
./report-writer --range-summary \
  --start-date 2025-01-01 \
  --end-date 2025-01-31 \
  --range-project 123
```

- `--range-project` 指定项目 ID；若配置中仅有一个项目，可省略
- `--range-branch` 覆盖区间查询的分支，例如 `--range-branch feature/api-refactor`
- 区间摘要输出包含项目、分支、日期范围、提交数量、提交列表与摘要

### 周报自动生成

```bash
# 自动查找月报和周报文件，生成本周周报
./report-writer --generate-weekly

# 指定月报和周报文件路径
./report-writer --generate-weekly \
  -f data/10月月报-范兴兴.xlsx \
  --weekly-file data/姓名-第n周周报表.xlsx

# 生成指定周的周报（指定周内任意日期）
./report-writer --generate-weekly --week-start 2025-10-27

# 详细日志模式
./report-writer --generate-weekly -vv
```

**功能说明**：
- 从月报文件中读取本周一到周五的日报内容
- 按时间顺序填入周报的"完成重点工作"表格（序号1-5对应周一-周五）
- 自动跳过节假日（某天无日报时该序号保持为空）
- 支持多种日期格式（datetime 对象和 "2025/10/31" 字符串）

**文件要求**：
- 月报文件：文件名包含"月报"的 .xlsx 文件
- 周报文件：文件名包含"周报"或"周"的 .xlsx 文件
- 周报表格结构：A列=序号，B列=事项内容，第3-7行对应周一到周五

### 输出示例

提交记录：

```
- fix(venue): 调整场地表格创建时间列宽度
- feat(order): 调整订单模块状态管理和UI展示
- refactor(match): 优化球局详情组件结构和UI
```

生成摘要：

```
优化场地表格和订单模块状态管理。新增播放器组件并集成阿里云SDK。
```

## 故障排除

| 问题 | 处理建议 |
|------|----------|
| GitLab 连接失败 | 检查 `.env` 中的 URL、令牌、项目 ID，确认网络可达 |
| AI 摘要失败 | 确认 `DEEPSEEK_API_KEY` 是否有效，必要时允许回退到简单摘要 |
| Excel 写入失败 | 确认文件未被占用，并检查 `excel_columns` 配置 |
| 定时任务未执行 | 检查 `schedule` 配置、系统时间以及系统日志 |

调试命令：

```bash
./report-writer -vv             # 输出调试日志
./report-writer --health-check  # 检查外部依赖
tail -f logs/report_writer.log  # 跟踪运行日志
```

## 部署

使用 systemd 管理服务：

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

启用服务：

```bash
sudo systemctl enable report-writer
sudo systemctl start report-writer
```
