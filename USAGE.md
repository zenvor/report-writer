# ReportWriter 使用指南

## 使用格式

```bash
./report-writer [-f Excel文件] [-d YYYY-MM-DD] [-w 工时] [-v[v[v]]] [--daemon|--run-once|--health-check|--status]
./report-writer [-C config.json] [--gitlab-url URL] [--gitlab-token TOKEN] [--gitlab-project ID] [--gitlab-branch BRANCH] [--deepseek-key KEY]
./report-writer -V
```

### 参数说明

```
-v[v[v]]           : 日志详细程度 (v=INFO, vv=DEBUG, vvv=TRACE)
-V                 : 显示版本信息
-C config.json     : 加载配置文件 (默认: config.json)
-f Excel文件       : 指定Excel文件路径
-d YYYY-MM-DD      : 指定日期 (默认: 今天)
-w 工时            : 指定工作小时数 (默认: 8)

模式选项:
--run-once         : 执行一次更新后退出 (默认模式)
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

### 使用示例

```bash
./report-writer                                    # 自动查找Excel文件并执行一次更新
./report-writer --daemon                           # 启动定时调度模式
./report-writer -f data/月报.xlsx                  # 指定Excel文件
./report-writer -d 2025-01-15                      # 指定日期
./report-writer -v --health-check                  # 详细日志模式下的健康检查
./report-writer -V                                 # 显示版本信息
```

## 🚀 快速开始

ReportWriter 现在提供了更加简洁和强大的命令行界面，参考了 webrtc-streamer 的设计理念。

### 基本使用

```bash
# 执行一次日报更新（自动查找Excel文件）
./report-writer

# 启动定时调度模式
./report-writer --daemon

# 健康检查
./report-writer --health-check

# 显示版本信息
./report-writer -V

# 显示帮助信息
./report-writer -h
```

### 指定参数

```bash
# 指定Excel文件
./report-writer -f data/月报.xlsx

# 指定日期
./report-writer -d 2025-01-15

# 指定工作小时数
./report-writer -w 8

# 组合使用
./report-writer -f data/月报.xlsx -d 2025-01-15 -w 8
```

### 日志详细程度

```bash
# 默认模式（只显示结果）
./report-writer

# 显示基本信息
./report-writer -v

# 显示详细调试信息
./report-writer -vv

# 显示所有跟踪信息
./report-writer -vvv
```

### 守护进程模式

```bash
# 启动定时调度
./report-writer --daemon

# 启动调度并显示详细日志
./report-writer -v --daemon

# 查看调度器状态
./report-writer --status
```

### 命令行配置

你可以通过命令行直接设置GitLab和AI配置，无需修改环境变量文件：

```bash
# 设置GitLab配置
./report-writer --gitlab-url http://your-gitlab.com \
                --gitlab-token glpat-xxxxxxxxxxxx \
                --gitlab-project 173 \
                --gitlab-branch dev

# 设置AI配置
./report-writer --deepseek-key sk-xxxxxxxxxxxxxxxx

# 组合使用
./report-writer --gitlab-url http://your-gitlab.com \
                --gitlab-token glpat-xxxxxxxxxxxx \
                --gitlab-project 173 \
                --deepseek-key sk-xxxxxxxxxxxxxxxx \
                --daemon
```

## 🎯 使用场景

### 1. 日常使用

```bash
# 每天下班前更新当天日报
./report-writer
```

### 2. 补充历史日报

```bash
# 补充指定日期的日报
./report-writer -d 2025-01-10
./report-writer -d 2025-01-11
./report-writer -d 2025-01-12
```

### 3. 自动化部署

```bash
# 启动定时调度（每天18:00自动执行）
./report-writer --daemon
```

### 4. 故障排除

```bash
# 检查系统状态
./report-writer --health-check

# 查看详细日志
./report-writer -vv -d 2025-01-15

# 查看调度器状态
./report-writer --status
```

## 🔧 Windows 用户

Windows 用户可以使用批处理文件：

```cmd
REM 基本使用
report-writer.bat

REM 启动定时调度
report-writer.bat --daemon

REM 健康检查
report-writer.bat --health-check
```

## 📊 输出示例

### 成功执行

```bash
$ ./report-writer -d 2025-07-04
📁 自动找到Excel文件: data/月报.xlsx
✅ 日报更新成功: 2025-07-04
```

### 详细日志

```bash
$ ./report-writer -v -d 2025-07-04
📁 自动找到Excel文件: data/月报.xlsx
INFO: 执行一次更新: data/月报.xlsx, 日期: 2025-07-04, 工时: 8
INFO: GitLab 客户端初始化 - 项目ID: 173, 分支: dev
INFO: 开始更新日报: data/月报.xlsx, 日期: 2025-07-04
INFO: 创建备份文件: data/backups/月报_20250706_102915.xlsx
INFO: 正在获取 2025-07-04 在分支 dev 的提交信息
INFO: 成功获取 10 条提交信息
INFO: 调用 Deepseek API 生成摘要
INFO: Deepseek API 调用成功
INFO: 找到日期行: 第 6 行
INFO: 成功写入日期 2025/7/4 的日报
✅ 日报更新成功: 2025-07-04
```

### 健康检查

```bash
$ ./report-writer --health-check
🔍 健康检查结果:
  GitLab连接: ✅
  Deepseek API: ✅
  配置加载: ✅
✅ 所有检查项目正常
```

### 调度器状态

```bash
$ ./report-writer --status
📁 自动找到Excel文件: data/月报.xlsx
📊 调度器状态:
  status: not_started
  job_id: daily_report_update
  job_name: 每日日报更新
  next_run_time: None
  trigger: cron[hour='18', minute='0']
  scheduler_running: False
```

## 🎨 设计理念

参考 webrtc-streamer 的设计，ReportWriter 遵循以下原则：

1. **简洁优先**：最常用的功能使用最简单的命令
2. **智能默认**：自动查找文件，使用合理的默认值
3. **渐进增强**：通过参数逐步增加功能复杂度
4. **一致性**：参数命名和行为保持一致
5. **可观测性**：通过日志级别控制输出详细程度

## 🔗 相关文档

- [完整 README](README.md) - 详细的安装和配置指南
- [配置文件说明](config.json) - 配置选项详解
- [环境变量模板](env.template) - 环境变量设置示例 