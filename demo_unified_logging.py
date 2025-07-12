#!/usr/bin/env python3
"""
统一日志演示脚本
Demo script for unified logging

演示统一日志文件功能
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

def demo_unified_logging():
    """演示统一日志功能"""
    print("🎯 演示统一日志功能")
    print("=" * 50)
    
    # 设置日志系统
    setup_system_logging()
    
    # 获取不同类型的日志记录器
    lca_logger = LoggerFactory.get_lca_logger()
    system_logger = LoggerFactory.get_system_logger()
    event_logger = LoggerFactory.get_event_logger()
    data_logger = LoggerFactory.get_data_logger()
    
    print("\n📝 所有模块日志将合并到同一个文件:")
    print("-" * 40)
    
    # 系统启动
    log_system_startup()
    system_logger.info("💾 数据库连接建立")
    
    # 数据加载
    log_data_loading("Daily Plan", "start")
    data_logger.info("📂 正在解析Excel文件结构")
    log_data_loading("Daily Plan", "success", "(307, 18)")
    log_data_loading("FG EOH", "success", "(177, 7)")
    
    # LCA事件处理
    event_data = {
        "event_id": "EVT_LCA_002",
        "事件类型": "LCA产量损失", 
        "选择影响日期": "2025-03-01",
        "选择影响班次": "T4",
        "选择产线": "F25"
    }
    
    log_lca_event_start("EVT_LCA_002", event_data)
    lca_logger.info("🧮 开始DOS计算")
    lca_logger.info("📊 DOS计算结果: 0.85天")
    lca_logger.warning("⚠️ DOS值低于阈值，需要补偿")
    lca_logger.info("🔧 计算补偿产量: 261台")
    lca_logger.info("🔍 检查后续班次调整可能性")
    
    # 事件管理
    log_event_creation("EVT_002", "LCA产量损失", {"产线": "F25", "班次": "T4"})
    event_logger.info("🔍 事件数据验证通过")
    event_logger.info("💾 事件保存到数据库")
    
    # 完成LCA事件
    result = {
        "status": "success",
        "dos_analysis": {"new_dos": 0.85},
        "compensation_calculation": {"compensation_needed": 261}
    }
    log_lca_event_complete("EVT_LCA_002", result)
    
    # 模拟一些错误
    lca_logger.error("❌ 产线F99不存在")
    system_logger.warning("⚠️ 系统内存使用率: 89%")
    
    print("\n✅ 统一日志演示完成!")

def show_unified_log():
    """显示统一日志文件内容"""
    print("\n📁 统一日志文件内容:")
    print("-" * 40)
    
    log_dir = "logs"
    from datetime import datetime
    date_str = datetime.now().strftime("%Y-%m-%d")
    unified_log_file = os.path.join(log_dir, f"system_{date_str}.log")
    
    if os.path.exists(unified_log_file):
        print(f"📄 文件: {unified_log_file}")
        print("内容:")
        
        with open(unified_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # 显示最后20行
            for line in lines[-20:]:
                print(f"  {line.rstrip()}")
    else:
        print(f"❌ 未找到统一日志文件: {unified_log_file}")

def analyze_unified_logs():
    """分析统一日志"""
    print("\n📊 统一日志分析:")
    print("-" * 40)
    
    analyzer = LogAnalyzer()
    report = analyzer.generate_daily_report()
    print(report)

def main():
    """主函数"""
    try:
        # 清理旧的分散日志文件
        log_dir = "logs"
        if os.path.exists(log_dir):
            for file in os.listdir(log_dir):
                if file.endswith('.log') and not file.startswith('system_'):
                    os.remove(os.path.join(log_dir, file))
                    print(f"🗑️ 删除旧日志文件: {file}")
        
        # 演示统一日志
        demo_unified_logging()
        show_unified_log()
        analyze_unified_logs()
        
        print("\n" + "=" * 50)
        print("🎉 统一日志演示完成!")
        print("📁 所有模块的日志现在都合并在 system_YYYY-MM-DD.log 文件中")
        print("🏷️ 每条日志都包含模块标识 [LCA] [EVENT] [SYS] [DATA]")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        LoggerFactory.close_all_loggers()

if __name__ == "__main__":
    main()