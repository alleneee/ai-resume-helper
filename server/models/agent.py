"""
代理相关的数据模型
"""
from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List, Dict, Any, Union
from enum import Enum

class JobType(str, Enum):
    """职位类型枚举"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    TEMPORARY = "temporary"
    REMOTE = "remote"
    ANY = "any"

class ExperienceLevel(str, Enum):
    """经验水平枚举"""
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"
    ANY = "any"

class CoverLetterTone(str, Enum):
    """求职信语调枚举"""
    PROFESSIONAL = "professional"
    ENTHUSIASTIC = "enthusiastic"
    FORMAL = "formal"
    CASUAL = "casual"
    CONFIDENT = "confident"

class ResumeOptimizationRequest(BaseModel):
    """简历优化请求模型"""
    resume_id: str = Field(..., description="简历ID")
    job_description: str = Field(..., description="职位描述", min_length=10)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "resume_id": "507f1f77bcf86cd799439011",
                "job_description": "我们正在寻找一名有经验的软件工程师，负责设计和实现高性能的Web应用程序..."
            }
        }
    )

class JobMatchRequest(BaseModel):
    """职位匹配请求模型"""
    resume_id: str = Field(..., description="简历ID")
    location: Optional[str] = Field(None, description="地点")
    job_type: Optional[JobType] = Field(None, description="职位类型")
    keywords: Optional[List[str]] = Field(None, description="关键词")
    limit: Optional[int] = Field(10, description="返回结果数量", ge=1, le=50)
    
    model_config = ConfigDict(
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

class CoverLetterRequest(BaseModel):
    """求职信生成请求模型"""
    resume_id: str = Field(..., description="简历ID")
    job_description: str = Field(..., description="职位描述", min_length=10)
    company_name: str = Field(..., description="公司名称")
    company_info: Optional[str] = Field(None, description="公司信息")
    tone: Optional[CoverLetterTone] = Field(CoverLetterTone.PROFESSIONAL, description="语调")
    
    model_config = ConfigDict(
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

class JobSearchRequest(BaseModel):
    """职位搜索请求模型"""
    keywords: List[str] = Field(..., description="搜索关键词", min_items=1)
    location: Optional[str] = Field(None, description="地点")
    job_type: Optional[JobType] = Field(None, description="职位类型")
    experience_level: Optional[ExperienceLevel] = Field(None, description="经验水平")
    salary_min: Optional[int] = Field(None, description="最低薪资")
    salary_max: Optional[int] = Field(None, description="最高薪资")
    page: Optional[int] = Field(1, description="页码", ge=1)
    limit: Optional[int] = Field(10, description="每页数量", ge=1, le=50)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "keywords": ["Python", "FastAPI", "React"],
                "location": "上海",
                "job_type": "full_time",
                "experience_level": "mid",
                "salary_min": 20000,
                "salary_max": 40000,
                "page": 1,
                "limit": 10
            }
        }
    )

class ResumeOptimizationResult(BaseModel):
    """简历优化结果模型"""
    original_content: str = Field(..., description="原始内容")
    optimized_content: str = Field(..., description="优化后的内容")
    suggestions: List[str] = Field(..., description="改进建议")
    keywords: List[str] = Field(..., description="关键词")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "original_content": "原始简历内容...",
                "optimized_content": "优化后的简历内容...",
                "suggestions": ["添加更多项目经验", "突出技术技能", "量化成就"],
                "keywords": ["Python", "FastAPI", "React", "项目管理"]
            }
        }
    )

class JobItem(BaseModel):
    """职位项模型"""
    id: str = Field(..., description="职位ID")
    title: str = Field(..., description="职位标题")
    company: str = Field(..., description="公司名称")
    location: str = Field(..., description="地点")
    description: str = Field(..., description="职位描述")
    salary: Optional[str] = Field(None, description="薪资范围")
    job_type: Optional[str] = Field(None, description="职位类型")
    url: Optional[str] = Field(None, description="职位链接")
    posted_date: Optional[str] = Field(None, description="发布日期")
    match_score: Optional[float] = Field(None, description="匹配分数")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "job123",
                "title": "高级Python开发工程师",
                "company": "科技有限公司",
                "location": "上海",
                "description": "负责设计和实现高性能的Web应用程序...",
                "salary": "20k-40k",
                "job_type": "全职",
                "url": "https://example.com/jobs/123",
                "posted_date": "2023-05-15",
                "match_score": 0.85
            }
        }
    )

class JobSearchResult(BaseModel):
    """职位搜索结果模型"""
    jobs: List[JobItem] = Field(..., description="职位列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    limit: int = Field(..., description="每页数量")
    
    model_config = ConfigDict(
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

class CoverLetterResult(BaseModel):
    """求职信生成结果模型"""
    content: str = Field(..., description="求职信内容")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "尊敬的招聘经理：\n\n我怀着极大的热情申请贵公司的高级Python开发工程师职位..."
            }
        }
    )

class AgentResponse(BaseModel):
    """代理响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    data: Union[
        ResumeOptimizationResult, 
        JobSearchResult, 
        CoverLetterResult, 
        Dict[str, Any]
    ] = Field(..., description="响应数据")
    
    model_config = ConfigDict(
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
