#!/usr/bin/env python3
"""
简单GUI功能测试
Simple GUI functionality test
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_simple_event():
    """测试简单事件创建"""
    print("🧪 测试事件创建功能...")
    
    try:
        from src.core.event_manager import EventManager
        from src.core.data_loader import DataLoader
        
        def test_log(level, message):
            print(f"[{level}] {message}")
        
        # 创建组件
        data_loader = DataLoader()
        event_manager = EventManager(data_loader, test_log)
        
        # 创建一个简单的测试事件（可能不会通过LCA验证，但可以测试基本功能）
        simple_event = {
            "事件类型": "LCA产能损失",
            "选择影响日期": "2025-03-01",
            "选择影响班次": "T1",
            "选择产线": "LCA",
            "输入XX小时": 4,
            "确认产品PN": "100849603",
            "已经损失的产量": 100,
            "剩余修理时间": 2
        }
        
        print(f"📝 测试事件: {simple_event}")
        
        # 创建事件
        success, message = event_manager.create_event(simple_event)
        print(f"✅ 事件创建: {success}")
        print(f"📝 结果: {message}")
        
        if success:
            # 获取事件列表
            events = event_manager.get_events()
            print(f"📋 事件列表: {len(events)} 个事件")
            
            # 显示数据库统计
            stats = event_manager.get_database_stats()
            print(f"📊 数据库统计: {stats}")
        
        return success
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 简单GUI功能测试")
    print("=" * 50)
    
    print("📋 GUI操作步骤:")
    print("1. 运行: python main.py")
    print("2. 点击 '事件管理' 标签")
    print("3. 选择事件类型: 'LCA产量损失'")
    print("4. 填写表单字段")
    print("5. 点击 '提交事件'")
    print("6. 查看结果")
    
    print("\n🔧 后端功能测试:")
    success = test_simple_event()
    
    if success:
        print("\n🎉 后端功能正常！")
        print("\n现在可以启动GUI进行完整测试:")
        print("python main.py")
    else:
        print("\n❌ 后端功能异常")
    
    print("\n💡 GUI使用提示:")
    print("- 如果下拉菜单为空，先在'控制面板'加载数据")
    print("- 选择存在于Daily Plan中的日期和产线")
    print("- 查看系统日志获取详细错误信息")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()