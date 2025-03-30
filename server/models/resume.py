"""
简历相关的数据模型
"""
from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId

class PyObjectId(str):
    """用于处理MongoDB ObjectId的自定义类型 (Pydantic v2兼容)"""
    
    @classmethod
    def validate(cls, v, info):
        """验证ObjectId并转换为字符串"""
        if not ObjectId.is_valid(v):
            if not isinstance(v, ObjectId):
                raise ValueError("无效的ObjectId")
        return str(v)
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        """为Pydantic v2提供核心模式"""
        from pydantic_core import core_schema
        return core_schema.str_schema()
    
    @classmethod
    def __get_pydantic_json_schema__(cls, schema, field_schema):
        """为JSON模式提供类型信息"""
        field_schema.update(type="string")

class ResumeBase(BaseModel):
    """简历基础模型"""
    title: str = Field(..., description="简历标题", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="简历描述", max_length=500)

class ResumeCreate(ResumeBase):
    """创建简历的请求模型"""
    file_name: str = Field(..., description="原始文件名")
    file_path: str = Field(..., description="存储路径")
    file_size: int = Field(..., description="文件大小(字节)")
    file_type: str = Field(..., description="文件类型")
    user_id: Any = Field(..., description="用户ID")

class ResumeUpdate(BaseModel):
    """更新简历的请求模型"""
    title: Optional[str] = Field(None, description="简历标题", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="简历描述", max_length=500)
    
    model_config = ConfigDict(
        extra="forbid",  # 禁止额外字段
        populate_by_name=True
    )

class ResumeModel(ResumeBase):
    """简历数据模型"""
    id: Optional[PyObjectId] = Field(None, alias="_id", description="简历ID")
    file_name: str = Field(..., description="原始文件名")
    file_path: str = Field(..., description="存储路径")
    file_size: int = Field(..., description="文件大小(字节)")
    file_type: str = Field(..., description="文件类型")
    user_id: Any = Field(..., description="用户ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        },
        json_schema_extra={
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "title": "软件工程师简历",
                "description": "5年经验的全栈开发工程师简历",
                "file_name": "resume.pdf",
                "file_path": "resumes/12345.pdf",
                "file_size": 1024000,
                "file_type": "pdf",
                "user_id": "507f1f77bcf86cd799439012",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }
    )

class ResumeResponse(BaseModel):
    """简历响应模型"""
    id: str = Field(..., description="简历ID")
    title: str = Field(..., description="简历标题")
    description: Optional[str] = Field(None, description="简历描述")
    file_name: str = Field(..., description="原始文件名")
    file_type: str = Field(..., description="文件类型")
    file_size: int = Field(..., description="文件大小(字节)")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "title": "软件工程师简历",
                "description": "5年经验的全栈开发工程师简历",
                "file_name": "resume.pdf",
                "file_type": "pdf",
                "file_size": 1024000,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }
    )
