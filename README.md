# 日报写入器 (ReportWriter)

一个自动化的日报写入工具，能够读取 GitLab 提交信息，使用 AI 生成日报摘要，并自动写入 Excel 文件。

## ✨ 特性

- 🔄 **自动化调度**：支持定时任务，每天自动生成日报
- 📊 **GitLab 集成**：自动获取指定项目的提交信息
- 🤖 **AI 生成摘要**：使用 Deepseek API 生成精炼的中文日报
- 📋 **Excel 操作**：自动写入月报表格的对应日期行
- 🛡️ **错误处理**：完善的错误处理和重试机制
- 💾 **文件备份**：自动备份 Excel 文件，防止数据丢失
- 📈 **健康检查**：内置健康检查功能，便于监控

## 🚀 快速开始

> 💡 **新用户推荐**：查看 [简洁使用指南](USAGE.md) 了解新版本的 webrtc-streamer 风格命令行界面！

### 1. 环境准备

确保已安装：
- python3 3.8+
- Git

### 2. 创建并激活虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境 (Linux/macOS)
source venv/bin/activate

# 激活虚拟环境 (Windows)
# venv\Scripts\activate
```

### 3. 安装依赖

```bash
# 确保虚拟环境已激活
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制环境变量模板
cp env.template .env

# 编辑 .env 文件，填入正确的配置
# 建议使用 vim, nano 或其他文本编辑器
vim .env
```

环境变量说明：
```bash
# GitLab 配置
GITLAB_URL=http://xxxx         # GitLab 服务地址
GITLAB_PROJECT_ID=173                        # 项目 ID
GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx      # 访问令牌
GITLAB_BRANCH=dev                            # 目标分支（可选，默认 master）

# Deepseek API 配置
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 可选：代理设置
# HTTP_PROXY=http://proxy.example.com:8080
# HTTPS_PROXY=https://proxy.example.com:8080
```

### 5. 准备 Excel 文件

将月报 Excel 文件放在 `data/` 目录中，例如：
```
data/
├── 2025年1月月报.xlsx
└── backups/           # 自动备份目录
```

### 6. 运行程序

#### 🚀 新版本使用方式（推荐）

```bash
# 基本使用 - 自动查找Excel文件并执行一次更新
./report-writer

# 或者在Windows上
report-writer.bat

# 启动定时调度模式
./report-writer --daemon

# 指定Excel文件
./report-writer -f data/月报.xlsx

# 指定日期
./report-writer -d 2025-01-15

# 健康检查
./report-writer --health-check

# 显示版本信息
./report-writer -V

# 显示帮助信息
./report-writer -h
```

#### 📖 经典使用方式（仍然支持）

```bash
# 确保虚拟环境已激活
# 脚本会自动查找 data 目录下的 Excel 文件
python3 src/updater.py

# 或者指定文件和日期
python3 src/updater.py --file data/月报.xlsx --date 2025-07-04

# 启动定时任务
python3 src/scheduler.py --file data/月报.xlsx
```

## 📖 使用说明

### 🎯 新版本命令行工具（推荐）

新版本提供了更加简洁和强大的命令行界面，参考了 webrtc-streamer 的设计理念：

```bash
# 基本使用方式
./report-writer [-v[v]] [-f Excel文件] [-d 日期] [模式选项]

# 常用命令
./report-writer                    # 自动查找Excel文件，执行一次更新
./report-writer --daemon           # 启动定时调度模式
./report-writer --health-check     # 健康检查
./report-writer -V                 # 显示版本信息
./report-writer -h                 # 显示帮助信息

# 高级用法
./report-writer -f data/月报.xlsx -d 2025-01-15 -w 8  # 指定文件、日期和工时
./report-writer -v --daemon        # 启动调度器并显示详细日志
./report-writer --status           # 查看调度器状态
```

### 📋 完整参数说明

```
选项:
  -v[v[v]]           : 日志详细程度 (v=INFO, vv=DEBUG, vvv=TRACE)
  -V                 : 显示版本信息
  -C config.json     : 加载配置文件 (默认: config.json)
  -f Excel文件       : 指定Excel文件路径
  -d YYYY-MM-DD      : 指定日期 (默认: 今天)
  -w 工时            : 指定工作小时数 (默认: 8)
  [Excel文件路径]    : 要处理的Excel文件路径

