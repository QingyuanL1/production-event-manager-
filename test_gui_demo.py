#!/usr/bin/env python3
"""
GUI演示和测试脚本
GUI Demo and Test Script
"""

import sys
import os
import time
import pandas as pd

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def show_gui_instructions():
    """显示GUI操作说明"""
    print("🖥️ GUI中执行事件的步骤:")
    print("=" * 50)
    print("1. 启动应用程序: python main.py")
    print("2. 点击 '事件管理' 标签页")
    print("3. 在 '选择事件类型' 下拉菜单中选择 'LCA产量损失'")
    print("4. 系统会自动显示表单字段")
    print("5. 填写事件信息:")
    print("   - 选择影响日期")
    print("   - 选择产线") 
    print("   - 选择产品PN")
    print("   - 输入已损失产量")
    print("   - 输入剩余修理时间")
    print("6. 点击 '提交事件' 按钮")
    print("7. 查看处理结果和事件列表")
    print("=" * 50)

def test_data_availability():
    """测试数据可用性"""
    print("\n🔍 检查数据文件可用性...")
    
    data_files = {
        "Daily Plan": "data/daily plan.xlsx",
        "FG EOH": "data/FG EOH.xlsx", 
        "Capacity": "data/capacity .xlsx",
        "Learning Curve": "data/Learning Curve.xlsx"
    }
    
    available_files = []
    for name, path in data_files.items():
        if os.path.exists(path):
            print(f"✅ {name}: {path}")
            available_files.append(name)
        else:
            print(f"❌ {name}: {path} (文件不存在)")
    
    if "Daily Plan" in available_files:
        print("\n📊 分析Daily Plan数据结构...")
        try:
            from src.core.data_loader import DataLoader
            loader = DataLoader()
            success, message, df = loader.load_data("HSA Daily Plan")
            
            if success and df is not None:
                print(f"✅ Daily Plan加载成功: {df.shape}")
                
                # 分析可用的日期
                date_cols = [col for col in df.columns if isinstance(col, str) and '-' in col and len(col) == 10]
                print(f"📅 可用日期: {len(date_cols)} 个")
                if date_cols:
                    print(f"   示例日期: {date_cols[:3]}")
                
                # 分析可用的产线
                lines = df.iloc[:, 0].dropna().unique()
                print(f"🏭 可用产线: {len(lines)} 个")
                if len(lines) > 0:
                    print(f"   示例产线: {list(lines[:5])}")
                
                # 分析可用的产品PN
                if len(df.columns) > 2:
                    products = df.iloc[:, 2].dropna().unique()
                    print(f"📦 可用产品: {len(products)} 个")
                    if len(products) > 0:
                        print(f"   示例产品: {list(products[:5])}")
                
                return True
            else:
                print(f"❌ Daily Plan加载失败: {message}")
                return False
                
        except Exception as e:
            print(f"❌ 分析Daily Plan时出错: {str(e)}")
            return False
    else:
        print("❌ Daily Plan文件不可用，GUI功能可能受限")
        return False

def create_sample_event():
    """创建示例事件进行测试"""
    print("\n🧪 创建示例事件进行测试...")
    
    try:
        from src.core.event_manager import EventManager
        from src.core.data_loader import DataLoader
        
        def test_log(level, message):
            print(f"[{level}] {message}")
        
        # 创建组件
        data_loader = DataLoader()
        event_manager = EventManager(data_loader, test_log)
        
        # 加载Daily Plan数据
        success, message, daily_plan = data_loader.load_data("HSA Daily Plan")
        if not success:
            print(f"❌ 无法加载Daily Plan: {message}")
            return False
        
        # 获取真实数据
        date_cols = [col for col in daily_plan.columns if isinstance(col, str) and '-' in col and len(col) == 10]
        lines = daily_plan.iloc[:, 0].dropna().unique()
        
        if not date_cols or len(lines) == 0:
            print("❌ Daily Plan数据格式异常")
            return False
        
        # 查找有生产计划的产线和产品
        found_valid_data = False
        sample_event = None
        
        for line in lines[:10]:  # 检查前10个产线
            line_data = daily_plan[daily_plan.iloc[:, 0] == line]
            if line_data.empty:
                continue
                
            for date in date_cols[:5]:  # 检查前5个日期
                if date in line_data.columns:
                    date_data = line_data[date].dropna()
                    if len(date_data) > 0:
                        try:
                            # 尝试计算总和（只对数值列）
                            numeric_sum = pd.to_numeric(date_data, errors='coerce').sum()
                            if numeric_sum > 0:
                                has_production = True
                            else:
                                has_production = False
                        except:
                            # 如果不是数值，检查是否有非空值
                            has_production = len(date_data) > 0
                        
                        if has_production:
                            # 找到有计划的产线和日期
                            products = line_data.iloc[:, 2].dropna().unique()
                            if len(products) > 0:
                                sample_event = {
                                    "事件类型": "LCA产能损失",
                                    "选择影响日期": date,
                                    "选择影响班次": "T1",
                                    "选择产线": str(line),
                                    "确认产品PN": str(products[0]),
                                    "已经损失的产量": 50,
                                    "剩余修理时间": 2
                                }
                                found_valid_data = True
                                break
            if found_valid_data:
                break
        
        if not sample_event:
            print("❌ 无法找到有效的生产计划数据")
            return False
        
        print(f"📝 示例事件数据: {sample_event}")
        
        # 创建事件
        success, message = event_manager.create_event(sample_event)
        print(f"✅ 事件创建: {success}")
        print(f"📝 结果: {message}")
        
        if success:
            # 显示数据库统计
            stats = event_manager.get_database_stats()
            print(f"📊 数据库统计: {stats}")
        
        return success
        
    except Exception as e:
        print(f"❌ 创建示例事件失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("🚀 GUI演示和测试")
    print("=" * 50)
    
    # 显示操作说明
    show_gui_instructions()
    
    # 检查数据可用性
    data_ok = test_data_availability()
    
    if data_ok:
        print("\n✅ 数据检查通过，可以进行GUI测试")
        
        # 创建示例事件
        event_ok = create_sample_event()
        
        if event_ok:
            print("\n🎉 后端功能测试通过！")
            print("\n现在你可以启动GUI进行测试:")
            print("python main.py")
            print("\n在GUI中:")
            print("1. 点击'事件管理'标签")
            print("2. 选择'LCA产量损失'事件类型")
            print("3. 填写表单并提交")
            print("4. 查看事件列表中的新事件")
        else:
            print("\n❌ 后端功能测试失败")
    else:
        print("\n❌ 数据文件不完整，GUI功能可能受限")
    
    print("\n" + "=" * 50)
    print("测试完成")

if __name__ == "__main__":
    main()