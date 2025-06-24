# 生产排班系统 (Production Scheduling System)

## 项目概述

这是一个生产排班系统，目的是实现自动处理和调配生产事件带来的生产计划的变化。系统以本地程序解析本地数据表来运行以实现功能。

## 主要功能

- **数据加载**：导入HSA Daily Plan原生成计划、HSA FG EOH（成品库存）、HSA Capacity（产线产能）、Learning Curve（改线后效能恢复曲线）等生产相关数据。
- **事件管理**：手动添加、删除、导入生产事件，并以列表形式展示。
- **事件处理**：根据预设的业务逻辑和算法，对生产事件进行处理，生成调整后的新生产计划和处理策略汇总。
- **结果展示与导出**：展示事件处理的详细结果和统计信息，导出为Excel文件。
- **系统设置**：配置自动加载时间、备份选项、日志级别等。
- **日志记录**：实时显示系统操作和处理日志。

## 安装与运行

### 依赖项

- Python 3.9+
- pandas
- openpyxl
- numpy
- tkinter (通常与Python一起安装)

### 安装步骤

1. 克隆或下载本仓库
2. 安装依赖项：

```bash
pip install -r requirements.txt
```

3. 运行程序：

```bash
python main.py
```

## 使用说明

1. 启动程序后，首先进入控制面板界面
2. 点击相应按钮加载各类数据：
   - 加载HSA Daily Plan
   - 加载HSA FG EOH
   - 加载HSA Capacity
   - 加载Learning Curve
3. 加载数据后，可以在"数据预览"标签页查看数据内容
4. 在"事件管理"标签页可以管理生产事件（待实现）
5. 在"结果分析"标签页可以查看处理结果（待实现）

## 项目结构

- `main.py`: 主程序入口，GUI界面实现
- `data_loader.py`: 数据加载模块
- `数据表/`: 包含所有Excel格式的数据文件
  - `daily plan.xlsx`: 每日生产计划
  - `FG EOH.xlsx`: 成品库存数据
  - `capacity .xlsx`: 产线产能数据
  - `Learning Curve.xlsx`: 改线后效能恢复曲线

## 当前版本

v1.0 - 基础功能实现：数据加载和预览 