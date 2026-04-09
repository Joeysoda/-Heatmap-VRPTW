@echo off
REM AnyLogic集成模式 - 与AnyLogic文件交换
REM 系统等待AnyLogic发送订单，处理后返回路由结果

echo ======================================================================
echo   AnyLogic集成模式 - 文件交换接口
echo   等待AnyLogic发送订单到 anylogic_bridge/input/
echo   处理后输出路由到 anylogic_bridge/output/routes.json
echo ======================================================================
echo.
echo 按 Ctrl+C 停止系统
echo.

D:\Python311\python.exe "%~dp0anylogic_file_bridge.py"

pause
