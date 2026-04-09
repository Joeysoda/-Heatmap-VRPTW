@echo off
REM ============================================================
REM 启动Python文件桥接脚本
REM 这个脚本会自动启动anylogic_file_bridge.py
REM ============================================================

echo.
echo ============================================================
echo 启动 AnyLogic File Bridge
echo ============================================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

echo 当前目录: %CD%
echo.

REM 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 找不到Python！
    echo 请确保Python已安装并添加到PATH环境变量中。
    echo.
    pause
    exit /b 1
)

echo Python版本:
python --version
echo.

REM 检查脚本文件是否存在
if not exist "anylogic_file_bridge.py" (
    echo [错误] 找不到 anylogic_file_bridge.py 文件！
    echo 请确保此批处理文件与Python脚本在同一目录。
    echo.
    pause
    exit /b 1
)

echo [✓] 找到 anylogic_file_bridge.py
echo.

REM 检查并创建必要的目录
if not exist "anylogic_bridge" mkdir anylogic_bridge
if not exist "anylogic_bridge\input" mkdir anylogic_bridge\input
if not exist "anylogic_bridge\output" mkdir anylogic_bridge\output
if not exist "anylogic_bridge\status" mkdir anylogic_bridge\status

echo [✓] 目录结构已准备就绪
echo.

echo ============================================================
echo 正在启动Python桥接服务...
echo 按 Ctrl+C 可以停止服务
echo ============================================================
echo.

REM 启动Python脚本
python anylogic_file_bridge.py

REM 如果脚本意外退出
echo.
echo ============================================================
echo Python桥接服务已停止
echo ============================================================
echo.
pause
