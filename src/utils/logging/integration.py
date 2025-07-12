"""
日志包集成模块
Logging Package Integration

将新的日志包集成到现有系统中
"""

import logging
from .logger_factory import LoggerFactory


def setup_system_logging():
    """设置系统级日志"""
    # 设置日志目录
    LoggerFactory.setup_log_directory("logs")
    
    # 为各个模块创建专用日志记录器
    loggers = {
        'lca_processor': LoggerFactory.get_lca_logger(),
        'event_manager': LoggerFactory.get_event_logger(),
        'system': LoggerFactory.get_system_logger(),
        'data_loader': LoggerFactory.get_data_logger()
    }
    
    return loggers


def get_module_logger(module_name: str) -> logging.Logger:
    """
    根据模块名获取对应的日志记录器
    
    Args:
        module_name: 模块名称
        
    Returns:
        日志记录器
    """
    logger_mapping = {
        'lca_capacity_loss': LoggerFactory.get_lca_logger(),
        'event_manager': LoggerFactory.get_event_logger(),
        'data_loader': LoggerFactory.get_data_logger(),
        'main_ui': LoggerFactory.get_system_logger(),
        'database_manager': LoggerFactory.get_system_logger()
    }
    
    return logger_mapping.get(module_name, LoggerFactory.get_system_logger())


def log_lca_event_start(event_id: str, event_data: dict):
    """记录LCA事件开始处理"""
    logger = LoggerFactory.get_lca_logger()
    logger.info(f"🚀 开始处理LCA事件: {event_id}")
    logger.info(f"📋 事件详情: {event_data.get('事件类型', 'Unknown')}")
    logger.info(f"📍 影响范围: {event_data.get('选择影响日期')} {event_data.get('选择影响班次')} {event_data.get('选择产线')}")


def log_lca_event_complete(event_id: str, result: dict):
    """记录LCA事件处理完成"""
    logger = LoggerFactory.get_lca_logger()
    
    if result.get('status') == 'success':
        logger.info(f"✅ LCA事件处理完成: {event_id}")
        
        # 记录关键结果
        if 'dos_analysis' in result:
            dos_result = result['dos_analysis']
            logger.info(f"📊 DOS分析结果: {dos_result.get('new_dos', 'N/A')}天")
        
        if 'compensation_calculation' in result:
            comp_result = result['compensation_calculation']
            logger.info(f"🔧 补偿产量: {comp_result.get('compensation_needed', 0)}")
        
        if 'subsequent_shifts_check' in result:
            shift_result = result['subsequent_shifts_check']
            logger.info(f"🔍 后续班次: {shift_result.get('message', 'N/A')}")
    else:
        logger.error(f"❌ LCA事件处理失败: {event_id}")
        logger.error(f"错误信息: {result.get('message', 'Unknown error')}")


def log_system_startup():
    """记录系统启动"""
    logger = LoggerFactory.get_system_logger()
    logger.info("🚀 生产排班系统启动")
    logger.info("📊 开始加载数据表...")


def log_system_shutdown():
    """记录系统关闭"""
    logger = LoggerFactory.get_system_logger()
    logger.info("🔄 系统正常关闭")
    LoggerFactory.close_all_loggers()


def log_data_loading(data_type: str, status: str, details: str = ""):
    """记录数据加载过程"""
    logger = LoggerFactory.get_data_logger()
    
    if status == "start":
        logger.info(f"📂 开始加载 {data_type}")
    elif status == "success":
        logger.info(f"✅ {data_type} 加载成功 {details}")
    elif status == "error":
        logger.error(f"❌ {data_type} 加载失败: {details}")


def log_event_creation(event_id: str, event_type: str, user_data: dict):
    """记录事件创建"""
    logger = LoggerFactory.get_event_logger()
    logger.info(f"📝 创建事件: {event_id}")
    logger.info(f"🏷️ 事件类型: {event_type}")
    logger.info(f"📋 事件数据: {user_data}")


def log_database_operation(operation: str, table: str, status: str, details: str = ""):
    """记录数据库操作"""
    logger = LoggerFactory.get_system_logger()
    
    if status == "success":
        logger.info(f"💾 数据库操作成功: {operation} {table} {details}")
    else:
        logger.error(f"❌ 数据库操作失败: {operation} {table} - {details}")


# 错误日志的便捷函数
def log_error(module: str, error: Exception, context: str = ""):
    """记录错误信息"""
    logger = get_module_logger(module)
    logger.error(f"❌ {module} 错误: {str(error)}")
    if context:
        logger.error(f"📍 错误上下文: {context}")


def log_warning(module: str, message: str):
    """记录警告信息"""
    logger = get_module_logger(module)
    logger.warning(f"⚠️ {module} 警告: {message}")


def log_performance(module: str, operation: str, duration: float):
    """记录性能信息"""
    logger = get_module_logger(module)
    logger.info(f"⏱️ {module} 性能: {operation} 耗时 {duration:.2f}秒")