from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import List, Optional, Dict, Any
import uuid

class JobSearchCriteria(BaseModel):
    """职位搜索条件模型"""
    keywords: List[str] = Field(..., description="搜索关键词列表")
    location: Optional[str] = Field(None, description="工作地点")
    limit: int = Field(description="返回的最大职位数量")
    other_filters: Optional[Dict[str, Any]] = Field(None, description="其他特定平台的筛选条件，例如经验、学历等")
    target_site_url: Optional[str] = Field(None, description="目标网站URL")
    target_site_name: Optional[str] = Field(None, description="目标网站名称")

class JobPosting(BaseModel):
    """职位信息模型"""
    id: str = Field(description="职位唯一ID")
    title: str = Field(..., description="职位名称")
    company_name: str = Field(..., description="公司名称")
    location: str = Field(..., description="工作地点")
    description: str = Field(..., description="职位描述")
    url: Optional[str] = Field(None, description="职位详情页URL")
    salary_range: Optional[str] = Field(None, description="薪资范围")
    experience_level: Optional[str] = Field(None, description="经验要求")
    education_level: Optional[str] = Field(None, description="学历要求")
    job_type: Optional[str] = Field(None, description="工作类型, e.g., 全职, 兼职")
    posted_date: Optional[str] = Field(None, description="发布日期")
    company_size: Optional[str] = Field(None, description="公司规模")
    industry: Optional[str] = Field(None, description="所属行业")
    # 可以根据需要添加更多字段

class ResumeData(BaseModel):
    """用户简历数据模型"""
    raw_text: Optional[str] = Field(None, description="简历原始文本")
    structured_data: Optional[Dict[str, Any]] = Field(None, description="结构化的简历数据，例如从JSON或数据库加载")
    file_path: Optional[str] = Field(None, description="原始简历文件路径 (如果适用)")

    # Pydantic v2 推荐使用 root_validator 或 model_validator 来进行跨字段验证
    # 这里我们简化，假设调用者会保证至少提供一个来源
    # 如果需要严格校验，可以使用 @model_validator(mode='before')
    # @classmethod
    # def check_at_least_one_source(cls, values):
    #     if not values.get('raw_text') and not values.get('structured_data'):
    #         raise ValueError("至少需要提供 raw_text 或 structured_data")
    #     return values

class AnalysisResult(BaseModel):
    """简历与职位匹配度分析结果模型"""
    match_score: float = Field(..., description="简历与目标职位的匹配度得分 (0.0 - 1.0)")
    strengths: List[str] = Field(description="简历匹配的优势点")
    weaknesses: List[str] = Field(description="简历存在的劣势或可改进点")
    suggestions: List[str] = Field(description="具体的简历修改建议")
    analyzed_jobs_count: int = Field(description="本次分析基于的职位数量")

class OptimizedResume(BaseModel):
    """优化后的简历模型"""
    optimized_text: str = Field(..., description="优化后的简历文本")
    original_resume: ResumeData = Field(..., description="用于优化的原始简历数据")
    analysis_summary: Optional[AnalysisResult] = Field(None, description="本次优化所依据的分析结果摘要")

# 可以根据需要添加更多模型，例如用于工具输入/输出的特定模型
class BrowserActionResult(BaseModel):
    """浏览器工具操作结果模型"""
    success: bool = Field(..., description="操作是否成功")
    extracted_content: Optional[Any] = Field(None, description="提取到的内容或操作结果")
    error_message: Optional[str] = Field(None, description="如果操作失败，返回错误信息")

# 新增：用于 browser-use 的输出模型
class JobPostingList(BaseModel):
    jobs: List[JobPosting] = Field(default_factory=list, description="List of job postings found")

# 从 test_agent.py 移动过来的模型
class Post(BaseModel):
	post_title: str
	post_url: str
	num_comments: int
	hours_since_post: int

class Posts(BaseModel):
	posts: List[Post]
