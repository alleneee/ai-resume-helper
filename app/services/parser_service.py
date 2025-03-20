import os
import mimetypes
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, BinaryIO, Tuple
from fastapi import UploadFile, HTTPException

from app.models.resume import ResumeData, FileType, ResumeFile
from app.services.parser import PDFParser, DocxParser, ImageParser, TextParser, BaseParser
from app.services.extractor import StructuredInfoExtractor
from app.config import get_settings


class ResumeParserService:
    """简历解析服务"""
    
    def __init__(
        self,
        pdf_parser: PDFParser,
        docx_parser: DocxParser,
        image_parser: ImageParser,
        text_parser: TextParser,
        structured_extractor: StructuredInfoExtractor
    ):
        self.parsers = {
            'application/pdf': pdf_parser,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': docx_parser,
            'application/msword': docx_parser,
            'image/jpeg': image_parser,
            'image/jpg': image_parser,
            'image/png': image_parser,
            'text/plain': text_parser,
            'text/html': text_parser,
            'text/markdown': text_parser,
            'text/csv': text_parser
        }
        self.extractor = structured_extractor
        self.settings = get_settings()
        
        # 确保上传目录存在
        os.makedirs(self.settings.UPLOAD_DIR, exist_ok=True)
    
    async def parse_resume_file(self, file: UploadFile, user_id: str) -> Tuple[ResumeFile, ResumeData]:
        """
        解析上传的简历文件
        
        Args:
            file: 上传的文件对象
            user_id: 用户ID
            
        Returns:
            Tuple[ResumeFile, ResumeData]: 简历文件记录和解析后的数据
        """
        # 检查文件类型
        mime_type = self._detect_mime_type(file)
        if not self._is_supported_mime_type(mime_type):
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {mime_type}")
        
        # 检查文件大小
        file_size = await self._get_file_size(file)
        if file_size > self.settings.MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=400, detail=f"文件过大，最大允许{self.settings.MAX_UPLOAD_SIZE/(1024*1024)}MB")
        
        # 保存文件
        file_id = str(uuid.uuid4())
        file_path, file_type = await self._save_file(file, file_id, user_id)
        
        # 创建简历文件记录
        resume_file = ResumeFile(
            id=file_id,
            user_id=user_id,
            filename=file.filename,
            file_path=str(file_path),
            file_type=file_type,
            file_size=file_size,
            parsed=False
        )
        
        # 解析文件内容
        file_data = await self._read_file(file_path)
        parser = self._get_parser(mime_type)
        
        # 提取文本
        raw_text = await parser.extract_text(file_data)
        
        # 提取结构化信息
        parsed_data = await self.extractor.extract_info(raw_text)
        
        # 更新简历文件记录
        resume_file.parsed = True
        resume_file.parsed_data = parsed_data
        
        return resume_file, parsed_data
    
    def _detect_mime_type(self, file: UploadFile) -> str:
        """
        检测文件MIME类型
        
        Args:
            file: 上传的文件对象
            
        Returns:
            str: MIME类型
        """
        # 优先使用文件提供的content_type
        if file.content_type and file.content_type != 'application/octet-stream':
            return file.content_type
        
        # 根据文件扩展名猜测MIME类型
        if file.filename:
            guessed_type = mimetypes.guess_type(file.filename)[0]
            if guessed_type:
                return guessed_type
        
        # 默认返回二进制类型
        return 'application/octet-stream'
    
    def _is_supported_mime_type(self, mime_type: str) -> bool:
        """
        检查MIME类型是否支持
        
        Args:
            mime_type: MIME类型
            
        Returns:
            bool: 是否支持
        """
        return mime_type in self.parsers
    
    async def _get_file_size(self, file: UploadFile) -> int:
        """
        获取文件大小
        
        Args:
            file: 上传的文件对象
            
        Returns:
            int: 文件大小(字节)
        """
        file.file.seek(0, os.SEEK_END)
        size = file.file.tell()
        file.file.seek(0)
        return size
    
    async def _save_file(self, file: UploadFile, file_id: str, user_id: str) -> Tuple[Path, FileType]:
        """
        保存上传的文件
        
        Args:
            file: 上传的文件对象
            file_id: 文件ID
            user_id: 用户ID
            
        Returns:
            Tuple[Path, FileType]: 文件路径和文件类型
        """
        # 创建用户目录
        user_dir = Path(self.settings.UPLOAD_DIR) / user_id
        os.makedirs(user_dir, exist_ok=True)
        
        # 获取文件扩展名
        if file.filename:
            ext = Path(file.filename).suffix.lower().lstrip('.')
        else:
            ext = self._mime_to_extension(self._detect_mime_type(file))
        
        # 转换为FileType枚举
        try:
            file_type = FileType(ext)
        except ValueError:
            # 如果不是预定义的类型，使用默认扩展名
            ext = 'txt'
            file_type = FileType.TXT
        
        # 构建文件路径
        file_path = user_dir / f"{file_id}.{ext}"
        
        # 写入文件
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        return file_path, file_type
    
    async def _read_file(self, file_path: Path) -> bytes:
        """
        读取文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            bytes: 文件二进制内容
        """
        with open(file_path, 'rb') as f:
            return f.read()
    
    def _get_parser(self, mime_type: str) -> BaseParser:
        """
        获取适合MIME类型的解析器
        
        Args:
            mime_type: MIME类型
            
        Returns:
            BaseParser: 解析器实例
        """
        return self.parsers[mime_type]
    
    def _mime_to_extension(self, mime_type: str) -> str:
        """
        将MIME类型转换为文件扩展名
        
        Args:
            mime_type: MIME类型
            
        Returns:
            str: 文件扩展名
        """
        mime_map = {
            'application/pdf': 'pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'application/msword': 'doc',
            'image/jpeg': 'jpg',
            'image/png': 'png',
            'text/plain': 'txt',
            'text/html': 'html',
            'text/markdown': 'md',
            'text/csv': 'csv'
        }
        
        return mime_map.get(mime_type, 'txt') 