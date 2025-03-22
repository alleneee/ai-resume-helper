"""
Agent通用配置 - 统一环境变量、API密钥和常量定义
"""
import os
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# API密钥
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

# OpenAI配置
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
DEFAULT_AGENT_TEMPERATURE = 0.2

# Boss直聘参数映射
BOSS_EXPERIENCE_MAP = {
    "应届": "108",
    "0-1年": "102",
    "1-3年": "103",
    "3-5年": "104",
    "5-10年": "105",
    "10年以上": "106"
}

BOSS_EDUCATION_MAP = {
    "初中及以下": "205",
    "中专/中技": "206",
    "高中": "207",
    "大专": "208",
    "本科": "209",
    "硕士": "210",
    "博士": "211"
}

BOSS_SALARY_MAP = {
    "0-5k": "401",
    "5k-10k": "402",
    "10k-15k": "403",
    "15k-20k": "404",
    "20k-30k": "405",
    "30k-50k": "406",
    "50k以上": "407"
}

BOSS_JOB_TYPE_MAP = {
    "全职": "801",
    "兼职": "802",
    "实习": "803"
}

# 目录配置
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

# 创建所需目录
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 数据模型
class JobSearchParams(BaseModel):
    """职位搜索参数"""
    keywords: List[str]
    locations: Optional[List[str]] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    salary_range: Optional[str] = None
    job_type: Optional[str] = None

class JobCrawlResult(BaseModel):
    """职位爬取结果"""
    total_jobs: int
    top_skills: List[str]
    salary_range: Dict[str, Any]
    common_requirements: List[str]

class ResumeAnalysisResult(BaseModel):
    """简历分析结果"""
    core_skills: List[str]
    experience_summary: str
    strengths: List[Dict[str, str]]
    improvements: List[Dict[str, str]]
    keywords: List[str]
    score: Optional[Dict[str, Any]] = None

class JobMatchResult(BaseModel):
    """职位匹配结果"""
    match_score: float
    matching_skills: List[str]
    missing_skills: List[str]
    recommendations: List[str]
    
class ResumeOptimizationResult(BaseModel):
    """简历优化结果"""
    improved_sections: Dict[str, str]
    added_keywords: List[str]
    suggestions: List[str]
    before_after: Dict[str, Dict[str, str]]

# 智能体配置
MAX_AGENT_TOKENS = int(os.environ.get("MAX_AGENT_TOKENS", "4000"))

# 数据库配置
DB_CONNECTION_STRING = os.environ.get("DB_CONNECTION_STRING", "mongodb://localhost:27017/resume_helper")
DB_NAME = os.environ.get("DB_NAME", "resume_helper")

# 应用配置
DEBUG_MODE = os.environ.get("DEBUG_MODE", "False").lower() in ("true", "1", "t")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# 上传文件配置
ALLOWED_FILE_EXTENSIONS = os.environ.get("ALLOWED_FILE_EXTENSIONS", "pdf,docx,doc,txt").split(",")
MAX_UPLOAD_SIZE_MB = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "10"))

# 共享上下文
class SharedContext:
    """智能体之间共享的上下文数据"""
    def __init__(self):
        self.resume_analysis: Optional[ResumeAnalysisResult] = None
        self.job_market_data: Optional[JobCrawlResult] = None
        self.optimization_suggestions: Optional[ResumeOptimizationResult] = None
        
    def reset(self):
        """重置上下文"""
        self.resume_analysis = None
        self.job_market_data = None
        self.optimization_suggestions = None 