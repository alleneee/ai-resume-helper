"""
AI简历助手 - Agent模块
提供简历分析、职位爬取、匹配评估和优化建议等功能的智能代理
"""

from .config import (
    JobSearchParams, ResumeAnalysisResult, JobCrawlResult, 
    JobMatchResult, ResumeOptimizationResult
)
from .resume_analyzer_agent import ResumeAnalyzerAgent
from .job_crawler_agent import JobCrawlerAgent
from .coordinator_agent import CoordinatorAgent

__all__ = [
    'ResumeAnalyzerAgent',
    'JobCrawlerAgent',
    'CoordinatorAgent',
    'JobSearchParams',
    'ResumeAnalysisResult',
    'JobCrawlResult',
    'JobMatchResult',
    'ResumeOptimizationResult'
]
