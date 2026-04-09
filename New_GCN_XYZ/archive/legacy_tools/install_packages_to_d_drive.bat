@echo off
REM 安装Python包到D盘（不使用C盘）
REM Install Python packages to D drive (avoid C drive)

echo ========================================
echo Installing Python packages to D drive
echo ========================================

REM 设置安装目录到D盘
set INSTALL_DIR=d:\1nottingham\Year4a\FYP\python_packages

REM 创建目录
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo.
echo Installing to: %INSTALL_DIR%
echo.

REM 安装必要的包到D盘
pip install --target="%INSTALL_DIR%" numpy
pip install --target="%INSTALL_DIR%" pandas
pip install --target="%INSTALL_DIR%" matplotlib
pip install --target="%INSTALL_DIR%" torch --index-url https://download.pytorch.org/whl/cpu
pip install --target="%INSTALL_DIR%" openpyxl
pip install --target="%INSTALL_DIR%" flask

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo Packages installed to: %INSTALL_DIR%
echo.
echo To use these packages, add this to your Python scripts:
echo import sys
echo sys.path.insert(0, r'd:\1nottingham\Year4a\FYP\python_packages')
echo.

pause
