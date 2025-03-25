"""
日志工具模块
"""
import logging
import os
import sys
from datetime import datetime
import json
from config.app import config

# 日志级别映射
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

# 确保日志目录存在
log_dir = os.path.join(os.getcwd(), "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 日志文件路径
log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")

# 默认日志级别
default_level = LOG_LEVELS.get(config["log"]["level"], logging.INFO)

# 日志格式
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# 配置根日志
root_logger = logging.getLogger()
root_logger.setLevel(default_level)

# 添加控制台处理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

# 添加文件处理器
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)

class Logger:
    """
    日志记录器类
    提供结构化日志记录功能
    """
    
    def __init__(self, name=None):
        """
        初始化日志记录器
        
        Args:
            name: 日志记录器名称
        """
        self.logger = logging.getLogger(name or __name__)
    
    def _format_message(self, message, data=None):
        """
        格式化日志消息
        
        Args:
            message: 日志消息
            data: 附加数据
            
        Returns:
            格式化后的消息
        """
        if data:
            if isinstance(data, dict):
                try:
                    return f"{message} {json.dumps(data, ensure_ascii=False)}"
                except:
                    return f"{message} {str(data)}"
            return f"{message} {str(data)}"
        return message
    
    def debug(self, message, data=None):
        """
        记录调试级别日志
        
        Args:
            message: 日志消息
            data: 附加数据
        """
        self.logger.debug(self._format_message(message, data))
    
    def info(self, message, data=None):
        """
        记录信息级别日志
        
        Args:
            message: 日志消息
            data: 附加数据
        """
        self.logger.info(self._format_message(message, data))
    
    def warning(self, message, data=None):
        """
        记录警告级别日志
        
        Args:
            message: 日志消息
            data: 附加数据
        """
        self.logger.warning(self._format_message(message, data))
    
    def error(self, message, data=None):
        """
        记录错误级别日志
        
        Args:
            message: 日志消息
            data: 附加数据
        """
        self.logger.error(self._format_message(message, data))
    
    def critical(self, message, data=None):
        """
        记录严重错误级别日志
        
        Args:
            message: 日志消息
            data: 附加数据
        """
        self.logger.critical(self._format_message(message, data))

# 创建默认日志记录器实例
logger = Logger("app")
