from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class SuggestionType(str, Enum):
    """建议类型枚举"""
    CONTENT = "content"         # 内容优化
    FORMAT = "format"           # 格式优化
    GRAMMAR = "grammar"         # 语法修正
    KEYWORD = "keyword"         # 关键词优化
    QUANTIFICATION = "quantification"  # 成就量化
    REDUNDANCY = "redundancy"   # 冗余内容


class ContentSuggestion(BaseModel):
    """内容优化建议"""
    type: SuggestionType
    section: str  # 如 "experience", "education", "skills"
    path: Optional[List[int]] = None  # 在文档中的位置索引
    original: Optional[str] = None  # 原始内容
    suggested: str  # 建议内容
    reason: str  # 建议理由


class KeywordAnalysis(BaseModel):
    """关键词分析"""
    detected: List[str]  # 检测到的关键词
    missing: List[str]  # 建议添加的关键词
    density: float  # 关键词密度


class QualityScores(BaseModel):
    """质量评分"""
    completeness: int = Field(..., ge=0, le=100)  # 完整性
    impact: int = Field(..., ge=0, le=100)        # 影响力
    relevance: int = Field(..., ge=0, le=100)     # 相关性
    clarity: int = Field(..., ge=0, le=100)       # 清晰度
    ats_compatibility: int = Field(..., ge=0, le=100)  # ATS兼容性


class ATSCompatibility(BaseModel):
    """ATS兼容性分析"""
    score: int = Field(..., ge=0, le=100)
    issues: List[str] = []
    formatting_issues: List[str] = []
    content_issues: List[str] = []
    recommendations: List[str] = []


class ResumeAnalysis(BaseModel):
    """简历分析结果"""
    resume_id: str
    overall_score: int = Field(..., ge=0, le=100)
    quality_scores: QualityScores
    content_suggestions: List[ContentSuggestion] = []
    keyword_analysis: KeywordAnalysis
    ats_compatibility: ATSCompatibility
    created_at: datetime = Field(default_factory=datetime.now)


class JobSpecificMatch(BaseModel):
    """职位匹配分析"""
    job_title: str
    match_score: int = Field(..., ge=0, le=100)
    missing_keywords: List[str] = []
    skill_gaps: List[str] = []
    strengths: List[str] = []
    content_suggestions: List[ContentSuggestion] = []
    section_recommendations: Dict[str, List[str]] = {}


class AnalysisRequest(BaseModel):
    """分析请求模型"""
    resume_id: str
    job_description: Optional[str] = None  # 如果提供，将进行针对性分析


class IndustryMetadata(BaseModel):
    """行业元数据"""
    industry: List[str] = []
    job_level: Optional[str] = None
    job_functions: List[str] = []
    key_skills: List[str] = []
    years_of_experience: Optional[int] = None 