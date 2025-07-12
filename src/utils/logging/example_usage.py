"""
日志包使用示例
Example Usage of Logging Package

演示如何使用日志包的各种功能
"""

from .logger_factory import LoggerFactory
from .log_analyzer import LogAnalyzer


def demo_basic_logging():
    """演示基本日志功能"""
    print("=== 基本日志功能演示 ===")
    
    # 获取不同类型的日志记录器
    lca_logger = LoggerFactory.get_lca_logger()
    system_logger = LoggerFactory.get_system_logger()
    event_logger = LoggerFactory.get_event_logger()
    
    # 记录不同级别的日志
    lca_logger.info("🚀 LCA产能损失事件处理开始")
    lca_logger.warning("⚠️ DOS值低于阈值，需要补偿")
    
    system_logger.info("✅ 系统启动成功")
    system_logger.debug("🔍 加载配置文件")
    
    event_logger.info("📋 创建新事件: EVT_001")
    event_logger.error("❌ 事件处理失败: 数据验证错误")
    
    print("日志已记录到控制台和文件")


def demo_log_analysis():
    """演示日志分析功能"""
    print("\n=== 日志分析功能演示 ===")
    
    # 创建日志分析器
    analyzer = LogAnalyzer()
    
    # 生成今日报告
    daily_report = analyzer.generate_daily_report()
    print("📊 今日日志报告:")
    print(daily_report)
    
    # 查找LCA相关事件
    lca_events = analyzer.find_lca_events()
    print(f"\n🔍 找到 {len(lca_events)} 个LCA相关事件")
    
    # 导出分析报告
    analyzer.export_report("log_analysis_report.json")


def demo_custom_logger():
    """演示自定义日志记录器"""
    print("\n=== 自定义日志记录器演示 ===")
    
    # 创建自定义日志记录器
    custom_logger = LoggerFactory.get_logger(
        name="custom_module",
        level=logging.DEBUG,
        file_logging=True,
        console_logging=True
    )
    
    # 使用自定义日志记录器
    custom_logger.debug("🔍 调试信息: 开始处理数据")
    custom_logger.info("ℹ️ 处理进度: 50%")
    custom_logger.warning("⚠️ 性能警告: 处理时间较长")
    custom_logger.error("❌ 处理错误: 文件不存在")
    
    print("自定义日志已记录")


if __name__ == "__main__":
    import logging
    
    # 设置日志目录
    LoggerFactory.setup_log_directory("./logs")
    
    # 运行演示
    demo_basic_logging()
    demo_log_analysis()
    demo_custom_logger()
    
    # 清理资源
    LoggerFactory.close_all_loggers()
    
    print("\n✅ 日志包演示完成！")
    print("📁 日志文件保存在 ./logs/ 目录下")