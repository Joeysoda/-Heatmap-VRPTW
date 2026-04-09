# 🚀 完整运行指南 / Complete Running Guide

## 📋 从零开始运行整个项目

---

## 第一部分：启动Python Bridge

### 步骤1：打开PowerShell或CMD

**按 Win+R，输入：**
```
powershell
```

### 步骤2：切换到项目目录

```powershell
cd D:\1nottingham\Year4a\FYP\hospital_main_copy\-Heatmap-VRPTW\New_GCN_XYZ
```

### 步骤3：运行Python Bridge

```powershell
python anylogic_file_bridge.py
```

### 步骤4：确认Python Bridge正在运行

**你应该看到：**
```
============================================================
AnyLogic File Bridge - Started
============================================================
Input directory:  D:\1nottingham\Year4a\FYP\hospital_main_copy\-Heatmap-VRPTW\New_GCN_XYZ\anylogic_bridge\input
Output directory: D:\1nottingham\Year4a\FYP\hospital_main_copy\-Heatmap-VRPTW\New_GCN_XYZ\anylogic_bridge\output
Status directory: D:\1nottingham\Year4a\FYP\hospital_main_copy\-Heatmap-VRPTW\New_GCN_XYZ\anylogic_bridge\status
============================================================

Waiting for orders from AnyLogic...
(Press Ctrl+C to stop)

[时间] Checking for new orders...
```

**✅ 保持这个窗口运行！不要关闭！**

---

## 第二部分：运行AnyLogic模型

### 步骤1：确认模型已打开

从你的截图看，Hospital模型已经打开了。如果没有打开：

1. 打开AnyLogic
2. File → Open
3. 选择：`D:\1nottingham\Year4a\FYP\hospital-main\Hospital_Simulator\Hospital.alp`

### 步骤2：找到Run按钮

**在AnyLogic工具栏中找到绿色的运行按钮 ▶️**

或者：
- 按键盘上的 **F5**
- 或者 Model → Run

### 步骤3：选择运行配置

**在左侧项目树中，你应该看到：**
- 📊 Simulation: Main
- ⚙️ Run Configuration: Main

**右键点击 "Simulation: Main"** 或 **"Run Configuration: Main"**，选择 **Run**

### 步骤4：等待模型编译

- 第一次运行可能需要几秒到几分钟
- 看左下角状态栏显示编译进度
- 等待编译完成

### 步骤5：观察运行

**模拟开始后，你应该看到：**

1. **AnyLogic控制台输出：**
   ```
   ========================================
   DEBUG: Checking node names from Excel
   ========================================
     ✓ FOUND: N0401S00230
     ✓ FOUND: N074S01111
     ...
   ========================================
   
   ----------------------------------------
   Processing order #1
     Start node: 'N0401S00230'
     End node: 'N021S00430'
     Start: (1305.0, 1200.0, 0)
     End: (1100.0, 1600.0, 40)
     ✓ Delivery point set: N021S00430
     ✓ Order sent to Python: ORDER_0001
   ----------------------------------------
   ```

2. **Python窗口输出：**
   ```
   [时间] Checking for new orders...
   Found 1 order file(s)
     Loaded order: ORDER_0001
     
   Solving with 1 orders...
     AGV-0: 1 tasks, 5570.0s
     
   Results written to: routes.json
   ```

3. **3D视图中：**
   - 切换到3D视图或Presentation视图
   - 你应该能看到AGV在移动
   - 订单在被处理

---

## 第三部分：查看运行结果

### 在AnyLogic中

1. **切换到3D视图**
   - 点击工具栏的3D按钮
   - 或者切换到Presentation视图

2. **观察AGV运行**
   - 使用鼠标滚轮缩放
   - 右键拖动旋转视角
   - 观察AGV移动

3. **查看控制台**
   - 查看订单处理信息
   - 确认没有错误

### 在Python窗口

1. **查看订单接收**
   - 确认显示 "Loaded order: ORDER_XXXX"
   - 不是 "UNKNOWN"

2. **查看求解结果**
   - 确认显示 "Solving with X orders..."
   - 显示AGV分配信息

3. **确认结果写入**
   - 确认显示 "Results written to: routes.json"

---

## 🎯 完整的运行流程图

