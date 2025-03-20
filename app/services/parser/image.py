import io
from typing import Dict, Any
from PIL import Image
from PIL.ExifTags import TAGS
import pytesseract
from .base import BaseParser


class ImageParser(BaseParser):
    """图像文件解析器"""
    
    async def extract_text(self, file_data: bytes) -> str:
        """
        从图像文件中提取文本内容
        
        Args:
            file_data: 图像文件二进制数据
            
        Returns:
            str: 提取的文本内容
        """
        try:
            img = Image.open(io.BytesIO(file_data))
            
            # 使用pytesseract进行OCR文本识别
            text = pytesseract.image_to_string(img, lang='chi_sim+eng')
            
            return text.strip()
        except Exception as e:
            # 实际应用中应该使用日志记录错误
            print(f"图像OCR错误: {str(e)}")
            return ""
    
    async def get_metadata(self, file_data: bytes) -> Dict[str, Any]:
        """
        从图像文件中提取元数据
        
        Args:
            file_data: 图像文件二进制数据
            
        Returns:
            Dict[str, Any]: 元数据字典
        """
        metadata = {}
        try:
            img = Image.open(io.BytesIO(file_data))
            
            # 基本图像信息
            metadata['format'] = img.format
            metadata['mode'] = img.mode
            metadata['size'] = img.size
            
            # 提取EXIF信息
            if hasattr(img, '_getexif') and img._getexif():
                exif = {
                    TAGS.get(tag_id, tag_id): value
                    for tag_id, value in img._getexif().items()
                }
                
                # 过滤并添加有用的EXIF信息
                useful_tags = ['Make', 'Model', 'DateTime', 'Software']
                for tag in useful_tags:
                    if tag in exif:
                        metadata[tag.lower()] = exif[tag]
            
            return metadata
        except Exception as e:
            # 实际应用中应该使用日志记录错误
            print(f"图像元数据提取错误: {str(e)}")
            return {}
    
    def supported_mime_types(self) -> list:
        """
        获取解析器支持的MIME类型列表
        
        Returns:
            list: 支持的MIME类型列表
        """
        return [
            "image/jpeg",
            "image/png",
            "image/jpg"
        ] 