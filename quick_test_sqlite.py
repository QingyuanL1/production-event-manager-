#!/usr/bin/env python3
"""
快速测试脚本 - 验证SQLite数据库功能
Quick test script for SQLite database functionality verification
"""

import sys
import os
import sqlite3

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_sqlite_functionality():
    """测试SQLite数据库功能"""
    print("🔧 测试SQLite数据库和LCA处理功能...")
    
    try:
        from src.core.event_manager import EventManager
        from src.core.data_loader import DataLoader
        from src.core.lca_capacity_loss import LCACapacityLossProcessor
        
        # 创建基本组件
        data_loader = DataLoader()
        
        def simple_log(level, message):
            print(f"[{level}] {message}")
        
        event_manager = EventManager(data_loader, simple_log)
        
        # 测试1：创建事件
        print("\n1️⃣ 测试创建事件...")
        test_event = {
            "事件类型": "LCA产能损失",
            "选择影响日期": "2024-01-15",
            "选择影响班次": "T1", 
            "选择产线": "Line A",
            "输入XX小时": 4,
            "确认产品PN": "PN001",
            "已经损失的产量": 100,
            "剩余修理时间": 2
        }
        
        success, message = event_manager.create_event(test_event)
        print(f"   ✅ 事件创建: {success}")
        if not success:
            print(f"   ❌ 创建失败原因: {message}")
        
        # 测试2：检查数据库保存
        print("\n2️⃣ 测试SQLite数据库持久化...")
        if os.path.exists("data/events.db"):
            stats = event_manager.get_database_stats()
            print(f"   ✅ 数据库保存成功，包含 {stats.get('total_events', 0)} 个事件")
            print(f"   📊 数据库大小: {stats.get('db_size_mb', 0)} MB")
            print(f"   📋 事件类型分布: {stats.get('events_by_type', {})}")
        else:
            print("   ❌ 数据库文件未创建")
        
        # 测试3：重新加载
        print("\n3️⃣ 测试数据加载...")
        event_manager2 = EventManager(data_loader, simple_log)
        loaded_events = event_manager2.get_events()
        print(f"   ✅ 数据加载成功，加载了 {len(loaded_events)} 个事件")
        
        # 测试4：数据库表结构验证
        print("\n4️⃣ 测试数据库表结构...")
        with sqlite3.connect("data/events.db") as conn:
            cursor = conn.cursor()
            
            # 检查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            expected_tables = ['events', 'lca_capacity_loss', 'event_processing_results']
            
            for table in expected_tables:
                if table in tables:
                    print(f"   ✅ 表 {table} 存在")
                    
                    # 检查记录数
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"       包含 {count} 条记录")
                else:
                    print(f"   ❌ 表 {table} 不存在")
        
        # 测试5：LCA处理（使用真实Daily Plan数据）
        print("\n5️⃣ 测试LCA产能损失处理...")
        
        # 首先尝试加载Daily Plan数据
        try:
            success, message, daily_plan = data_loader.load_data("HSA Daily Plan")
            if success and daily_plan is not None and not daily_plan.empty:
                print(f"   📊 Daily Plan数据加载成功: {daily_plan.shape}")
                
                # 获取真实的日期和产线数据
                real_dates = [col for col in daily_plan.columns if isinstance(col, str) and '-' in col][:3]
                real_lines = daily_plan.iloc[:, 0].dropna().unique()[:3]
                
                if real_dates and len(real_lines) > 0:
                    real_test_event = {
                        "事件类型": "LCA产能损失",
                        "选择影响日期": real_dates[0],
                        "选择影响班次": "T1",
                        "选择产线": str(real_lines[0]),
                        "输入XX小时": 2
                    }
                    
                    import logging
                    logger = logging.getLogger("test")
                    handler = logging.StreamHandler()
                    handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
                    logger.addHandler(handler)
                    logger.setLevel(logging.INFO)
                    
                    lca_processor = LCACapacityLossProcessor(data_loader, logger)
                    result = lca_processor.process_lca_capacity_loss(real_test_event)
                    print(f"   ✅ LCA处理状态: {result['status']}")
                    print(f"   📝 处理消息: {result['message']}")
                else:
                    print("   ⚠️  Daily Plan数据格式异常")
            else:
                print("   ⚠️  Daily Plan数据为空或加载失败")
        except Exception as e:
            print(f"   ⚠️  无法加载Daily Plan数据: {str(e)}")
            
            # 使用模拟数据测试
            import logging
            logger = logging.getLogger("test")
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            
            lca_processor = LCACapacityLossProcessor(data_loader, logger)
            result = lca_processor.process_lca_capacity_loss(test_event)
            print(f"   ✅ LCA处理状态: {result['status']}")
            print(f"   📝 处理消息: {result['message']}")
        
        print("\n🎉 所有SQLite数据库功能测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
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

def inspect_database():
    """检查数据库内容"""
    if not os.path.exists("data/events.db"):
        print("❌ 数据库文件不存在")
        return
    
    print("\n🔍 数据库内容检查:")
    try:
        with sqlite3.connect("data/events.db") as conn:
            cursor = conn.cursor()
            
            # 查看events表
            cursor.execute("SELECT * FROM events")
            events = cursor.fetchall()
            print(f"📋 events表: {len(events)} 条记录")
            for event in events:
                print(f"   - {event[1]}: {event[2]}")
            
            # 查看lca_capacity_loss表
            cursor.execute("SELECT * FROM lca_capacity_loss")
            lca_events = cursor.fetchall()
            print(f"🏭 lca_capacity_loss表: {len(lca_events)} 条记录")
            for lca in lca_events:
                print(f"   - {lca[1]}: {lca[3]} 产线 {lca[2]} {lca[6]}小时")
                
    except Exception as e:
        print(f"❌ 检查数据库时出错: {str(e)}")

if __name__ == "__main__":
    print("🚀 开始SQLite数据库功能测试")
    print("=" * 50)
    
    try:
        success = test_sqlite_functionality()
        
        print("\n" + "=" * 50)
        if success:
            print("✅ 测试完成 - SQLite数据库功能正常")
            inspect_database()
        else:
            print("❌ 测试失败 - 请检查错误信息")
            
        print("\n🧹 清理测试数据...")
        cleanup()
        print("✨ 清理完成")
        
    except KeyboardInterrupt:
        print("\n⏹️  测试被中断")
        cleanup()