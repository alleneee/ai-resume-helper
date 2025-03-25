"""
用户数据模型
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, ClassVar
from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict
from bson import ObjectId
import bcrypt
from sqlalchemy import Column, String, DateTime, JSON, Boolean, Integer, Enum as SQLAEnum
from sqlalchemy.dialects.postgresql import JSONB

from models.database import Base

# Pydantic模型 - 用于API交互
class PyObjectId(str):
    """自定义ObjectId字段，支持序列化和验证"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("无效的ObjectId")
        return str(ObjectId(v))

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

# 用户角色枚举
class UserRole(str, Enum):
    USER = 'USER'
    PREMIUM = 'PREMIUM'
    ADMIN = 'ADMIN'

# 用户状态枚举
class UserStatus(str, Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    SUSPENDED = 'suspended'

# SQLAlchemy模型 - 用于关系数据库
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    subscription_tier = Column(String, default='free')
    preferences = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """哈希密码"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    async def compare_password(self, candidate_password: str) -> bool:
        """比较密码"""
        return bcrypt.checkpw(
            candidate_password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

# 用户偏好模型
class UserPreferences(BaseModel):
    """用户偏好设置模型"""
    preferredJobTitles: List[str] = Field(default_factory=list, description="首选职位标题")
    preferredLocations: List[str] = Field(default_factory=list, description="首选工作地点")
    preferredIndustries: List[str] = Field(default_factory=list, description="首选行业")
    salaryExpectations: Dict[str, Any] = Field(
        default_factory=lambda: {
            "min": None,
            "max": None,
            "currency": "CNY",
        },
        description="薪资期望"
    )
    notificationSettings: Dict[str, bool] = Field(
        default_factory=lambda: {
            "email": True,
            "browser": True,
            "application": True,
        },
        description="通知设置"
    )

# Pydantic模型 - MongoDB文档
class UserModel(BaseModel):
    """用户数据模型"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    email: EmailStr = Field(..., description="用户邮箱", index=True)
    phone_number: Optional[str] = Field(None, description="用户电话号码")
    password_hash: str = Field(..., description="密码哈希值", exclude=True)
    full_name: str = Field(..., min_length=2, max_length=100, description="用户全名")
    subscription_tier: str = Field(default="free", description="订阅级别")
    preferences: UserPreferences = Field(default_factory=UserPreferences, description="用户偏好设置")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    role: UserRole = Field(default=UserRole.USER, description="用户角色")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="用户状态")
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "_id": "60d21b4967d0d8992e610c85",
                "email": "user@example.com",
                "phone_number": "13800138000",
                "full_name": "张三",
                "subscription_tier": "free",
                "preferences": {
                    "preferredJobTitles": ["软件工程师", "前端开发"],
                    "preferredLocations": ["北京", "上海"],
                    "preferredIndustries": ["科技", "金融"],
                    "salaryExpectations": {
                        "min": 15000,
                        "max": 30000,
                        "currency": "CNY",
                    },
                    "notificationSettings": {
                        "email": True,
                        "browser": True,
                        "application": True,
                    },
                },
                "created_at": "2023-10-01T12:00:00Z",
                "last_login": "2023-10-10T15:30:00Z",
                "role": "USER",
                "status": "active"
            }
        }
    )
    
    @validator('email')
    def email_must_be_valid(cls, v):
        """验证邮箱格式"""
        # EmailStr已经验证了格式，这里可以添加额外的验证逻辑
        if v.endswith('.test'):
            raise ValueError('不允许使用测试域名')
        return v
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """哈希密码"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    async def compare_password(self, candidate_password: str) -> bool:
        """比较密码"""
        return bcrypt.checkpw(
            candidate_password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

# 创建用户请求模型
class UserCreate(BaseModel):
    """用户创建请求模型"""
    email: EmailStr = Field(..., description="用户邮箱")
    phone_number: Optional[str] = Field(None, description="用户电话号码")
    password: str = Field(..., min_length=8, description="用户密码")
    full_name: str = Field(..., min_length=2, max_length=100, description="用户全名")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "email": "user@example.com",
            "phone_number": "13800138000",
            "password": "securepassword123",
            "full_name": "张三"
        }
    })

# 用户登录请求模型
class UserLogin(BaseModel):
    """用户登录请求模型"""
    email: EmailStr = Field(..., description="用户邮箱")
    password: str = Field(..., description="用户密码")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "email": "user@example.com",
            "password": "securepassword123"
        }
    })

# 用户信息响应模型（不包含密码）
class UserResponse(BaseModel):
    """用户信息响应模型"""
    id: str = Field(..., description="用户ID")
    email: str = Field(..., description="用户邮箱")
    phone_number: Optional[str] = Field(None, description="用户电话号码")
    full_name: str = Field(..., description="用户全名")
    subscription_tier: str = Field(..., description="订阅级别")
    preferences: Dict[str, Any] = Field(..., description="用户偏好设置")
    created_at: datetime = Field(..., description="创建时间")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    role: UserRole = Field(..., description="用户角色")
    status: UserStatus = Field(..., description="用户状态")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "60d21b4967d0d8992e610c85",
            "email": "user@example.com",
            "phone_number": "13800138000",
            "full_name": "张三",
            "subscription_tier": "free",
            "preferences": {
                "preferredJobTitles": ["软件工程师", "前端开发"],
                "preferredLocations": ["北京", "上海"],
                "preferredIndustries": ["科技", "金融"],
                "salaryExpectations": {
                    "min": 15000,
                    "max": 30000,
                    "currency": "CNY",
                },
                "notificationSettings": {
                    "email": True,
                    "browser": True,
                    "application": True,
                },
            },
            "created_at": "2023-10-01T12:00:00Z",
            "last_login": "2023-10-10T15:30:00Z",
            "role": "USER",
            "status": "active"
        }
    })