模式:
  --run-once         : 执行一次更新后退出
  --daemon           : 启动守护进程模式 (定时调度)
  --health-check     : 执行健康检查
  --status           : 显示调度器状态

GitLab选项:
  --gitlab-url URL   : GitLab服务器地址
  --gitlab-token TOKEN : GitLab访问令牌
  --gitlab-project ID : 项目ID
  --gitlab-branch BRANCH : 分支名称 (默认: dev)

AI选项:
  --deepseek-key KEY : Deepseek API密钥
```

### 🔧 经典命令行工具（仍然支持）

激活虚拟环境后，可以直接使用 `python3` 调用 `src` 目录下的脚本。

```bash
# 激活虚拟环境
source venv/bin/activate

# 手动执行日报更新（推荐，自动查找文件）
python3 src/updater.py

# 指定文件和日期执行更新
python3 src/updater.py --file data/月报.xlsx --date 2025-07-04

# 启动调度器（推荐，自动查找文件）
python3 src/scheduler.py

# 执行健康检查
python3 src/updater.py --health-check

# 测试 GitLab 连接（通过 updater 的健康检查）
python3 src/updater.py --health-check
```

## 🛠️ 部署指南

### 系统服务部署

创建 systemd 服务文件示例：

```ini
[Unit]
Description=Report Writer Service
After=network.target

[Service]
Type=simple
User=your-user                 # 运行服务的用户
Group=your-group               # 运行服务的用户组
WorkingDirectory=/path/to/ReportWriter  # 项目根目录的绝对路径
ExecStart=/path/to/ReportWriter/venv/bin/python3 src/scheduler.py # 使用虚拟环境的Python
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 📊 监控和日志

### 日志文件

- 应用日志：`logs/report_writer.log`

### 健康检查

```bash
# 激活虚拟环境后执行
python3 src/updater.py --health-check
```

### 监控指标

- GitLab 连接状态
- API 调用成功率
- 文件写入成功率
- 调度器运行状态

## 🐛 故障排除

### 快速诊断

```bash
# 1. 检查 GitLab 连接
python3 src/updater.py --health-check

# 2. 调试提交信息获取（需要创建相应的调试脚本）
# python3 debug_commits.py

# 3. 执行单次运行查看日志
python3 src/updater.py
```

### 常见问题

1. **GitLab 连接失败**
   - 检查网络连接
   - 验证 `.env` 文件中的 GitLab URL, Token, 和 Project ID
   - 检查分支配置是否正确

2. **Excel 文件写入失败**
   - 检查文件路径和权限
   - 确认 Excel 文件格式正确
   - 验证日期格式匹配

3. **AI 摘要生成失败**
   - 检查 `.env` 文件中的 Deepseek API Key
   - 确认网络连接
   - 查看 API 调用日志

4. **调度器未运行**
   - 检查时区设置
   - 确认 `config.json` 中的调度配置正确
   - 查看调度器日志

5. **获取不到提交信息**
   - 检查目标分支是否正确
   - 确认提交时间是否在查询范围内

6. **日报内容太长**
   - 已优化为最多2句话，每句不超过30字
   - 可在 `config.json` 中调整 `max_tokens` 和 `system_prompt`

### 调试模式

```bash
# 设置调试日志级别 (Linux/macOS)
export LOG_LEVEL=DEBUG

# 设置调试日志级别 (Windows)
# set LOG_LEVEL=DEBUG

# 运行单次更新查看详细日志
python3 src/updater.py --date 2025-07-04
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。

## 📞 支持

如有问题或建议，请提交 [Issue](https://github.com/your-repo/issues)。

---

## 🎯 使用示例

### 完整使用流程

```bash
# 1. 克隆项目并进入目录
# git clone ...
# cd ReportWriter

# 2. 环境准备
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 配置环境变量
cp env.template .env
# 编辑 .env 文件，填入你的 GitLab 和 AI 配置

# 4. 准备数据文件
# 将你的月报.xlsx文件放入 data/ 目录

# 5. 测试连接
./report-writer --health-check

# 6. 手动执行一次
./report-writer

# 7. 启动定时调度
./report-writer --daemon
```

### 🎯 极简使用方式

如果你的环境已经配置好，只需要：

```bash
# 一次性更新
./report-writer

# 定时调度
./report-writer --daemon

