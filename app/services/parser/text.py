from typing import Dict, Any
from .base import BaseParser


class TextParser(BaseParser):
    """纯文本文件解析器"""
    
    async def extract_text(self, file_data: bytes) -> str:
        """
        从纯文本文件中提取文本内容
        
        Args:
            file_data: 文本文件二进制数据
            
        Returns:
            str: 提取的文本内容
        """
        try:
            # 尝试使用不同编码解码文本
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            
            for encoding in encodings:
                try:
                    text = file_data.decode(encoding)
                    return text.strip()
                except UnicodeDecodeError:
                    continue
            
            # 如果所有编码都失败，使用最宽松的编码
            return file_data.decode('latin-1', errors='ignore').strip()
        except Exception as e:
            # 实际应用中应该使用日志记录错误
            print(f"文本解析错误: {str(e)}")
            return ""
    
    async def get_metadata(self, file_data: bytes) -> Dict[str, Any]:
        """
        从纯文本文件中提取元数据
        
        Args:
            file_data: 文本文件二进制数据
            
        Returns:
            Dict[str, Any]: 元数据字典
        """
        metadata = {}
        try:
            # 对于纯文本文件，我们可以提供一些基本统计信息
            text = await self.extract_text(file_data)
            
            # 计算行数
            lines = text.split("\n")
            metadata['line_count'] = len(lines)
            
            # 计算单词数（简单估计）
            words = text.split()
            metadata['word_count'] = len(words)
            
            # 计算字符数
            metadata['char_count'] = len(text)
            
            # 尝试识别编码
            for encoding in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
                try:
                    file_data.decode(encoding)
                    metadata['encoding'] = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            return metadata
        except Exception as e:
            # 实际应用中应该使用日志记录错误
            print(f"文本元数据提取错误: {str(e)}")
            return {}
    
    def supported_mime_types(self) -> list:
        """
        获取解析器支持的MIME类型列表
        
        Returns:
            list: 支持的MIME类型列表
        """
        return [
            "text/plain",
            "text/html",
            "text/markdown",
            "text/csv"
        ] 