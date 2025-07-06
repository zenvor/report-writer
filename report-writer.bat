@echo off
REM ReportWriter 启动脚本 (Windows)

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 激活虚拟环境（如果存在）
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
)

REM 运行主程序
python src\report_writer.py %*

REM 如果运行失败，尝试使用python3
if %errorlevel% neq 0 (
    python3 src\report_writer.py %*
) 