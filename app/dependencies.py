from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, Any

from app.config import get_settings
from app.services.parser import PDFParser, DocxParser, ImageParser, TextParser
from app.services.extractor import StructuredInfoExtractor
from app.services.parser_service import ResumeParserService


# 数据库连接
async def get_database():
    """获取数据库连接"""
    settings = get_settings()
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB]
    try:
        yield db
    finally:
        client.close()


# 解析服务相关依赖
def get_pdf_parser():
    """获取PDF解析器"""
    return PDFParser()


def get_docx_parser():
    """获取DOCX解析器"""
    return DocxParser()


def get_image_parser():
    """获取图像解析器"""
    return ImageParser()


def get_text_parser():
    """获取文本解析器"""
    return TextParser()


def get_structured_info_extractor():
    """获取结构化信息提取器"""
    return StructuredInfoExtractor()


def get_resume_parser_service(
    pdf_parser: PDFParser = Depends(get_pdf_parser),
    docx_parser: DocxParser = Depends(get_docx_parser),
    image_parser: ImageParser = Depends(get_image_parser),
    text_parser: TextParser = Depends(get_text_parser),
    structured_extractor: StructuredInfoExtractor = Depends(get_structured_info_extractor)
):
    """获取简历解析服务"""
    return ResumeParserService(
        pdf_parser=pdf_parser,
        docx_parser=docx_parser,
        image_parser=image_parser,
        text_parser=text_parser,
        structured_extractor=structured_extractor
    )


# 用户认证相关依赖
async def get_current_user():
    """获取当前用户（简化版，实际应用中应该实现JWT验证等）"""
    # 这里简化处理，返回一个测试用户ID
    return {"id": "test_user_id", "email": "test@example.com"} 