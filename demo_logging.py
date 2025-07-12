#!/usr/bin/env python3
"""
日志包演示脚本
Demo script for the logging package

运行此脚本可以看到日志包的实际效果
"""

import os
import sys

# 添加src路径到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.logging import LoggerFactory, LogAnalyzer
from src.utils.logging.integration import (
    setup_system_logging, 
    log_lca_event_start, 
    log_lca_event_complete,
    log_system_startup,
    log_data_loading,
    log_event_creation
)

def demo_basic_logging():
    """演示基本日志功能"""
    print("🎯 开始演示日志包功能")
    print("=" * 50)
    
    # 设置日志系统
    setup_system_logging()
    
    # 获取不同类型的日志记录器
    lca_logger = LoggerFactory.get_lca_logger()
    system_logger = LoggerFactory.get_system_logger()
    event_logger = LoggerFactory.get_event_logger()
    
    print("\n1. 📝 基本日志记录:")
    print("-" * 30)
    
    # 系统启动日志
    log_system_startup()
    
    # LCA处理日志
    lca_logger.info("🚀 开始LCA产能损失事件处理")
    lca_logger.info("📊 DOS计算结果: 0.85天")
    lca_logger.warning("⚠️ DOS值低于阈值1.00天，需要补偿")
    lca_logger.info("🔧 计算补偿产量: 261台")
    lca_logger.info("🔍 检查后续班次调整可能性")
    lca_logger.info("✅ LCA事件处理完成")
    
    # 系统运行日志
    system_logger.info("💾 数据库连接建立")
    system_logger.info("📂 开始加载数据表")
    log_data_loading("Daily Plan", "success", "(307, 18)")
    log_data_loading("FG EOH", "success", "(177, 7)")
    
    # 事件管理日志
    log_event_creation("EVT_001", "LCA产量损失", {
        "产线": "F25",
        "班次": "T4", 
        "损失产量": 1000
    })
    event_logger.info("🔍 事件验证通过")
    event_logger.info("💾 事件已保存到数据库")
    
    # 模拟一些错误和警告
    lca_logger.error("❌ 数据验证失败: PN不存在")
    system_logger.warning("⚠️ 内存使用率较高: 85%")
    
    print("\n✅ 基本日志演示完成!")

def demo_lca_event_logging():
    """演示LCA事件专用日志"""
    print("\n2. 🏭 LCA事件专用日志:")
    print("-" * 30)
    
    # 模拟LCA事件数据
    event_data = {
        "event_id": "EVT_LCA_001",
        "事件类型": "LCA产量损失", 
        "选择影响日期": "2025-03-01",
        "选择影响班次": "T4",
        "选择产线": "F25",
        "确认产品PN": "200723400",
        "已经损失的产量": 1000,
        "剩余修理时间": 3
    }
    
    # 记录事件开始
    log_lca_event_start("EVT_LCA_001", event_data)
    
    # 模拟处理结果
    result = {
        "status": "success",
        "dos_analysis": {
            "new_dos": 0.90,
            "threshold": 1.00,
            "acceptable": False
        },
        "compensation_calculation": {
            "compensation_needed": 261,
            "original_production": 1400,
            "required_total_production": 1661
        },
        "subsequent_shifts_check": {
            "message": "后续2班次中1班次有事件",
            "adjustable_shifts": 1
        }
    }
    
    # 记录事件完成
    log_lca_event_complete("EVT_LCA_001", result)
    
    print("✅ LCA事件日志演示完成!")

def demo_log_analysis():
    """演示日志分析功能"""
    print("\n3. 📊 日志分析功能:")
    print("-" * 30)
    
    # 创建分析器
    analyzer = LogAnalyzer()
    
    # 生成今日报告
    print("📈 生成今日日志分析报告:")
    daily_report = analyzer.generate_daily_report()
    print(daily_report)
    
    # 查找LCA事件
    lca_events = analyzer.find_lca_events()
    print(f"\n🔍 找到 {len(lca_events)} 个LCA相关日志条目")
    
    if lca_events:
        print("最近的LCA事件日志:")
        for event in lca_events[-3:]:  # 显示最近3个
            print(f"  [{event['time']}] {event['message']}")

def show_log_files():
    """显示生成的日志文件"""
    print("\n4. 📁 生成的日志文件:")
    print("-" * 30)
    
    log_dir = "logs"
    if os.path.exists(log_dir):
        log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
        if log_files:
            print(f"📂 日志目录: {log_dir}/")
            for log_file in sorted(log_files):
                file_path = os.path.join(log_dir, log_file)
                file_size = os.path.getsize(file_path)
                print(f"  📄 {log_file} ({file_size} bytes)")
        else:
            print("📂 日志目录为空")
    else:
        print("📂 日志目录不存在")

def main():
    """主函数"""
    try:
        # 演示各种日志功能
        demo_basic_logging()
        demo_lca_event_logging() 
        demo_log_analysis()
        show_log_files()
        
        print("\n" + "=" * 50)
        print("🎉 日志包演示完成!")
        print("📁 查看 logs/ 目录可以看到生成的日志文件")
        print("🔍 日志文件按模块和日期自动分类保存")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        LoggerFactory.close_all_loggers()

if __name__ == "__main__":
    main()