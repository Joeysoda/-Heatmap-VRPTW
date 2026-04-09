@echo off
chcp 65001 >nul
echo ========================================
echo   生成对比图表
echo   Generate Comparison Charts
echo ========================================
echo.
echo 从已有的实验结果生成图表...
echo.

D:\Python311\python.exe generate_charts.py

echo.
pause
