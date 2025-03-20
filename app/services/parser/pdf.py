import io
import PyPDF2
from typing import Dict, Any
from .base import BaseParser


class PDFParser(BaseParser):
    """PDF文件解析器"""
    
    async def extract_text(self, file_data: bytes) -> str:
        """
        从PDF文件中提取文本内容
        
        Args:
            file_data: PDF文件二进制数据
            
        Returns:
            str: 提取的文本内容
        """
        text = ""
        try:
            pdf_file = io.BytesIO(file_data)
            reader = PyPDF2.PdfReader(pdf_file)
            
            # 提取文本
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() + "\n"
                
            return text.strip()
        except Exception as e:
            # 实际应用中应该使用日志记录错误
            print(f"PDF解析错误: {str(e)}")
            return ""
    
    async def get_metadata(self, file_data: bytes) -> Dict[str, Any]:
        """
        从PDF文件中提取元数据
        
        Args:
            file_data: PDF文件二进制数据
            
        Returns:
            Dict[str, Any]: 元数据字典
        """
        metadata = {}
        try:
            pdf_file = io.BytesIO(file_data)
            reader = PyPDF2.PdfReader(pdf_file)
            
            # 提取元数据
            if reader.metadata:
                for key in reader.metadata:
                    # 跳过私有属性
                    if not key.startswith('/'):
                        continue
                    # 移除前缀斜杠并添加到结果中
                    clean_key = key[1:].lower()
                    metadata[clean_key] = reader.metadata[key]
            
            # 添加页数信息
            metadata['page_count'] = len(reader.pages)
            
            return metadata
        except Exception as e:
            # 实际应用中应该使用日志记录错误
            print(f"PDF元数据提取错误: {str(e)}")
            return {}
    
    def supported_mime_types(self) -> list:
        """
        获取解析器支持的MIME类型列表
        
        Returns:
            list: 支持的MIME类型列表
        """
        return ["application/pdf"] 