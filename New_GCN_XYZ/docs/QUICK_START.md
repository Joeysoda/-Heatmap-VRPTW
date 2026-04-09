# ⚡ 快速启动指南 - 3分钟让系统运行起来

## 🎯 超快速启动（3步）

### 步骤1：启动Python服务（30秒）
```
双击 start_python_bridge.bat
```
✅ 看到 "Waiting for orders..." 就成功了！

### 步骤2：配置AnyLogic路径（1分钟）
在AnyLogic的Main agent中设置：

**inputDir:**
```java
"d:/1nottingham/Year4a/FYP/hospital_main_copy/-Heatmap-VRPTW/New_GCN_XYZ/anylogic_bridge/input/"
```

**outputDir:**
```java
"d:/1nottingham/Year4a/FYP/hospital_main_copy/-Heatmap-VRPTW/New_GCN_XYZ/anylogic_bridge/output/"
```

### 步骤3：运行模拟（30秒）
1. 在AnyLogic中按 **F7** (Build)
2. 右键 "Simulation" → **Run**
3. 观察两个窗口的输出

---

## 📋 完整路径配置（复制粘贴）

### AnyLogic Main agent 变量配置

```java
// 1. inputDir 变量
String inputDir = "d:/1nottingham/Year4a/FYP/hospital_main_copy/-Heatmap-VRPTW/New_GCN_XYZ/anylogic_bridge/input/";

// 2. outputDir 变量
String outputDir = "d:/1nottingham/Year4a/FYP/hospital_main_copy/-Heatmap-VRPTW/New_GCN_XYZ/anylogic_bridge/output/";

// 3. pythonBridgePath 变量（如果需要）
String pythonBridgePath = "d:/1nottingham/Year4a/FYP/hospital_main_copy/-Heatmap-VRPTW/New_GCN_XYZ/anylogic_bridge";

// 4. lastRouteCheckTime 变量（新增）
long lastRouteCheckTime = 0;
```

---

## 🔧 添加路线检查事件（必须！）

### 在Main agent中添加Cyclic Event

**名称:** `checkForRoutes`  
**首次触发:** `5` 秒  
**重复间隔:** `2` 秒

**代码:**
```java
try {
    String routesFile = outputDir + "routes.json";
    java.io.File file = new java.io.File(routesFile);
    
    if (file.exists()) {
        long lastModified = file.lastModified();
        
        if (lastModified > lastRouteCheckTime) {
            traceln("========================================");
            traceln("发现新的路线文件！");
            traceln("========================================");
            
            readRoutesFromPython();
            lastRouteCheckTime = lastModified;
            
            traceln("路线读取完成");
        }
    }
} catch (Exception e) {
    traceln("检查路线文件时出错: " + e.getMessage());
}
```

---

## ✅ 成功标志

### Python窗口应该显示：
```
Found 164 order file(s)
Solving with 164 orders...
  AGV-0: 19 tasks, 114830.0s
  AGV-1: 19 tasks, 114830.0s
  ...
Results written to: .../routes.json
```

### AnyLogic控制台应该显示：
```
✓ Order sent to Python: ORDER_0001
========================================
发现新的路线文件！
========================================
✓ 成功读取路线文件
路线读取完成
```

---

## 🛠️ 常用工具

### 验证路径配置
```bash
python verify_paths.py
```

### 手动启动Python服务
```bash
cd d:\1nottingham\Year4a\FYP\hospital_main_copy\-Heatmap-VRPTW\New_GCN_XYZ
python anylogic_file_bridge.py
```

### 清理AnyLogic
```
Model → Clean
Model → Build (F7)
```

---

## ⚠️ 常见问题快速修复

### 问题：Python没有收到订单
**检查：** AnyLogic的 `inputDir` 路径是否正确  
**修复：** 确保路径末尾有 `/` 且使用正斜杠

### 问题：AnyLogic没有读取路线
**检查：** 是否添加了 `checkForRoutes` 事件  
**修复：** 按照上面的代码添加事件

### 问题：ClassNotFoundException
**修复：** 
1. 保存模型 (Ctrl+S)
2. 关闭AnyLogic
3. 重新打开
4. Build (F7)

### 问题：this.solution is null
**修复：** 在AGV的On startup中添加：
```java
if (solution == null) solution = new int[0];
```

---

## 📚 详细文档

- **完整设置指南:** `COMPLETE_SETUP_GUIDE.md`
- **错误修复:** `FIX_NULL_SOLUTION_ERROR.md`
- **实验界面创建:** `CREATE_GCN_EXPERIMENT_GUIDE.md`

---

## 🚀 启动顺序（重要！）

```
1. 双击 start_python_bridge.bat
   ↓
2. 等待看到 "Waiting for orders..."
   ↓
3. 打开AnyLogic
   ↓
4. 按 F7 (Build)
   ↓
5. 右键 Simulation → Run
   ↓
6. 观察两个窗口
```

---

## 💡 提示

- ✅ **保持Python窗口运行** - 不要关闭！
- ✅ **先启动Python** - 再运行AnyLogic
- ✅ **使用正斜杠** - 在路径中用 `/` 不是 `\`
- ✅ **路径末尾加斜杠** - `input/` 不是 `input`

---

## 🎉 就这么简单！

按照上面的步骤，您的GCN算法应该就能运行了！

如果遇到问题，查看 `COMPLETE_SETUP_GUIDE.md` 获取详细说明。

**祝您成功！** 🚀
