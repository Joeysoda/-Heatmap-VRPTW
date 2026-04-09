# GCN-Guided Online AGV Scheduling System

基于论文方法的完整实现：GCN热力图 + 插入启发式 + 充电约束 + 在线调度

## 📋 项目概述

本系统实现了论文《Unsupervised Learning for Multi-Vehicle VRP with Charging and Time Windows》中提出的方法，用于医院AGV（自动导引车）的智能调度。

### 核心特性

✅ **GCN热力图生成** - 使用图卷积网络学习边缘概率  
✅ **无监督学习** - 通过距离损失和熵正则化训练  
✅ **热力图引导启发式** - 两阶段插入策略（负载均衡 + 优化）  
✅ **充电约束管理** - 电池监控和充电站插入  
✅ **在线动态调度** - 实时处理动态到达的订单  
✅ **AnyLogic集成** - 文件交换接口，无需REST API  

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    AnyLogic 仿真                         │
│  - 医院地图可视化                                         │
│  - AGV运动学仿真                                          │
│  - 隐式时间窗约束                                         │
└────────────────┬────────────────────────────────────────┘
                 │ 文件交换 (JSON)
┌────────────────▼────────────────────────────────────────┐
│         anylogic_file_bridge.py (主入口)                 │
│  - 监控 input/ 目录                                       │
│  - 调用 OnlineScheduler                                   │
│  - 输出 routes.json                                       │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│         core/online_scheduler.py (在线调度器)             │
│  - 动态订单管理                                           │
│  - AGV状态跟踪                                            │
│  - 调用 solver.py                                         │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│         core/solver.py (核心求解器)                       │
│  - GCN热力图引导的插入启发式                               │
│  - 充电约束检查                                           │
│  - 时间窗可行性检查                                        │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│         core/gnn_model.py (GCN模型)                      │
│  - 图神经网络                                             │
│  - 热力图生成                                             │
│  - 无监督训练                                             │
└─────────────────────────────────────────────────────────┘
```

## 📁 目录结构

```
New_GCN_XYZ/
├── core/                          # 核心算法模块
│   ├── __init__.py                # 模块初始化
│   ├── config.py                  # 配置文件
│   ├── data_loader.py             # 数据加载器（robot_data）
│   ├── gnn_model.py               # GCN热力图模型
│   ├── solver.py                  # 求解器（热力图引导启发式）
│   └── online_scheduler.py        # 在线调度器
│
├── anylogic_bridge/               # AnyLogic集成
│   ├── input/                     # AnyLogic输入订单
│   ├── output/                    # Python输出路由
│   └── status/                    # 状态文件
│
├── utils/                         # 工具脚本
│   ├── verify_paths.py            # 路径验证
│   ├── visualize_heatmap.py       # 热力图可视化
│   └── compare_methods.py         # 算法对比
│
├── models/                        # 训练好的模型
│   └── gcn_model.pth              # GCN模型权重
│
├── docs/                          # 文档
│   ├── ARCHITECTURE.md            # 架构说明
│   └── archived/                  # 归档的旧文档
│
├── anylogic_file_bridge.py        # 主入口
├── start_python_bridge.bat        # 启动脚本
└── README.md                      # 本文件
```

## 🚀 快速开始

### 1. 启动Python调度系统

```bash
# 方法1：使用批处理脚本
start_python_bridge.bat

# 方法2：直接运行Python
python anylogic_file_bridge.py
```

### 2. 系统初始化

系统启动时会自动：
1. 加载 `robot_data/*.xlsx` 数据
2. 训练GCN模型（如果不存在）
3. 生成热力图
4. 初始化在线调度器

### 3. 与AnyLogic集成

在AnyLogic中：
1. 配置文件路径指向 `anylogic_bridge/`
2. 订单写入 `input/` 目录（JSON格式）
3. 读取 `output/routes.json` 获取路由

## 📊 算法说明

### GCN热力图生成

```python
# 节点特征：(x, y, z) 坐标
# 输出：边缘概率矩阵 H[u,v]
heatmap = generate_heatmap(unique_nodes, train=True)
```

### 插入启发式评分函数

```
Score = λ_dist · Δdist + λ_load · Load_new - γ · Δheat

其中：
- Δdist: 距离增量
- Load_new: AGV新的总时间
- Δheat: 热力图增益
```

### 两阶段分配策略

**Stage 1**: 优先分配给空车（负载均衡）  
**Stage 2**: 优化插入位置（最小化评分）

## ⚙️ 配置参数

编辑 `core/config.py` 修改参数：

```python
# AGV数量
AGV_NUM = 9

# 电池参数
BATTERY_CAPACITY = 10000.0
BATTERY_LOW_THRESHOLD = 2000.0
CHARGING_TIME = 300.0

# 约束开关
ENABLE_CHARGING = True
ENABLE_TIME_WINDOWS = True

# 启发式权重
LAMBDA_DIST = 0.5
LAMBDA_LOAD = 0.1
GAMMA_HEAT = 200.0
```

## 📈 性能对比

与基线算法对比（论文结果）：

| 算法 | Makespan | Total Cost | 改进率 |
|------|----------|------------|--------|
| GCN-Guided | **20095** | **173450** | - |
| Best Fit | 63920 | 168575 | +32.8% |
| First Fit | 29920 | 212850 | -18.4% |
| Nearest Neighbor | 44310 | 194220 | -10.7% |

## 🔧 故障排除

### 问题1：模块导入错误

```bash
# 确保Python包路径正确
sys.path.insert(0, r'd:\1nottingham\Year4a\FYP\python_packages')
```

### 问题2：数据加载失败

```bash
# 检查robot_data路径
ROBOT_DATA_DIR = r"d:\1nottingham\Year4a\FYP\hospital-main\robot_data"
```

### 问题3：GCN训练慢

```python
# 减少训练轮数
generate_heatmap(nodes, train=True)  # 默认500轮
```

## 📚 相关文档

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - 详细架构说明
- [论文PDF](../../../314002_Jie_ZHANG_Interim_Report.pdf) - 理论基础
- [DATA_DICTIONARY.md](../../../hospital-main/robot_data/DATA_DICTIONARY.md) - 数据字典

## 🎯 下一步工作

- [ ] 完善时间窗约束（当前依赖AnyLogic隐式约束）
- [ ] 优化GCN训练速度
- [ ] 添加更多基线算法对比
- [ ] 实现在线学习（动态更新热力图）

## 📝 引用

如果使用本系统，请引用：

```
Zhang, J. (2024). Unsupervised Learning for Multi-Vehicle VRP 
with Charging and Time Windows. University of Nottingham Ningbo China.
```

## 📧 联系方式

- 作者：Jie ZHANG
- 学号：20514564
- 导师：Ning XUE
- 学校：University of Nottingham Ningbo China

---

**最后更新**: 2026-03-08  
**版本**: 2.0 - 完整实现版本
