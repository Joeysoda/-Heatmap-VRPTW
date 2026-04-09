@echo off
chcp 65001 >nul
echo ========================================
echo   算法对比实验
echo   Algorithm Comparison Experiment
echo ========================================
echo.
echo 这将运行GCN引导算法与三个基线算法的对比实验
echo This will run comparison experiments between GCN-Guided and baseline algorithms
echo.
echo 实验规模: 50, 100, 200, 500, 1000, 2328 订单
echo Test scales: 50, 100, 200, 500, 1000, 2328 orders
echo.
pause

echo.
echo 开始运行对比实验...
echo Starting comparison experiments...
echo.

D:\Python311\python.exe run_comparison.py

echo.
echo ========================================
echo   实验完成！
echo   Experiments Complete!
echo ========================================
echo.
echo 结果已保存到 results/comparison_YYYYMMDD_HHMMSS/ 目录
echo Results saved to results/comparison_YYYYMMDD_HHMMSS/ directory
echo.
echo 包含以下文件:
echo Contains the following files:
echo   - comparison_table.csv (对比表格)
echo   - comparison_report.txt (详细报告)
echo   - chart_total_travel.png (总行驶时间图)
echo   - chart_makespan.png (Makespan图)
echo   - chart_improvement.png (改进百分比图)
echo   - chart_combined.png (组合对比图)
echo   - raw_results.json (原始数据)
echo.
pause
