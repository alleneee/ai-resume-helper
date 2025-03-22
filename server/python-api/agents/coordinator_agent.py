"""
协调Agent - 用于管理整体AI简历助手流程，调度其他Agent完成任务
"""
import json
import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI
from openai_agents.agent import Agent

from .config import (
    OPENAI_API_KEY, OPENAI_MODEL, DEFAULT_AGENT_TEMPERATURE
)
from .resume_analyzer_agent import ResumeAnalyzerAgent
from .job_crawler_agent import JobCrawlerAgent
from .config import (
    JobSearchParams, ResumeAnalysisResult, JobCrawlResult, JobMatchResult,
    ResumeOptimizationResult
)

logger = logging.getLogger(__name__)

class CoordinatorAgent(Agent):
    """
    协调Agent - 负责整体AI简历助手流程，协调简历分析、职位搜索和优化建议
    """
    
    def __init__(self, api_key: str = None, model: str = None):
        """初始化协调Agent"""
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or OPENAI_MODEL
        
        # 初始化子Agent
        self.resume_analyzer = ResumeAnalyzerAgent(api_key=self.api_key, model=self.model)
        self.job_crawler = JobCrawlerAgent(api_key=self.api_key, model=self.model)
        
        super().__init__(
            name="简历助手协调员",
            handoff_description="AI简历助手的主协调者，管理整体优化流程",
            instructions=self._get_agent_instructions(),
            model=self.model,
        )
    
    def _get_agent_instructions(self) -> str:
        """获取Agent指令"""
        return """你是AI简历助手的主协调员，负责管理用户的整体简历优化和职位申请流程。

你的主要职责包括：
1. 理解用户的需求，确定是简历分析、职位搜索、匹配评估还是简历优化
2. 协调调用适当的专家Agent完成相应任务
3. 整合各Agent的结果，提供连贯一致的用户体验
4. 维护用户的上下文状态，确保对话的连续性
5. 提供清晰的引导和解释，帮助用户理解流程

你可以协调以下几种专家Agent：
- 简历分析专家：负责分析用户简历，识别核心技能和改进点
- 职位爬取专家：负责搜索和分析职位数据，提供市场洞察
- 匹配评估专家：评估简历与特定职位的匹配度
- 简历优化专家：提供具体的简历改进建议

确保整个流程顺畅、专业且为用户提供真正有价值的帮助。
"""

    async def process_resume(self, resume_text: str) -> ResumeAnalysisResult:
        """
        处理用户简历
        
        Args:
            resume_text: 简历文本内容
            
        Returns:
            ResumeAnalysisResult: 简历分析结果
        """
        try:
            # 调用简历分析Agent
            logger.info("开始分析用户简历")
            analysis_result = await self.resume_analyzer.analyze_resume(resume_text)
            logger.info("简历分析完成")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"简历处理失败: {str(e)}")
            # 发生错误时返回基本结果
            return ResumeAnalysisResult(
                core_skills=["处理出错"],
                experience_summary="无法处理简历内容",
                strengths=[{"title": "错误", "description": f"处理过程中出错: {str(e)}"}],
                improvements=[{"area": "格式", "suggestion": "请重新提交有效的简历文档"}],
                keywords=[]
            )
    
    async def search_jobs(self, search_params: JobSearchParams) -> JobCrawlResult:
        """
        搜索职位
        
        Args:
            search_params: 职位搜索参数
            
        Returns:
            JobCrawlResult: 职位爬取分析结果
        """
        try:
            # 调用职位爬取Agent
            logger.info(f"开始搜索职位: {search_params}")
            crawl_result = await self.job_crawler.crawl_jobs(search_params)
            logger.info("职位搜索完成")
            
            return crawl_result
            
        except Exception as e:
            logger.error(f"职位搜索失败: {str(e)}")
            # 发生错误时返回基本结果
            return JobCrawlResult(
                total_jobs=0,
                top_skills=[],
                salary_range={"error": str(e)},
                common_requirements=[]
            )
    
    async def match_resume_with_job(self, resume_text: str, job_description: str) -> JobMatchResult:
        """
        评估简历与职位的匹配度
        
        Args:
            resume_text: 简历文本内容
            job_description: 职位描述
            
        Returns:
            JobMatchResult: 职位匹配结果
        """
        try:
            # 先分析简历
            resume_analysis = await self.resume_analyzer.analyze_resume(resume_text, job_description)
            
            # 使用OpenAI评估匹配度
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": """你是一个专业的简历匹配专家。请分析提供的简历和职位描述，评估它们的匹配程度，并返回JSON格式的分析结果，包含以下字段：
                    - match_score: 匹配分数(0-100之间的数字)
                    - matching_skills: 匹配的技能列表(字符串数组)
                    - missing_skills: 缺失的关键技能(字符串数组)
                    - recommendations: 改进建议列表(字符串数组)
                    
                    确保返回的是有效的JSON格式，不要包含任何其他文本。
                    """},
                    {"role": "user", "content": f"简历内容:\n{resume_text}\n\n职位描述:\n{job_description}"}
                ],
                temperature=DEFAULT_AGENT_TEMPERATURE,
                response_format={"type": "json_object"}
            )
            
            # 解析JSON响应
            result_json = response.choices[0].message.content
            result_data = json.loads(result_json)
            
            # 构建结构化结果
            match_result = JobMatchResult(
                match_score=float(result_data.get("match_score", 0)) / 100.0,  # 转换为0-1之间的浮点数
                matching_skills=result_data.get("matching_skills", []),
                missing_skills=result_data.get("missing_skills", []),
                recommendations=result_data.get("recommendations", [])
            )
            
            logger.info(f"简历匹配评估完成，匹配度: {match_result.match_score:.2%}")
            return match_result
            
        except Exception as e:
            logger.error(f"简历匹配评估失败: {str(e)}")
            # 发生错误时返回基本结果
            return JobMatchResult(
                match_score=0.0,
                matching_skills=[],
                missing_skills=["无法评估匹配度"],
                recommendations=["请重新提交有效的简历和职位描述"]
            )
    
    async def optimize_resume(self, resume_text: str, job_description: Optional[str] = None) -> ResumeOptimizationResult:
        """
        优化简历
        
        Args:
            resume_text: 简历文本内容
            job_description: 可选的目标职位描述
            
        Returns:
            ResumeOptimizationResult: 简历优化结果
        """
        try:
            # 先分析简历
            resume_analysis = await self.resume_analyzer.analyze_resume(resume_text, job_description)
            
            # 准备优化提示
            prompt = f"原始简历内容:\n{resume_text}\n\n"
            
            if job_description:
                prompt += f"目标职位描述:\n{job_description}\n\n"
                prompt += "请基于上述简历内容和目标职位描述，提供针对性的简历优化建议。"
            else:
                prompt += "请基于上述简历内容，提供专业的简历优化建议。"
            
            # 使用OpenAI生成优化建议
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": """你是一个专业的简历优化专家。请分析提供的简历，并返回JSON格式的优化结果，包含以下字段：
                    - improved_sections: 改进后的各个简历部分(对象，包含各部分的优化内容)
                    - added_keywords: 建议添加的关键词列表(字符串数组)
                    - suggestions: 一般性优化建议(字符串数组)
                    - before_after: 对比示例(对象，包含before和after字段，展示优化前后的差异)
                    
                    确保返回的是有效的JSON格式，不要包含任何其他文本。
                    """},
                    {"role": "user", "content": prompt}
                ],
                temperature=DEFAULT_AGENT_TEMPERATURE,
                response_format={"type": "json_object"}
            )
            
            # 解析JSON响应
            result_json = response.choices[0].message.content
            result_data = json.loads(result_json)
            
            # 构建结构化结果
            optimization_result = ResumeOptimizationResult(
                improved_sections=result_data.get("improved_sections", {}),
                added_keywords=result_data.get("added_keywords", []),
                suggestions=result_data.get("suggestions", []),
                before_after=result_data.get("before_after", {})
            )
            
            logger.info("简历优化完成")
            return optimization_result
            
        except Exception as e:
            logger.error(f"简历优化失败: {str(e)}")
            # 发生错误时返回基本结果
            return ResumeOptimizationResult(
                improved_sections={"error": "处理失败"},
                added_keywords=[],
                suggestions=["优化过程中出错，请重试"],
                before_after={}
            )
    
    async def analyze_market_trend(self, job_title: str, location: Optional[str] = None) -> Dict[str, Any]:
        """
        分析市场趋势
        
        Args:
            job_title: 职位名称
            location: 可选的地点
            
        Returns:
            Dict[str, Any]: 市场趋势分析结果
        """
        try:
            # 构建搜索参数
            search_params = JobSearchParams(
                keywords=[job_title],
                locations=[location] if location else []
            )
            
            # 爬取职位数据
            job_data = await self.job_crawler.crawl_jobs(search_params)
            
            # 使用OpenAI进行趋势分析
            market_analysis = {
                "job_data": job_data.dict(),
                "trends": {
                    "growing_skills": [],
                    "salary_trend": "",
                    "market_demand": "",
                    "competition_level": ""
                },
                "recommendations": []
            }
            
            # 如果有足够的职位数据，进行更深入的趋势分析
            if job_data.total_jobs > 0:
                client = OpenAI(api_key=self.api_key)
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": """你是一个专业的就业市场分析专家。请分析提供的职位市场数据，并返回JSON格式的趋势分析，包含以下字段：
                        - growing_skills: 增长最快的技能(字符串数组)
                        - salary_trend: 薪资趋势描述(字符串)
                        - market_demand: 市场需求状况(字符串)
                        - competition_level: 竞争程度(字符串)
                        - career_path: 可能的职业发展路径(字符串数组)
                        - recommendations: 针对求职者的建议(字符串数组)
                        
                        确保返回的是有效的JSON格式，不要包含任何其他文本。
                        """},
                        {"role": "user", "content": f"请分析以下职位市场数据:\n{json.dumps(job_data.dict(), ensure_ascii=False, indent=2)}"}
                    ],
                    temperature=DEFAULT_AGENT_TEMPERATURE,
                    response_format={"type": "json_object"}
                )
                
                # 解析JSON响应
                result_json = response.choices[0].message.content
                result_data = json.loads(result_json)
                
                # 更新趋势分析
                market_analysis["trends"] = {
                    "growing_skills": result_data.get("growing_skills", []),
                    "salary_trend": result_data.get("salary_trend", ""),
                    "market_demand": result_data.get("market_demand", ""),
                    "competition_level": result_data.get("competition_level", ""),
                    "career_path": result_data.get("career_path", [])
                }
                market_analysis["recommendations"] = result_data.get("recommendations", [])
            
            logger.info(f"市场趋势分析完成: {job_title}")
            return market_analysis
            
        except Exception as e:
            logger.error(f"市场趋势分析失败: {str(e)}")
            # 发生错误时返回基本结果
            return {
                "error": str(e),
                "job_data": {
                    "total_jobs": 0,
                    "top_skills": [],
                    "salary_range": {}
                },
                "trends": {},
                "recommendations": ["分析过程中出错，请重试"]
            }


# 示例用法
"""
# 1. 基本用法示例
import asyncio
from openai_agents.runner import Runner
from pprint import pprint

async def main():
    # 初始化协调者智能体
    coordinator = CoordinatorAgent()
    
    # 示例1：使用协调者处理简历分析请求
    resume_text = "资深Python开发工程师，5年经验，熟悉Django, Flask框架，精通RESTful API设计..."
    
    result = await Runner.run(coordinator, f"请分析这份简历：{resume_text}")
    pprint(result.final_output)
    
    # 示例2：使用协调者处理职位搜索请求
    job_request = "我想找北京地区的Python后端开发职位，薪资25k以上，有3年工作经验"
    
    result = await Runner.run(coordinator, job_request)
    pprint(result.final_output)
    
    # 示例3：综合分析请求
    comprehensive_request = {
        "type": "comprehensive_analysis",
        "resume_text": resume_text,
        "job_params": {
            "keywords": ["Python开发", "后端工程师"],
            "locations": ["北京", "上海"],
            "experience": "3-5年",
            "education": "本科",
            "salary_range": "25k-35k",
            "job_type": "全职"
        }
    }
    
    result = await coordinator.process_request(comprehensive_request)
    pprint(result)

if __name__ == "__main__":
    asyncio.run(main())
""" 