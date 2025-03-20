from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum


class ContactInfo(BaseModel):
    """联系信息模型"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    links: Optional[List[str]] = None


class EducationExperience(BaseModel):
    """教育经历模型"""
    institution: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    gpa: Optional[str] = None
    description: Optional[str] = None
    achievements: Optional[List[str]] = None


class WorkExperience(BaseModel):
    """工作经历模型"""
    company: str
    position: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    location: Optional[str] = None
    description: Optional[str] = None
    achievements: Optional[List[str]] = None


class Project(BaseModel):
    """项目经历模型"""
    name: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    technologies: Optional[List[str]] = None
    link: Optional[str] = None
    achievements: Optional[List[str]] = None


class Certification(BaseModel):
    """证书模型"""
    name: str
    issuer: Optional[str] = None
    date: Optional[date] = None
    expiry_date: Optional[date] = None
    description: Optional[str] = None
    link: Optional[str] = None


class Language(BaseModel):
    """语言技能模型"""
    name: str
    level: Optional[str] = None


class FileType(str, Enum):
    """文件类型枚举"""
    PDF = "pdf"
    DOCX = "docx"
    JPG = "jpg"
    PNG = "png"
    TXT = "txt"


class ResumeData(BaseModel):
    """简历数据模型"""
    raw_text: str
    contact_info: Optional[ContactInfo] = None
    education: Optional[List[EducationExperience]] = None
    work_experience: Optional[List[WorkExperience]] = None
    skills: Optional[List[str]] = None
    projects: Optional[List[Project]] = None
    certifications: Optional[List[Certification]] = None
    languages: Optional[List[Language]] = None
    summary: Optional[str] = None


class ResumeFile(BaseModel):
    """简历文件模型"""
    id: str = Field(..., description="简历文件ID")
    user_id: str = Field(..., description="用户ID")
    filename: str = Field(..., description="文件名")
    file_path: str = Field(..., description="存储路径")
    file_type: FileType = Field(..., description="文件类型")
    file_size: int = Field(..., description="文件大小(字节)")
    parsed: bool = Field(False, description="是否已解析")
    parsed_data: Optional[ResumeData] = None
    uploaded_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ResumeUploadResponse(BaseModel):
    """简历上传响应"""
    resume_id: str
    filename: str
    file_type: str
    message: str = "文件上传成功" 