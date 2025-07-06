# ReportWriter 变更日志

## v1.0.0 - 2025-07-06

### 🚀 重大更新：webrtc-streamer 风格的命令行界面

参考 [webrtc-streamer](https://github.com/mpromonet/webrtc-streamer) 的优雅设计，完全重构了命令行界面，提供更加简洁和强大的用户体验。

### ✨ 新特性

#### 1. 统一的程序入口点
- 新增 `src/report_writer.py` 作为主程序入口
- 创建 `report-writer` 启动脚本（Linux/macOS）
- 创建 `report-writer.bat` 启动脚本（Windows）
- 自动激活虚拟环境，无需手动管理

#### 2. 智能化的默认行为
- **自动文件发现**：自动查找 `data/` 目录下的 Excel 文件
- **智能默认值**：使用合理的默认配置
- **优雅的错误处理**：友好的错误提示和建议

#### 3. 简洁的命令行语法
```bash
# 基本使用
./report-writer                    # 自动查找Excel文件并执行一次更新
./report-writer --daemon           # 启动定时调度模式
./report-writer --health-check     # 健康检查
./report-writer -V                 # 显示版本信息
```

#### 4. 灵活的参数组合
```bash
# 指定参数
./report-writer -f data/月报.xlsx -d 2025-01-15 -w 8

# 日志详细程度
./report-writer -v                 # INFO级别
./report-writer -vv                # DEBUG级别
./report-writer -vvv               # 最详细

# 命令行配置
./report-writer --gitlab-url http://gitlab.com \
                --gitlab-token glpat-xxx \
                --deepseek-key sk-xxx
```

#### 5. 改进的用户体验
- **彩色输出**：使用 emoji 和颜色增强可读性
- **进度提示**：清晰的状态反馈
- **友好的错误信息**：具体的错误描述和解决建议

### 🎨 设计理念

1. **简洁优先**：最常用的功能使用最简单的命令
2. **智能默认**：自动查找文件，使用合理的默认值  
3. **渐进增强**：通过参数逐步增加功能复杂度
4. **一致性**：参数命名和行为保持一致
5. **可观测性**：通过日志级别控制输出详细程度

### 🔄 向后兼容

- 保留原有的 `src/updater.py` 和 `src/scheduler.py` 脚本
- 所有原有功能完全兼容
- 现有的配置文件和环境变量继续有效

### 📚 文档更新

- 更新 `README.md` 展示新的使用方式
- 新增 `USAGE.md` 提供简洁的使用指南
- 新增 `CHANGELOG.md` 记录版本变更

### 🛠️ 技术改进

- 优化了调度器状态查看功能
- 修复了 APScheduler 兼容性问题
- 改进了错误处理和日志记录
- 增强了跨平台兼容性

### 📊 使用对比

#### 旧版本
```bash
# 需要手动激活虚拟环境
source venv/bin/activate

# 需要指定完整路径和参数
python3 src/updater.py --file data/月报.xlsx --date 2025-07-04

# 启动调度器
python3 src/scheduler.py --file data/月报.xlsx

# 健康检查
python3 src/updater.py --health-check
```

#### 新版本
```bash
# 一键执行，自动处理所有细节
./report-writer -d 2025-07-04

# 启动调度器
./report-writer --daemon

# 健康检查
./report-writer --health-check
```

### 🎯 使用场景优化

1. **日常使用**：`./report-writer` 一键完成
2. **批量处理**：`./report-writer -d 2025-01-10` 快速指定日期
3. **自动化部署**：`./report-writer --daemon` 启动定时任务
4. **故障排除**：`./report-writer -vv --health-check` 详细诊断

### 🚀 未来规划

- [ ] 支持配置文件热重载
- [ ] 增加 Web 界面
- [ ] 支持多种 Excel 模板
- [ ] 集成更多 Git 服务（GitHub、Gitee 等）
- [ ] 支持更多 AI 服务提供商

---

这次更新显著提升了 ReportWriter 的易用性和专业性，让日报自动化变得更加简单和高效！ 