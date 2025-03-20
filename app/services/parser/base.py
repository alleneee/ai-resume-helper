from abc import ABC, abstractmethod
from typing import Any, Optional, Dict


class BaseParser(ABC):
    """文档解析器基类"""
    
    @abstractmethod
    async def extract_text(self, file_data: bytes) -> str:
        """
        从文件数据中提取文本内容
        
        Args:
            file_data: 文件二进制数据
            
        Returns:
            str: 提取的文本内容
        """
        pass
    
    @abstractmethod
    async def get_metadata(self, file_data: bytes) -> Dict[str, Any]:
        """
        从文件数据中提取元数据
        
        Args:
            file_data: 文件二进制数据
            
        Returns:
            Dict[str, Any]: 元数据字典
        """
        pass
    
    def is_supported(self, mime_type: str) -> bool:
        """
        检查解析器是否支持给定MIME类型
        
        Args:
            mime_type: 文件MIME类型
            
        Returns:
            bool: 是否支持
        """
        return mime_type in self.supported_mime_types()
    
    @abstractmethod
    def supported_mime_types(self) -> list:
        """
        获取解析器支持的MIME类型列表
        
        Returns:
            list: 支持的MIME类型列表
        """
        pass 