```
1. 打开PowerShell
   ↓
2. cd 到项目目录
   ↓
3. 运行 python anylogic_file_bridge.py
   ↓
4. 看到 "Waiting for orders..." ✓
   ↓
5. 打开AnyLogic（保持Python窗口运行）
   ↓
6. 打开 Hospital.alp
   ↓
7. 点击 Run 按钮（或按F5）
   ↓
8. 等待编译完成
   ↓
9. 观察模拟运行
   ↓
10. 查看3D视图中的AGV
```

---

## ⚠️ 常见问题 / Common Issues

### 问题1：点击Run后没反应

**解决：**
- 等待30秒，可能正在编译
- 查看左下角状态栏
- 如果还是没反应，重启AnyLogic

### 问题2：出现编译错误

**解决：**
- 查看控制台的错误信息
- 确认代码是否正确
- 参考 FIX_ANYLOGIC_ERROR.md

### 问题3：Python没有收到订单

**检查：**
- Python Bridge是否在运行？
- 路径配置是否正确？
- 查看 anylogic_bridge/input/ 文件夹是否有JSON文件

### 问题4：看不到AGV

**检查：**
- 是否添加了 `agent.deliveryPoint = endNode;`？
- agvFleet是否有3D模型？
- 切换到3D视图了吗？

---

## 📝 运行检查清单 / Running Checklist

**启动前：**
- [ ] Python已安装
- [ ] AnyLogic已安装
- [ ] 模型文件存在
- [ ] Excel数据文件存在

**运行步骤：**
- [ ] 打开PowerShell/CMD
- [ ] cd 到项目目录
- [ ] 运行 `python anylogic_file_bridge.py`
- [ ] 看到 "Waiting for orders..." 消息
- [ ] 打开AnyLogic
- [ ] 打开 Hospital.alp
- [ ] 点击Run按钮（或按F5）
- [ ] 等待编译完成
- [ ] 观察控制台输出
- [ ] 切换到3D视图
- [ ] 观察AGV运行

**成功标志：**
- [ ] Python显示 "Loaded order: ORDER_XXXX"
- [ ] Python显示 "Solving with X orders..."
- [ ] AnyLogic显示 "✓ Order sent to Python"
- [ ] 3D视图中能看到AGV
- [ ] 没有错误信息

---

## 🛑 停止运行 / Stop Running

### 停止AnyLogic

1. 点击 ⏹️ Stop 按钮
2. 或关闭运行窗口
3. 或按 Shift+F5

### 停止Python Bridge

1. 切换到Python窗口
2. 按 **Ctrl+C**
3. 看到 "Bridge stopped by user"

---

## 🔄 重新运行 / Re-run

**每次重新运行：**

1. ✅ 先启动Python Bridge
2. ✅ 再运行AnyLogic模型
3. ✅ 停止时先停AnyLogic，再停Python

---

## 🎉 成功运行的标志

**当你看到以下所有内容时，说明运行成功：**

1. ✅ Python窗口显示 "Loaded order: ORDER_XXXX"（不是UNKNOWN）
2. ✅ Python窗口显示 "Solving with X orders..."
3. ✅ Python窗口显示 "Results written to: routes.json"
4. ✅ AnyLogic控制台显示 "✓ Order sent to Python: ORDER_XXXX"
5. ✅ AnyLogic控制台显示 "✓ Delivery point set: XXX"
6. ✅ 3D视图中能看到AGV移动
7. ✅ 没有红色的错误信息

---

## 💡 提示 / Tips

1. **保持Python窗口可见**
   - 可以并排放置AnyLogic和Python窗口
   - 方便同时观察两边的输出

2. **使用虚拟时间模式**
   - 在AnyLogic中选择 "Virtual time"
   - 运行速度更快

3. **调整运行速度**
   - 使用AnyLogic的速度滑块
   - 可以加快或减慢模拟速度

4. **保存模型**
   - 运行前记得保存（Ctrl+S）
   - 避免意外丢失修改

---

## 📞 需要帮助？

**如果遇到问题：**

1. 查看控制台的错误信息
2. 截图错误对话框
3. 检查Python窗口的输出
4. 参考 FIX_ANYLOGIC_ERROR.md
5. 参考 TROUBLESHOOTING_GUIDE.md

**现在就开始运行吧！** 🚀
