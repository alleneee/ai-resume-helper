"""
代理相关的数据模型
"""
from pydantic import BaseModel, Field, field_validator, field_serializer, ConfigDict, model_validator
from pydantic.version import VERSION as PYDANTIC_VERSION
from pydantic_core import PydanticCustomError
from typing import Optional, List, Dict, Any, Union, Annotated, Type, TypeVar, Generic, ClassVar
from enum import Enum
from datetime import datetime, date
import re

# 泛型类型变量
T = TypeVar('T')

class JobType(str, Enum):
    """职位类型枚举"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    TEMPORARY = "temporary"
    REMOTE = "remote"
    ANY = "any"
    
    @classmethod
    def get_description(cls, value: str) -> str:
        """获取枚举值的中文描述"""
        descriptions = {
            cls.FULL_TIME.value: "全职",
            cls.PART_TIME.value: "兼职",
            cls.CONTRACT.value: "合同工",
            cls.INTERNSHIP.value: "实习",
            cls.TEMPORARY.value: "临时工",
            cls.REMOTE.value: "远程",
            cls.ANY.value: "任意"
        }
        return descriptions.get(value, value)

class ExperienceLevel(str, Enum):
    """经验水平枚举"""
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"
    ANY = "any"
    
    @classmethod
    def get_description(cls, value: str) -> str:
        """获取枚举值的中文描述"""
        descriptions = {
            cls.ENTRY.value: "入门级",
            cls.JUNIOR.value: "初级",
            cls.MID.value: "中级",
            cls.SENIOR.value: "高级",
            cls.LEAD.value: "团队负责人",
            cls.EXECUTIVE.value: "高管",
            cls.ANY.value: "任意"
        }
        return descriptions.get(value, value)

class EducationLevel(str, Enum):
    """学历水平枚举"""
    HIGH_SCHOOL = "high_school"
    ASSOCIATE = "associate"
    BACHELOR = "bachelor"
    MASTER = "master"
    DOCTORATE = "doctorate"
    ANY = "any"
    
    @classmethod
    def get_description(cls, value: str) -> str:
        """获取枚举值的中文描述"""
        descriptions = {
            cls.HIGH_SCHOOL.value: "高中",
            cls.ASSOCIATE.value: "大专",
            cls.BACHELOR.value: "本科",
            cls.MASTER.value: "硕士",
            cls.DOCTORATE.value: "博士",
            cls.ANY.value: "任意"
        }
        return descriptions.get(value, value)

class CompanySize(str, Enum):
    """公司规模枚举"""
    STARTUP = "startup"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"
    ANY = "any"
    
    @classmethod
    def get_description(cls, value: str) -> str:
        """获取枚举值的中文描述"""
        descriptions = {
            cls.STARTUP.value: "初创公司(<20人)",
            cls.SMALL.value: "小型公司(20-200人)",
            cls.MEDIUM.value: "中型公司(201-1000人)",
            cls.LARGE.value: "大型公司(1001-5000人)",
            cls.ENTERPRISE.value: "企业(>5000人)",
            cls.ANY.value: "任意规模"
        }
        return descriptions.get(value, value)

class FundingStage(str, Enum):
    """融资阶段枚举"""
    BOOTSTRAP = "bootstrap"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    SERIES_C = "series_c"
    SERIES_D_PLUS = "series_d_plus"
    IPO = "ipo"
    ACQUIRED = "acquired"
    ANY = "any"
    
    @classmethod
    def get_description(cls, value: str) -> str:
        """获取枚举值的中文描述"""
        descriptions = {
            cls.BOOTSTRAP.value: "自筹资金",
            cls.SEED.value: "种子轮",
            cls.SERIES_A.value: "A轮",
            cls.SERIES_B.value: "B轮",
            cls.SERIES_C.value: "C轮",
            cls.SERIES_D_PLUS.value: "D轮及以上",
            cls.IPO.value: "已上市",
            cls.ACQUIRED.value: "已被收购",
            cls.ANY.value: "任意阶段"
        }
        return descriptions.get(value, value)

class CoverLetterTone(str, Enum):
    """求职信语调枚举"""
    PROFESSIONAL = "professional"
    ENTHUSIASTIC = "enthusiastic"
    FORMAL = "formal"
    CASUAL = "casual"
    CONFIDENT = "confident"
    
    @classmethod
    def get_description(cls, value: str) -> str:
        """获取枚举值的中文描述"""
        descriptions = {
            cls.PROFESSIONAL.value: "专业",
            cls.ENTHUSIASTIC.value: "热情",
            cls.FORMAL.value: "正式",
            cls.CASUAL.value: "随意",
            cls.CONFIDENT.value: "自信"
        }
        return descriptions.get(value, value)

# 自定义字段类型
ObjectId = Annotated[str, Field(pattern=r'^[0-9a-fA-F]{24}$')]

class BaseAPIModel(BaseModel, Generic[T]):
    """
    基础API模型
    
    所有API模型的基类，提供通用配置和方法
    """
    # 类变量，用于动态文档生成
    title: ClassVar[str] = "基础API模型"
    description: ClassVar[str] = "所有API模型的基类"
    
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        validate_default=True,
        extra="ignore",
        json_schema_extra={
            "title": "基础API模型",
            "description": "所有API模型的基类"
        }
    )
    
    @classmethod
    def get_model_name(cls) -> str:
        """获取模型名称"""
        return cls.__name__
    
    @classmethod
    def get_schema_title(cls) -> str:
        """获取模型文档标题"""
        return getattr(cls, 'title', cls.__name__)
    
    @classmethod
    def get_schema_description(cls) -> str:
        """获取模型文档描述"""
        return getattr(cls, 'description', cls.__doc__ or "")

class ResumeOptimizationRequest(BaseAPIModel):
    """简历优化请求模型"""
    title: ClassVar[str] = "简历优化请求"
    description: ClassVar[str] = "用于请求AI分析和优化简历内容的模型"
    
    resume_id: ObjectId = Field(
        ..., 
        description="简历ID", 
        examples=["507f1f77bcf86cd799439011"]
    )
    job_description: str = Field(
        ..., 
        description="职位描述", 
        min_length=10,
        max_length=5000,
        examples=["我们正在寻找一名有经验的软件工程师，负责设计和实现高性能的Web应用程序..."]
    )
    
    model_config = ConfigDict(
        title="简历优化请求",
        json_schema_extra={
            "example": {
                "resume_id": "507f1f77bcf86cd799439011",
                "job_description": "我们正在寻找一名有经验的软件工程师，负责设计和实现高性能的Web应用程序..."
            }
        }
    )
    
    @field_validator('job_description')
    @classmethod
    def validate_job_description(cls, v: str) -> str:
        """验证职位描述内容"""
        # 检查是否包含有效内容
        if not v.strip():
            raise PydanticCustomError(
                'invalid_job_description',
                '职位描述不能为空'
            )
        
        # 检查是否包含最少的职位相关信息
        if len(v) < 50:
            raise PydanticCustomError(
                'too_short_job_description',
                '职位描述过短，请提供更详细的信息'
            )
            
        return v

class JobMatchRequest(BaseAPIModel):
    """职位匹配请求模型"""
    title: ClassVar[str] = "职位匹配请求"
    description: ClassVar[str] = "用于根据简历内容匹配合适职位的请求模型"
    
    resume_id: ObjectId = Field(
        ..., 
        description="简历ID", 
        examples=["507f1f77bcf86cd799439011"]
    )
    location: Optional[str] = Field(
        None, 
        description="地点", 
        max_length=100, 
        examples=["上海"]
    )
    job_type: Optional[JobType] = Field(
        None, 
        description="职位类型"
    )
    keywords: Optional[List[str]] = Field(
        None, 
        description="关键词", 
        max_items=10
    )
    limit: int = Field(
        10, 
        description="返回结果数量", 
        ge=1, 
        le=50
    )
    
    model_config = ConfigDict(
        title="职位匹配请求",
        json_schema_extra={
            "example": {
                "resume_id": "507f1f77bcf86cd799439011",
                "location": "上海",
                "job_type": "full_time",
                "keywords": ["Python", "FastAPI", "React"],
                "limit": 10
            }
        }
    )
    
    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """验证关键词列表"""
        if v is None:
            return v
            
        # 过滤空字符串
        filtered = [k.strip() for k in v if k.strip()]
        
        if not filtered:
            return None
            
        # 限制每个关键词的长度
        for keyword in filtered:
            if len(keyword) > 50:
                raise PydanticCustomError(
                    'keyword_too_long',
                    f'关键词 "{keyword[:20]}..." 过长，请限制在50个字符以内'
                )
                
        return filtered

class CoverLetterRequest(BaseAPIModel):
    """求职信生成请求模型"""
    title: ClassVar[str] = "求职信生成请求"
    description: ClassVar[str] = "用于生成针对特定职位和公司的个性化求职信的请求模型"
    
    resume_id: ObjectId = Field(
        ..., 
        description="简历ID", 
        examples=["507f1f77bcf86cd799439011"]
    )
    job_description: str = Field(
        ..., 
        description="职位描述", 
        min_length=10,
        max_length=5000,
        examples=["我们正在寻找一名有经验的软件工程师，负责设计和实现高性能的Web应用程序..."]
    )
    company_name: str = Field(
        ..., 
        description="公司名称", 
        max_length=100, 
        examples=["科技有限公司"]
    )
    company_info: Optional[str] = Field(
        None, 
        description="公司信息", 
        max_length=1000, 
        examples=["一家专注于人工智能和机器学习的创新型科技公司"]
    )
    tone: CoverLetterTone = Field(
        CoverLetterTone.PROFESSIONAL, 
        description="语调"
    )
    
    model_config = ConfigDict(
        title="求职信生成请求",
        json_schema_extra={
            "example": {
                "resume_id": "507f1f77bcf86cd799439011",
                "job_description": "我们正在寻找一名有经验的软件工程师，负责设计和实现高性能的Web应用程序...",
                "company_name": "科技有限公司",
                "company_info": "一家专注于人工智能和机器学习的创新型科技公司",
                "tone": "professional"
            }
        }
    )
    
    @field_serializer('tone')
    def serialize_tone(self, tone: CoverLetterTone) -> str:
        """序列化语调枚举"""
        return tone.value

class JobSearchRequest(BaseAPIModel):
    """职位搜索请求模型"""
    title: ClassVar[str] = "职位搜索请求"
    description: ClassVar[str] = "用于按照多种条件筛选和搜索职位的请求模型"
    
    keywords: List[str] = Field(
        ..., 
        description="搜索关键词", 
        min_items=1, 
        max_items=10
    )
    location: Optional[str] = Field(
        None, 
        description="地点", 
        max_length=100
    )
    job_type: Optional[JobType] = Field(
        None, 
        description="职位类型"
    )
    experience_level: Optional[ExperienceLevel] = Field(
        None, 
        description="经验水平"
    )
    education_level: Optional[EducationLevel] = Field(
        None, 
        description="学历要求"
    )
    salary_min: Optional[int] = Field(
        None, 
        description="最低薪资", 
        ge=0
    )
    salary_max: Optional[int] = Field(
        None, 
        description="最高薪资", 
        ge=0
    )
    company_size: Optional[CompanySize] = Field(
        None, 
        description="公司规模"
    )
    funding_stage: Optional[FundingStage] = Field(
        None, 
        description="融资阶段"
    )
    page: int = Field(
        1, 
        description="页码", 
        ge=1
    )
    limit: int = Field(
        10, 
        description="每页数量", 
        ge=1, 
        le=50
    )
    
    model_config = ConfigDict(
        title="职位搜索请求",
        json_schema_extra={
            "example": {
                "keywords": ["Python", "FastAPI", "React"],
                "location": "上海",
                "job_type": "full_time",
                "experience_level": "mid",
                "education_level": "bachelor",
                "salary_min": 20000,
                "salary_max": 40000,
                "company_size": "medium",
                "funding_stage": "series_b",
                "page": 1,
                "limit": 10
            }
        }
    )
    
    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v: List[str]) -> List[str]:
        """验证关键词列表"""
        if not v:
            raise PydanticCustomError(
                'empty_keywords',
                '至少需要提供一个搜索关键词'
            )
        
        # 过滤空字符串
        filtered = [k.strip() for k in v if k.strip()]
        
        if not filtered:
            raise PydanticCustomError(
                'invalid_keywords',
                '搜索关键词不能为空'
            )
        
        # 限制每个关键词的长度
        for keyword in filtered:
            if len(keyword) > 50:
                raise PydanticCustomError(
                    'keyword_too_long',
                    f'关键词 "{keyword[:20]}..." 过长，请限制在50个字符以内'
                )
        
        return filtered
    
    @model_validator(mode='after')
    def validate_salary_range(self) -> 'JobSearchRequest':
        """验证薪资范围"""
        if (self.salary_min is not None and 
            self.salary_max is not None and 
            self.salary_min > self.salary_max):
            raise PydanticCustomError(
                'invalid_salary_range',
                '最低薪资不能高于最高薪资'
            )
        return self

class ResumeOptimizationResult(BaseAPIModel):
    """简历优化结果模型"""
    title: ClassVar[str] = "简历优化结果"
    description: ClassVar[str] = "包含AI优化后的简历内容和改进建议的结果模型"
    
    original_content: str = Field(..., description="原始内容")
    optimized_content: str = Field(..., description="优化后的内容")
    suggestions: List[str] = Field(..., description="改进建议")
    keywords: List[str] = Field(..., description="关键词")
    
    model_config = ConfigDict(
        title="简历优化结果",
        json_schema_extra={
            "example": {
                "original_content": "原始简历内容...",
                "optimized_content": "优化后的简历内容...",
                "suggestions": ["添加更多项目经验", "突出技术技能", "量化成就"],
                "keywords": ["Python", "FastAPI", "React", "项目管理"]
            }
        }
    )

class JobItem(BaseAPIModel):
    """职位项模型"""
    title: ClassVar[str] = "职位项"
    description: ClassVar[str] = "表示单个职位信息的详细数据模型"
    
    id: str = Field(..., description="职位ID")
    title: str = Field(..., description="职位标题")
    company: str = Field(..., description="公司名称")
    location: str = Field(..., description="地点")
    description: str = Field(..., description="职位描述")
    salary: Optional[str] = Field(None, description="薪资范围")
    job_type: Optional[str] = Field(None, description="职位类型")
    experience_level: Optional[str] = Field(None, description="经验要求")
    education_level: Optional[str] = Field(None, description="学历要求")
    company_size: Optional[str] = Field(None, description="公司规模")
    funding_stage: Optional[str] = Field(None, description="融资阶段")
    company_description: Optional[str] = Field(None, description="公司描述")
    url: Optional[str] = Field(
        None, 
        description="职位链接", 
        pattern=r'^https?://'
    )
    posted_date: Optional[str] = Field(None, description="发布日期")
    match_score: Optional[float] = Field(
        None, 
        description="匹配分数", 
        ge=0, 
        le=1
    )
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    model_config = ConfigDict(
        title="职位项",
        json_encoders={
            datetime: lambda v: v.isoformat()
        },
        json_schema_extra={
            "example": {
                "id": "job123",
                "title": "高级Python开发工程师",
                "company": "科技有限公司",
                "location": "上海",
                "description": "负责设计和实现高性能的Web应用程序...",
                "salary": "20k-40k",
                "job_type": "全职",
                "experience_level": "3-5年",
                "education_level": "本科及以上",
                "company_size": "中型公司(201-1000人)",
                "funding_stage": "B轮",
                "company_description": "一家专注于人工智能和机器学习的创新型科技公司...",
                "url": "https://example.com/jobs/123",
                "posted_date": "2023-05-15",
                "match_score": 0.85
            }
        }
    )
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """验证URL格式"""
        if v is None:
            return v
            
        if not v.startswith(('http://', 'https://')):
            raise PydanticCustomError(
                'invalid_url',
                'URL必须以http://或https://开头'
            )
            
        return v

class JobSearchResult(BaseAPIModel):
    """职位搜索结果模型"""
    title: ClassVar[str] = "职位搜索结果"
    description: ClassVar[str] = "包含职位列表和分页信息的搜索结果模型"
    
    jobs: List[JobItem] = Field(..., description="职位列表")
    total: int = Field(..., description="总数", ge=0)
    page: int = Field(..., description="当前页码", ge=1)
    limit: int = Field(..., description="每页数量", ge=1, le=50)
    
    model_config = ConfigDict(
        title="职位搜索结果",
        json_schema_extra={
            "example": {
                "jobs": [
                    {
                        "id": "job123",
                        "title": "高级Python开发工程师",
                        "company": "科技有限公司",
                        "location": "上海",
                        "description": "负责设计和实现高性能的Web应用程序...",
                        "salary": "20k-40k",
                        "job_type": "全职",
                        "experience_level": "3-5年",
                        "education_level": "本科及以上",
                        "company_size": "中型公司(201-1000人)",
                        "funding_stage": "B轮",
                        "company_description": "一家专注于人工智能和机器学习的创新型科技公司...",
                        "url": "https://example.com/jobs/123",
                        "posted_date": "2023-05-15",
                        "match_score": 0.85
                    }
                ],
                "total": 100,
                "page": 1,
                "limit": 10
            }
        }
    )
    
    @property
    def total_pages(self) -> int:
        """计算总页数"""
        return (self.total + self.limit - 1) // self.limit if self.limit > 0 else 0

class CoverLetterResult(BaseAPIModel):
    """求职信生成结果模型"""
    title: ClassVar[str] = "求职信生成结果"
    description: ClassVar[str] = "包含生成的求职信内容的结果模型"
    
    content: str = Field(..., description="求职信内容")
    
    model_config = ConfigDict(
        title="求职信生成结果",
        json_schema_extra={
            "example": {
                "content": "尊敬的招聘经理：\n\n我怀着极大的热情申请贵公司的高级Python开发工程师职位..."
            }
        }
    )

class AgentResponse(BaseAPIModel, Generic[T]):
    """代理响应模型"""
    title: ClassVar[str] = "代理响应"
    description: ClassVar[str] = "智能代理通用响应模型，包含操作结果状态、消息和数据"
    
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    data: Union[
        ResumeOptimizationResult, 
        JobSearchResult, 
        CoverLetterResult, 
        Dict[str, Any]
    ] = Field(..., description="响应数据")
    
    model_config = ConfigDict(
        title="代理响应",
        json_schema_extra={
            "example": {
                "success": True,
                "message": "操作成功",
                "data": {
                    "original_content": "原始简历内容...",
                    "optimized_content": "优化后的简历内容...",
                    "suggestions": ["添加更多项目经验", "突出技术技能", "量化成就"],
                    "keywords": ["Python", "FastAPI", "React", "项目管理"]
                }
            }
        }
    )
    
    @classmethod
    def create_response(
        cls, 
        success: bool, 
        message: str, 
        data: T
    ) -> 'AgentResponse[T]':
        """
        创建AgentResponse实例
        
        Args:
            success: 操作是否成功
            message: 响应消息
            data: 响应数据
            
        Returns:
            AgentResponse实例
        """
        return cls(success=success, message=message, data=data)
    
    @classmethod
    def success_response(
        cls, 
        message: str = "操作成功", 
        data: T = None
    ) -> 'AgentResponse[T]':
        """
        创建成功响应
        
        Args:
            message: 成功消息
            data: 响应数据
            
        Returns:
            成功的AgentResponse实例
        """
        return cls(success=True, message=message, data=data)
    
    @classmethod
    def error_response(
        cls, 
        message: str = "操作失败", 
        data: Optional[Dict[str, Any]] = None
    ) -> 'AgentResponse[Dict[str, Any]]':
        """
        创建错误响应
        
        Args:
            message: 错误消息
            data: 错误详情数据
            
        Returns:
            错误的AgentResponse实例
        """
        return cls(success=False, message=message, data=data or {})


# 定义JobSearchInput类
class JobSearchInput(BaseAPIModel):
    """职位搜索输入参数模型"""
    title: ClassVar[str] = "职位搜索输入"
    description: ClassVar[str] = "用于智能代理搜索职位的输入参数模型"
    
    keywords: List[str] = Field(..., description="搜索关键词列表")
    location: Optional[str] = Field(None, description="工作地点")
    job_type: Optional[str] = Field(None, description="工作类型，如全职、兼职等")
    experience_level: Optional[str] = Field(None, description="经验要求")
    education_level: Optional[str] = Field(None, description="学历要求")
    salary_min: Optional[int] = Field(None, description="最低薪资")
    salary_max: Optional[int] = Field(None, description="最高薪资")
    company_size: Optional[str] = Field(None, description="公司规模")
    funding_stage: Optional[str] = Field(None, description="融资阶段")
    page: int = Field(1, description="页码")
    limit: int = Field(10, description="每页结果数量")
    
    model_config = ConfigDict(
        title="职位搜索输入",
        json_schema_extra={
            "example": {
                "keywords": ["Python", "FastAPI", "React"],
                "location": "上海",
                "job_type": "full_time",
                "experience_level": "mid",
                "education_level": "bachelor",
                "salary_min": 20000,
                "salary_max": 40000,
                "company_size": "medium",
                "funding_stage": "series_b",
                "page": 1,
                "limit": 10
            }
        }
    )

# 定义JobSearchOutput类
class JobSearchOutput(BaseAPIModel):
    """职位搜索结果模型"""
    title: ClassVar[str] = "职位搜索结果"
    description: ClassVar[str] = "智能代理搜索职位的输出结果模型"
    
    jobs: List[Dict[str, Any]] = Field(..., description="搜索到的职位列表")
    total: int = Field(..., description="结果总数")
    page: int = Field(..., description="当前页码")
    limit: int = Field(..., description="每页数量")
    
    model_config = ConfigDict(
        title="职位搜索结果",
        json_schema_extra={
            "example": {
                "jobs": [
                    {
                        "id": "job123",
                        "title": "高级Python开发工程师",
                        "company": "科技有限公司",
                        "location": "上海",
                        "description": "负责设计和实现高性能的Web应用程序...",
                        "salary": "20k-40k",
                        "job_type": "全职",
                        "experience_level": "3-5年",
                        "education_level": "本科及以上"
                    }
                ],
                "total": 100,
                "page": 1,
                "limit": 10
            }
        }
    )

# 定义JobMatchInput类
class JobMatchInput(BaseAPIModel):
    """职位匹配输入参数模型"""
    title: ClassVar[str] = "职位匹配输入"
    description: ClassVar[str] = "用于智能代理匹配简历和职位的输入参数模型"
    
    resume_content: str = Field(..., description="简历内容")
    job_requirements: str = Field(..., description="职位要求描述")
    
    model_config = ConfigDict(
        title="职位匹配输入",
        json_schema_extra={
            "example": {
                "resume_content": "简历内容...",
                "job_requirements": "职位要求描述..."
            }
        }
    )

# 定义ResumeOptimizationInput类
class ResumeOptimizationInput(BaseAPIModel):
    """简历优化输入参数模型"""
    title: ClassVar[str] = "简历优化输入"
    description: ClassVar[str] = "用于智能代理优化简历的输入参数模型"
    
    resume_content: str = Field(..., description="原始简历内容")
    job_description: str = Field(..., description="目标职位描述")
    focus_areas: Optional[List[str]] = Field(None, description="需要重点关注的领域或技能")
    job_analysis: Optional[Dict[str, Any]] = Field(None, description="职位分析结果，包含共同要求、关键技能等")
    
    model_config = ConfigDict(
        title="简历优化输入",
        json_schema_extra={
            "example": {
                "resume_content": "简历内容...",
                "job_description": "职位描述...",
                "focus_areas": ["Python", "FastAPI", "React"],
                "job_analysis": {
                    "common_requirements": ["精通前端开发", "熟悉React框架"],
                    "key_skills": {"Python": 10, "FastAPI": 8, "React": 12}
                }
            }
        }
    )

# 定义JobAnalysisInput类
class JobAnalysisInput(BaseAPIModel):
    """职位分析输入参数模型"""
    title: ClassVar[str] = "职位分析输入"
    description: ClassVar[str] = "用于智能代理分析职位的输入参数模型"
    
    jobs: List[Dict[str, Any]] = Field(..., description="职位列表")
    analysis_focus: Optional[List[str]] = Field(None, description="分析重点，如'技能要求'、'经验要求'等")
    
    model_config = ConfigDict(
        title="职位分析输入",
        json_schema_extra={
            "example": {
                "jobs": [
                    {
                        "id": "job123",
                        "title": "高级Python开发工程师",
                        "company": "科技有限公司",
                        "location": "上海",
                        "description": "负责设计和实现高性能的Web应用程序...",
                        "requirements": "精通Python和FastAPI，熟悉React框架..."
                    }
                ],
                "analysis_focus": ["技能要求", "经验要求"]
            }
        }
    )

# 定义JobAnalysisOutput类
class JobAnalysisOutput(BaseAPIModel):
    """职位分析结果模型"""
    title: ClassVar[str] = "职位分析结果"
    description: ClassVar[str] = "智能代理分析职位的输出结果模型"
    
    common_requirements: List[str] = Field(..., description="共同职位要求")
    key_skills: Dict[str, int] = Field(..., description="关键技能及其频率")
    experience_requirements: Dict[str, int] = Field(..., description="经验要求统计")
    education_requirements: Dict[str, int] = Field(..., description="学历要求统计")
    salary_range: Dict[str, Any] = Field(..., description="薪资范围分析")
    report_summary: str = Field(..., description="岗位需求报告摘要")
    
    model_config = ConfigDict(
        title="职位分析结果",
        json_schema_extra={
            "example": {
                "common_requirements": ["精通Python", "熟悉Web开发"],
                "key_skills": {"Python": 10, "FastAPI": 8, "React": 12},
                "experience_requirements": {"3-5年": 15, "5年以上": 5},
                "education_requirements": {"本科": 10, "硕士": 10},
                "salary_range": {"min": 20000, "max": 40000, "average": 30000},
                "report_summary": "大多数职位要求精通Python和Web开发，并且要求3-5年的相关经验..."
            }
        }
    )

# 定义ResumeOptimizationOutput类
class ResumeOptimizationOutput(BaseAPIModel):
    """简历优化结果模型"""
    title: ClassVar[str] = "简历优化结果"
    description: ClassVar[str] = "智能代理优化简历的输出结果模型"
    
    optimized_content: str = Field(..., description="优化后的简历内容")
    suggestions: List[str] = Field(..., description="改进建议")
    matched_skills: Optional[List[str]] = Field(None, description="与职位匹配的技能")
    missing_skills: Optional[List[str]] = Field(None, description="缺失的技能")
    
    model_config = ConfigDict(
        title="简历优化结果",
        json_schema_extra={
            "example": {
                "optimized_content": "优化后的简历内容...",
                "suggestions": ["增加项目经验描述", "突出技术技能"],
                "matched_skills": ["Python", "FastAPI", "React"],
                "missing_skills": ["Docker", "Kubernetes"]
            }
        }
    )

# 定义JobMatchOutput类
class JobMatchOutput(BaseAPIModel):
    """职位匹配结果模型"""
    title: ClassVar[str] = "职位匹配结果"
    description: ClassVar[str] = "智能代理匹配简历和职位的输出结果模型"
    
    match_score: float = Field(..., description="匹配分数，0-1之间")
    matching_skills: List[str] = Field(..., description="匹配的技能列表")
    missing_skills: List[str] = Field(..., description="缺失的技能列表")
    recommendations: List[str] = Field(..., description="求职建议列表")
    
    model_config = ConfigDict(
        title="职位匹配结果",
        json_schema_extra={
            "example": {
                "match_score": 0.85,
                "matching_skills": ["Python", "FastAPI", "React"],
                "missing_skills": ["Docker", "Kubernetes"],
                "recommendations": ["增加Docker经验", "学习Kubernetes"]
            }
        }
    )

# 定义JobMatchResponse类
class JobMatchResponse(BaseAPIModel):
    """职位匹配响应模型"""
    title: ClassVar[str] = "职位匹配响应"
    description: ClassVar[str] = "包含职位匹配结果的响应模型"
    
    resume_id: ObjectId = Field(..., description="简历ID")
    job_id: str = Field(..., description="职位ID")
    match_score: float = Field(..., description="匹配分数，0-1之间")
    matching_skills: List[str] = Field(..., description="匹配的技能列表")
    missing_skills: List[str] = Field(..., description="缺失的技能列表")
    recommendations: List[str] = Field(..., description="求职建议列表")
    
    model_config = ConfigDict(
        title="职位匹配响应",
        json_schema_extra={
            "example": {
                "resume_id": "507f1f77bcf86cd799439011",
                "job_id": "job123",
                "match_score": 0.85,
                "matching_skills": ["Python", "FastAPI", "React"],
                "missing_skills": ["Docker", "Kubernetes"],
                "recommendations": ["增加Docker经验", "学习Kubernetes"]
            }
        }
    )

# 为兼容性提供别名
JobSearchResponse = JobSearchResult

class JobDetail(BaseAPIModel):
    """职位详情模型"""
    title: ClassVar[str] = "职位详情"
    description: ClassVar[str] = "表示单个职位的详细信息模型"
    
    id: str = Field(..., description="职位ID")
    title: Optional[str] = Field(None, description="职位标题")
    company_name: Optional[str] = Field(None, description="公司名称")
    location: Optional[str] = Field(None, description="工作地点")
    salary_range: Optional[str] = Field(None, description="薪资范围")
    job_type: Optional[str] = Field(None, description="工作类型")
    experience_level: Optional[str] = Field(None, description="经验要求")
    education_level: Optional[str] = Field(None, description="学历要求")
    company_size: Optional[str] = Field(None, description="公司规模")
    funding_stage: Optional[str] = Field(None, description="融资阶段")
    company_description: Optional[str] = Field(None, description="公司描述")
    job_description: Optional[str] = Field(None, description="职位描述")
    responsibilities: Optional[List[str]] = Field(None, description="工作职责")
    requirements: Optional[List[str]] = Field(None, description="岗位要求")
    benefits: Optional[List[str]] = Field(None, description="福利待遇")
    url: Optional[str] = Field(
        None, 
        description="职位链接", 
        pattern=r'^https?://'
    )
    posted_date: Optional[str] = Field(None, description="发布日期")
    
    model_config = ConfigDict(
        title="职位详情",
        json_encoders={
            datetime: lambda v: v.isoformat()
        },
        json_schema_extra={
            "example": {
                "id": "job123",
                "title": "高级Python开发工程师",
                "company_name": "科技有限公司",
                "location": "上海",
                "salary_range": "20k-40k",
                "job_type": "全职",
                "experience_level": "3-5年",
                "education_level": "本科及以上",
                "company_size": "中型公司(201-1000人)",
                "funding_stage": "B轮",
                "company_description": "一家专注于人工智能和机器学习的创新型科技公司...",
                "job_description": "负责设计和实现高性能的Web应用程序...",
                "responsibilities": [
                    "设计和开发高可扩展的Web应用",
                    "优化系统性能",
                    "参与代码审查和技术决策"
                ],
                "requirements": [
                    "熟练掌握Python编程",
                    "熟悉FastAPI、Django或Flask框架",
                    "具有良好的算法和数据结构基础"
                ],
                "benefits": [
                    "有竞争力的薪资",
                    "五险一金",
                    "弹性工作制",
                    "定期技术培训"
                ],
                "url": "https://example.com/jobs/123",
                "posted_date": "2023-05-15"
            }
        }
    )
    
    @field_validator('url')
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """验证URL格式"""
        if v is None:
            return v
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL必须以http://或https://开头")
        return v
