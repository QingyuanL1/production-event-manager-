"""
日志工厂类
Logger Factory

统一创建和管理系统中的各种日志记录器
"""

import logging
import os
from datetime import datetime
from typing import Optional, Dict
from .log_formatter import CustomFormatter


class LoggerFactory:
    """日志工厂类，负责创建和配置各种日志记录器"""
    
    _loggers: Dict[str, logging.Logger] = {}
    _log_dir = "logs"
    
    @classmethod
    def setup_log_directory(cls, log_dir: str = None):
        """设置日志目录"""
        if log_dir:
            cls._log_dir = log_dir
        
        # 确保日志目录存在
        if not os.path.exists(cls._log_dir):
            os.makedirs(cls._log_dir)
    
    @classmethod
    def get_logger(cls, name: str, 
                   level: int = logging.INFO,
                   file_logging: bool = True,
                   console_logging: bool = True,
                   unified_log: bool = True) -> logging.Logger:
        """
        获取或创建日志记录器
        
        Args:
            name: 日志记录器名称
            level: 日志级别
            file_logging: 是否启用文件日志
            console_logging: 是否启用控制台日志
            unified_log: 是否使用统一日志文件
            
        Returns:
            配置好的日志记录器
        """
        if name in cls._loggers:
            return cls._loggers[name]
        
        # 创建日志记录器
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # 清除现有的处理器
        logger.handlers.clear()
        
        # 创建自定义格式器，包含模块信息
        from .log_formatter import UnifiedFormatter
        formatter = UnifiedFormatter(include_module=True) if unified_log else CustomFormatter()
        
        # 添加控制台处理器
        if console_logging:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(CustomFormatter())  # 控制台仍使用原格式
            logger.addHandler(console_handler)
        
        # 添加文件处理器
        if file_logging:
            cls.setup_log_directory()
            
            # 根据unified_log决定文件名
            date_str = datetime.now().strftime("%Y-%m-%d")
            if unified_log:
                log_file = os.path.join(cls._log_dir, f"system_{date_str}.log")
            else:
                log_file = os.path.join(cls._log_dir, f"{name}_{date_str}.log")
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # 防止日志向上传播
        logger.propagate = False
        
        # 缓存日志记录器
        cls._loggers[name] = logger
        
        return logger
    
    @classmethod
    def get_lca_logger(cls) -> logging.Logger:
        """获取LCA处理专用日志记录器"""
        return cls.get_logger(
            name="lca_processor",
            level=logging.INFO,
            file_logging=True,
            console_logging=True
        )
    
    @classmethod
    def get_system_logger(cls) -> logging.Logger:
        """获取系统运行日志记录器"""
        return cls.get_logger(
            name="system",
            level=logging.INFO,
            file_logging=True,
            console_logging=True
        )
    
    @classmethod
    def get_event_logger(cls) -> logging.Logger:
        """获取事件管理日志记录器"""
        return cls.get_logger(
            name="event_manager",
            level=logging.INFO,
            file_logging=True,
            console_logging=True
        )
    
    @classmethod
    def get_data_logger(cls) -> logging.Logger:
        """获取数据加载日志记录器"""
        return cls.get_logger(
            name="data_loader",
            level=logging.INFO,
            file_logging=True,
            console_logging=False  # 数据加载日志只记录到文件
        )
    
    @classmethod
    def close_all_loggers(cls):
        """关闭所有日志记录器的文件处理器"""
        for logger in cls._loggers.values():
            for handler in logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
        cls._loggers.clear()