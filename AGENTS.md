# Repository Guidelines

## 项目结构与模块分工
- `src/`：核心代码目录，`report_writer.py` 协调流程，`updater.py` 调用 Deepseek 生成摘要，`gitlab_client.py` 封装 GitLab API，`config_manager.py` 管理配置加载，`scheduler.py` 处理定时任务。  
- `data/` 存放日报 Excel 或文本文件，`logs/` 保存运行日志，`config.json` 为默认业务配置，`env.template` 提供环境变量模板。  
- 可执行入口为 `report-writer` 脚本（Windows 使用 `report-writer.bat`），日志示例输出写入 `report_writer.log`。

## 构建、测试与开发命令
- 创建环境：`python3 -m venv venv && source venv/bin/activate`。  
- 安装依赖：`pip install -r requirements.txt`。  
- 本地运行一次：`./report-writer --run-once -f data/日报.xlsx`。  
- 健康检查：`./report-writer --health-check`。若需调试单模块，可执行 `python -m src.report_writer --run-once`。

## 代码风格与命名规范
- Python 使用 4 空格缩进，遵循 PEP 8；中文注释说明“为什么”这样实现。  
- 遵循 camelCase 变量与函数命名，类名用 PascalCase，类内常量使用 UPPER_SNAKE_CASE。  
- 文件与目录采用 kebab-case；配置、路径、命令示例应与实际目录保持一致。  
- 提交前请确保未留下临时调试代码或未清理的日志语句。

## 测试指引
- 当前仓库未提供自动化测试，新增功能时优先编写 `tests/` 目录下的 `pytest` 测试。  
- 测试文件命名建议为 `test_模块名.py`，用例函数使用 `test_行为描述`，断言需要覆盖正常与异常路径。  
- 运行测试：`pytest -q`。若依赖外部服务，可使用 `pytest -m "not network"` 标记跳过。

## 提交与合并请求规范
- 提交信息遵循 Conventional Commits，例如 `feat(updater): 支持多项目合并摘要`。  
- 每个提交聚焦单一改动，附带必要的配置或数据文件更新。  
- 拉取请求说明需包含变更摘要、验证步骤、相关任务链接，涉及 UI 或 Excel 模板调整时请附示例截图或文件片段。  
- 合并前确认通过测试，并同步更新 `config.json` 或文档中的示例。

## 配置与安全提示
- 敏感信息仅放入 `.env`，使用 `env.template` 初始化后手动编辑。  
- `config.json` 中的项目与 Deepseek 配置需要随业务调整，修改时保持字段含义一致并记录默认值。  
- 推送前排查日志与数据目录，避免上传真实日报或包含隐私的附件。