# 健康检查
./report-writer --health-check
```

### 实际效果展示

**原始提交信息：**
```
- fix(venue): 调整场地表格创建时间列宽度
- feat(order): 调整订单模块状态管理和UI展示
- refactor(match): 优化球局详情组件结构和UI
- feat(livestream): 优化直播模块UI和数据展示
- chore(layout): 更新平台名称和logo展示
```

**生成的日报摘要：**
```
优化场地表格和订单模块状态管理。新增播放器组件并集成阿里云SDK。
```

---

**注意**：
1. 首次使用请仔细阅读配置说明，确保所有环境变量正确设置
2. 确保 GitLab 分支配置正确，默认从 `dev` 分支获取提交信息
3. 日报内容已优化为精简格式，最多2句话

## 📁 项目结构详解

### 目录结构说明

```
ReportWriter/
├── README.md              # 项目说明文档（本文件）
├── config.json            # 项目配置文件
├── requirements.txt       # python3依赖包列表
├── env.template           # 环境变量模板
├── src/                   # 源代码目录
│   ├── config_manager.py  # 配置管理模块
│   ├── gitlab_client.py   # GitLab API客户端
│   ├── updater.py         # 主更新程序
│   └── scheduler.py       # 任务调度模块
├── scripts/               # 脚本文件目录
│   └── startup/           # (此目录下的脚本已移除)
├── data/                  # 数据文件目录
│   ├── 月报.xlsx        # 示例数据文件
│   └── backups/           # 自动备份目录
├── logs/                  # 日志文件目录
└── venv/                  # python3虚拟环境目录
```

### 核心模块说明

#### 1. 配置管理 (`config_manager.py`)
- 统一管理所有配置项
- 支持环境变量和配置文件两种配置方式
- 自动设置日志记录
- 提供默认配置降级机制

#### 2. GitLab 客户端 (`gitlab_client.py`)
- 封装 GitLab API 调用逻辑
- 支持自动重试和错误处理
- 分页获取提交信息，避免数据截断
- 支持多分支切换和连接验证

#### 3. 报告更新器 (`updater.py`)
- 实现主要业务逻辑
- 自动文件备份和恢复机制
- AI 摘要生成（精简至最多2句话）
- 智能降级处理，确保服务可用性

#### 4. 任务调度器 (`scheduler.py`)
- 基于 APScheduler 的定时任务管理
- 支持健康检查和监控
- 优雅停止和异常处理
- 灵活的调度配置

### 配置文件说明

#### 环境变量配置 (`.env`)
```bash
# GitLab 配置
GITLAB_URL=http://your-gitlab-url
GITLAB_PROJECT_ID=your-project-id
GITLAB_TOKEN=your-access-token
GITLAB_BRANCH=dev

# Deepseek API 配置
DEEPSEEK_API_KEY=your-api-key

# 可选：代理设置
HTTP_PROXY=http://proxy:8080
HTTPS_PROXY=https://proxy:8080
```

#### 项目配置 (`config.json`)
```json
{
    "excel_columns": {
        "date": 6,      // 出勤日期列
        "content": 7,   // 工作内容列
        "hours": 8      // 工时列
    },
    "retry_config": {
        "max_retries": 3,
        "backoff_factor": 2,
        "timeout": 10
    },
    "deepseek_config": {
        "model": "deepseek-chat",
        "temperature": 0.4,
        "max_tokens": 100,
        "system_prompt": "你是一名中国程序员，擅长写精炼的技术日报。请将提交信息总结为最多2句话，每句话不超过30字。"
    },
    "schedule": {
        "enabled": true,
        "hour": 18,
        "minute": 0,
        "timezone": "Asia/Shanghai"
    },
    "backup": {
        "enabled": true,
        "max_backups": 5
    }
}
```

### 开发和维护建议

1. **代码组织**
   - 所有源代码放在 `src/` 目录
   - 数据文件放在 `data/` 目录

2. **日志管理**
   - 应用日志自动生成到 `logs/` 目录
   - 定期清理旧日志文件
   - 使用不同日志级别进行调试

3. **配置管理**
   - 敏感信息使用环境变量
   - 业务配置使用配置文件
   - 更新依赖时记得更新 `requirements.txt`

4. **备份策略**
   - Excel 文件自动备份到 `data/backups/`
   - 保留最近 5 个备份文件
   - 重要操作前手动备份

---

*最后更新时间：2025年7月* 