"""
日志格式化器
Log Formatter

自定义日志格式，提供美观且信息丰富的日志输出
"""

import logging
from datetime import datetime


class CustomFormatter(logging.Formatter):
    """自定义日志格式化器，支持彩色输出和结构化格式"""
    
    # 日志级别颜色映射（ANSI颜色码）
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
        'RESET': '\033[0m'       # 重置
    }
    
    # 日志级别emoji映射
    EMOJIS = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🚨'
    }
    
    def __init__(self, use_colors: bool = True, use_emojis: bool = True):
        """
        初始化格式化器
        
        Args:
            use_colors: 是否使用颜色
            use_emojis: 是否使用emoji
        """
        super().__init__()
        self.use_colors = use_colors
        self.use_emojis = use_emojis
    
    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录
        
        Args:
            record: 日志记录对象
            
        Returns:
            格式化后的日志字符串
        """
        # 获取时间戳
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # 获取日志级别
        level = record.levelname
        
        # 获取记录器名称
        logger_name = record.name
        
        # 获取消息
        message = record.getMessage()
        
        # 构建基础格式
        if self.use_emojis and level in self.EMOJIS:
            emoji = self.EMOJIS[level]
            log_parts = [f"[{timestamp}]", emoji, f"{level}:", message]
        else:
            log_parts = [f"[{timestamp}]", f"{level}:", message]
        
        # 如果有异常信息，添加到日志中
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            log_parts.append(f"\n{exc_text}")
        
        # 组合日志字符串
        log_line = " ".join(log_parts)
        
        # 应用颜色（仅在控制台输出时）
        if self.use_colors and hasattr(record, 'stream') and hasattr(record.stream, 'isatty'):
            if record.stream.isatty() and level in self.COLORS:
                color = self.COLORS[level]
                reset = self.COLORS['RESET']
                log_line = f"{color}{log_line}{reset}"
        
        return log_line


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器，用于机器可读的日志格式"""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        格式化为结构化日志
        
        Args:
            record: 日志记录对象
            
        Returns:
            JSON格式的日志字符串
        """
        import json
        
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # 添加自定义字段
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage']:
                log_data[key] = value
        
        return json.dumps(log_data, ensure_ascii=False)