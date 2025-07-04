#!/usr/bin/env python3
"""
使用真实Daily Plan数据测试LCA产能损失处理
Test LCA capacity loss processing with real Daily Plan data
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_with_real_data():
    """使用真实Daily Plan数据测试"""
    print("🔍 使用真实Daily Plan数据测试LCA处理...")
    
    try:
        from src.core.event_manager import EventManager
        from src.core.data_loader import DataLoader
        from src.core.lca_capacity_loss import LCACapacityLossProcessor
        import logging
        
        # 设置日志
        logger = logging.getLogger("test")
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        def simple_log(level, message):
            print(f"[{level}] {message}")
        
        # 加载数据
        data_loader = DataLoader()
        success, message, daily_plan = data_loader.load_data("HSA Daily Plan")
        
        if not success:
            print(f"❌ 无法加载Daily Plan: {message}")
            return False
        
        print(f"✅ Daily Plan加载成功: {daily_plan.shape}")
        print(f"📊 列数: {len(daily_plan.columns)}")
        print(f"📊 行数: {len(daily_plan)}")
        
        # 显示前几行和前几列
        print("\n📋 Daily Plan数据预览:")
        print("前5行，前5列:")
        print(daily_plan.iloc[:5, :5])
        
        # 获取真实的日期列
        date_columns = [col for col in daily_plan.columns if isinstance(col, str) and '-' in col and len(col) == 10]
        print(f"\n📅 找到日期列: {len(date_columns)} 个")
        if date_columns:
            print(f"前几个日期: {date_columns[:5]}")
        
        # 获取真实的产线
        lines = daily_plan.iloc[:, 0].dropna().unique()
        print(f"\n🏭 找到产线: {len(lines)} 个")
        print(f"前几个产线: {list(lines[:5])}")
        
        # 获取真实的产品PN
        if len(daily_plan.columns) > 2:
            products = daily_plan.iloc[:, 2].dropna().unique()
            print(f"\n📦 找到产品PN: {len(products)} 个")
            print(f"前几个产品: {list(products[:5])}")
        else:
            products = []
        
        if date_columns and len(lines) > 0:
            # 创建使用真实数据的测试事件
            real_event = {
                "事件类型": "LCA产能损失",
                "选择影响日期": date_columns[0],
                "选择影响班次": "T1",
                "选择产线": str(lines[0]),
                "输入XX小时": 2
            }
            
            if len(products) > 0:
                real_event["确认产品PN"] = str(products[0])
            
            print(f"\n🧪 测试事件: {real_event}")
            
            # 测试事件管理器
            event_manager = EventManager(data_loader, simple_log)
            success, message = event_manager.create_event(real_event)
            print(f"\n✅ 事件创建: {success}")
            print(f"📝 消息: {message}")
            
            # 测试LCA处理器
            lca_processor = LCACapacityLossProcessor(data_loader, logger)
            result = lca_processor.process_lca_capacity_loss(real_event)
            print(f"\n🔄 LCA处理结果:")
            print(f"状态: {result['status']}")
            print(f"消息: {result['message']}")
            
            if result['status'] == 'success':
                print("🎉 LCA处理成功！")
                if 'event_info' in result:
                    print(f"事件信息: {result['event_info']}")
            elif result['status'] == 'ended':
                print("⚠️  LCA处理结束（第一步检查未通过）")
            
            # 显示数据库统计
            stats = event_manager.get_database_stats()
            print(f"\n📊 数据库统计: {stats}")
            
            return True
        else:
            print("❌ 无法找到有效的日期或产线数据")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def cleanup():
    """清理测试数据"""
    files = ["data/events.db", "data/events.db-journal"]
    for file in files:
        if os.path.exists(file):
            os.remove(file)
            print(f"🗑️  已清理: {file}")

if __name__ == "__main__":
    print("🚀 开始真实数据测试")
    print("=" * 50)
    
    try:
        success = test_with_real_data()
        
        print("\n" + "=" * 50)
        if success:
            print("✅ 真实数据测试完成")
        else:
            print("❌ 真实数据测试失败")
            
        print("\n🧹 清理测试数据...")
        cleanup()
        print("✨ 清理完成")
        
    except KeyboardInterrupt:
        print("\n⏹️  测试被中断")
        cleanup()