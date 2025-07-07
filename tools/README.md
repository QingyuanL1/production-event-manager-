# 工具脚本目录

本目录包含用于数据分析和系统开发的工具脚本。

## 文件说明

### fg_eoh_analysis.py
FG EOH（成品库存）数据分析工具

**功能：**
- 分析 FG EOH.xlsx 文件结构
- 计算G值（上一个班的合计EOH库存）
- 演示Head_Qty分组逻辑
- 提供DOS计算中G值计算的参考实现

**使用方法：**
```bash
cd tools
python fg_eoh_analysis.py
```

**主要函数：**
- `load_fg_eoh_data(file_path)` - 加载FG EOH数据
- `get_g_value_for_pn(df, part_number)` - 获取指定PN的G值
- `analyze_head_qty_groups(df)` - 分析所有Head_Qty组

**注意：**
此工具脚本的核心逻辑已集成到主系统的 `src/core/lca_capacity_loss.py` 中。
本脚本主要用于独立分析和调试FG EOH数据。