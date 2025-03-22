"""
职位爬取Agent - 负责通过Firecrawl爬取Boss直聘的职位信息
"""
import json
import logging
import httpx
import asyncio
from typing import Dict, List, Any, Optional
from openai import OpenAI
from openai_agents.agent import Agent

from .config import (
    OPENAI_API_KEY, OPENAI_MODEL, FIRECRAWL_API_KEY, DEFAULT_AGENT_TEMPERATURE,
    BOSS_EXPERIENCE_MAP, BOSS_EDUCATION_MAP, BOSS_SALARY_MAP, BOSS_JOB_TYPE_MAP
)
from .config import JobSearchParams, JobCrawlResult

logger = logging.getLogger(__name__)

class JobCrawlerAgent(Agent):
    """
    职位爬取Agent - 使用Firecrawl API爬取Boss直聘网站上的职位信息
    并分析职位要求、薪资范围等市场趋势
    """
    
    def __init__(self, api_key: str = None, model: str = None):
        """初始化职位爬取Agent"""
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or OPENAI_MODEL
        self.firecrawl_api_key = FIRECRAWL_API_KEY
        
        super().__init__(
            name="职位信息专家",
            handoff_description="专门爬取和分析职位市场信息的专家",
            instructions=self._get_agent_instructions(),
            model=self.model,
        )
    
    def _get_agent_instructions(self) -> str:
        """获取Agent指令"""
        return """你是一个专业的职位数据爬取分析专家，负责从Boss直聘获取职位信息并进行分析。
        
你的主要职责包括：
1. 使用Firecrawl API爬取Boss直聘上的职位信息
2. 解析和分析爬取的职位数据
3. 识别市场上最需求的技能、常见要求和薪资范围
4. 提供结构化的职位市场分析结果

当用户提供搜索条件时，你应该：
- 准确理解并转换为API调用参数
- 有效地抓取相关职位数据
- 对数据进行系统性分析，识别技能需求模式
- 提供统计性的薪资范围和要求分析
"""
    
    async def crawl_jobs(self, search_params: JobSearchParams) -> JobCrawlResult:
        """
        爬取并分析职位数据
        
        Args:
            search_params: 职位搜索参数
            
        Returns:
            JobCrawlResult: 职位爬取分析结果
        """
        try:
            # 构建API参数
            api_params = self._build_api_params(search_params)
            
            # 调用Firecrawl API获取职位数据
            jobs_data = await self._call_firecrawl_api(api_params)
            
            if not jobs_data or "jobs" not in jobs_data or not jobs_data["jobs"]:
                logger.warning(f"未找到符合条件的职位: {search_params}")
                return JobCrawlResult(
                    total_jobs=0,
                    top_skills=[],
                    salary_range={"min": 0, "max": 0, "currency": "CNY", "period": "monthly"},
                    common_requirements=[]
                )
            
            # 解析职位数据
            total_jobs = len(jobs_data["jobs"])
            logger.info(f"找到 {total_jobs} 个职位")
            
            # 提取薪资范围
            salary_range = await self._analyze_salary_range(jobs_data["jobs"])
            
            # 提取技能需求
            top_skills = await self._extract_skills(jobs_data["jobs"])
            
            # 提取常见要求
            common_requirements = await self._extract_common_requirements(jobs_data["jobs"])
            
            # 返回结果
            return JobCrawlResult(
                total_jobs=total_jobs,
                top_skills=top_skills,
                salary_range=salary_range,
                common_requirements=common_requirements
            )
            
        except Exception as e:
            logger.error(f"职位爬取失败: {str(e)}")
            # 发生错误时返回基本结果
            return JobCrawlResult(
                total_jobs=0,
                top_skills=[],
                salary_range={"error": str(e)},
                common_requirements=[]
            )
    
    def _build_api_params(self, search_params: JobSearchParams) -> Dict[str, Any]:
        """构建Firecrawl API参数"""
        # 构建基础参数
        params = {
            "keywords": " ".join(search_params.keywords),
            "locations": ",".join(search_params.locations) if search_params.locations else "",
            "page": 1,
            "count": 50  # 获取的职位数量
        }
        
        # 添加工作经验筛选
        if search_params.experience and search_params.experience in BOSS_EXPERIENCE_MAP:
            params["experience"] = BOSS_EXPERIENCE_MAP[search_params.experience]
        
        # 添加学历要求筛选
        if search_params.education and search_params.education in BOSS_EDUCATION_MAP:
            params["education"] = BOSS_EDUCATION_MAP[search_params.education]
        
        # 添加薪资范围筛选
        if search_params.salary_range and search_params.salary_range in BOSS_SALARY_MAP:
            params["salary"] = BOSS_SALARY_MAP[search_params.salary_range]
        
        # 添加工作类型筛选
        if search_params.job_type and search_params.job_type in BOSS_JOB_TYPE_MAP:
            params["job_type"] = BOSS_JOB_TYPE_MAP[search_params.job_type]
        
        return params
    
    async def _call_firecrawl_api(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """调用Firecrawl API获取职位数据"""
        if not self.firecrawl_api_key:
            raise ValueError("Firecrawl API密钥未设置")
        
        try:
            # 构建API请求URL
            url = "https://api.firecrawl.dev/bosszp/search"
            
            # 设置请求头
            headers = {
                "Authorization": f"Bearer {self.firecrawl_api_key}",
                "Content-Type": "application/json"
            }
            
            # 发送API请求
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=params, headers=headers)
                
                if response.status_code != 200:
                    logger.error(f"Firecrawl API请求失败: {response.status_code} {response.text}")
                    raise Exception(f"API请求失败: {response.status_code}")
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Firecrawl API调用失败: {str(e)}")
            raise
    
    async def _extract_skills(self, jobs: List[Dict[str, Any]]) -> List[str]:
        """从职位数据中提取热门技能"""
        # 提取所有职位描述
        descriptions = [job.get("description", "") for job in jobs if job.get("description")]
        if not descriptions:
            return []
        
        combined_text = "\n".join(descriptions[:10])  # 限制数量以控制API请求大小
        
        client = OpenAI(api_key=self.api_key)
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个职位技能提取专家。请从职位描述中提取出最常见的技能要求，并按照需求频率排序。结果仅返回技能列表，每项一行，不要添加其他说明。"},
                    {"role": "user", "content": f"请从以下职位描述中提取出15-20个最常见的技能要求，按需求频率排序:\n\n{combined_text}"}
                ],
                temperature=DEFAULT_AGENT_TEMPERATURE,
                max_tokens=500
            )
            
            skills_text = response.choices[0].message.content.strip()
            
            # 解析技能列表
            skills = []
            for line in skills_text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                    
                # 移除序号、破折号等前缀
                if any(line.startswith(prefix) for prefix in ["-", "*", "•"]) or (len(line) >= 2 and line[0].isdigit() and line[1] in ['.', '、', '）', ')']):
                    skill = line.lstrip("-*•0123456789.、）) ").strip()
                else:
                    skill = line
                    
                if skill and skill not in skills:
                    skills.append(skill)
            
            return skills[:20]  # 限制返回数量
            
        except Exception as e:
            logger.error(f"技能提取失败: {str(e)}")
            return ["技能提取过程中出错"]
    
    async def _analyze_salary_range(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析职位薪资范围"""
        if not jobs:
            return {"min": 0, "max": 0, "currency": "CNY", "period": "monthly"}
        
        # 提取所有有效的薪资信息
        salaries = []
        for job in jobs:
            salary_text = job.get("salary", "")
            if salary_text:
                parsed = self._parse_salary(salary_text)
                if parsed:
                    salaries.append(parsed)
        
        if not salaries:
            return {"min": 0, "max": 0, "currency": "CNY", "period": "monthly"}
        
        # 计算统计值
        min_values = [s["min"] for s in salaries]
        max_values = [s["max"] for s in salaries]
        
        # 计算平均值
        avg_min = sum(min_values) / len(min_values)
        avg_max = sum(max_values) / len(max_values)
        
        # 计算中位数
        min_values.sort()
        max_values.sort()
        median_min = min_values[len(min_values) // 2]
        median_max = max_values[len(max_values) // 2]
        
        # 计算最常见的薪资范围
        salary_ranges = [f"{s['min']}-{s['max']}" for s in salaries]
        from collections import Counter
        most_common = Counter(salary_ranges).most_common(3)
        
        return {
            "average": {"min": int(avg_min), "max": int(avg_max)},
            "median": {"min": int(median_min), "max": int(median_max)},
            "most_common": most_common,
            "currency": "CNY",
            "period": "monthly"
        }
    
    def _parse_salary(self, salary_text: str) -> Optional[Dict[str, int]]:
        """解析薪资文本"""
        if not salary_text:
            return None
        
        # 移除单位和其他文本
        salary_text = salary_text.lower()
        salary_text = salary_text.replace("k", "").replace("千", "")
        
        # 处理范围值
        if "-" in salary_text:
            parts = salary_text.split("-")
            if len(parts) == 2:
                try:
                    min_val = float(parts[0].strip()) * 1000
                    max_val = float(parts[1].strip()) * 1000
                    return {"min": int(min_val), "max": int(max_val)}
                except ValueError:
                    pass
        
        # 处理单一值
        try:
            value = float(salary_text.strip()) * 1000
            return {"min": int(value), "max": int(value)}
        except ValueError:
            pass
        
        return None
    
    async def _extract_common_requirements(self, jobs: List[Dict[str, Any]]) -> List[str]:
        """提取常见的职位要求"""
        # 提取所有职位描述
        descriptions = [job.get("description", "") for job in jobs if job.get("description")]
        if not descriptions:
            return []
        
        combined_text = "\n".join(descriptions[:10])  # 限制数量以控制API请求大小
        
        client = OpenAI(api_key=self.api_key)
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个职位分析专家。请从职位描述中提取出最常见的要求（非技术技能），如工作经验、学历要求、个人素质等。结果仅返回要求列表，每项一行，不要添加其他说明。"},
                    {"role": "user", "content": f"请从以下职位描述中提取出10个最常见的非技术要求，如工作经验、学历要求、个人素质等:\n\n{combined_text}"}
                ],
                temperature=DEFAULT_AGENT_TEMPERATURE,
                max_tokens=500
            )
            
            requirements_text = response.choices[0].message.content.strip()
            
            # 解析要求列表
            requirements = []
            for line in requirements_text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                    
                # 移除序号、破折号等前缀
                if any(line.startswith(prefix) for prefix in ["-", "*", "•"]) or (len(line) >= 2 and line[0].isdigit() and line[1] in ['.', '、', '）', ')']):
                    requirement = line.lstrip("-*•0123456789.、）) ").strip()
                else:
                    requirement = line
                    
                if requirement and requirement not in requirements:
                    requirements.append(requirement)
            
            return requirements[:10]  # 限制返回数量
            
        except Exception as e:
            logger.error(f"要求提取失败: {str(e)}")
            return ["要求提取过程中出错"] 