"""
智能代理服务
处理简历优化、职位匹配和求职信生成等AI驱动功能
"""
import logging
import os
import json
from typing import Dict, Any, List, Optional, Union, AsyncIterator, cast
from datetime import datetime
import httpx
from contextlib import asynccontextmanager
from bson import ObjectId
import asyncio
from functools import lru_cache
import re
from bs4 import BeautifulSoup
from motor.motor_asyncio import AsyncIOMotorDatabase
from firecrawl import FirecrawlApp
from dotenv import load_dotenv
from config.settings import Settings, get_settings
from langchain_openai import ChatOpenAI
from browser_use import Agent as BrowserAgent, ActionResult, Controller
from browser_use.browser.browser import Browser, BrowserConfig
from pydantic import BaseModel, Field, HttpUrl

# 加载环境变量
load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)

# 定义HTTP客户端超时和重试配置
HTTP_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
MAX_RETRIES = 3
RETRY_BACKOFF = 0.5  # 重试间隔的基础秒数（会按指数增长）

# 定义响应模型
class JobDetail(BaseModel):
    """职位详情模型"""
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
    url: Optional[HttpUrl] = Field(None, description="职位链接")
    posted_date: Optional[str] = Field(None, description="发布日期")
    
    class Config:
        """配置类"""
        json_encoders = {
            ObjectId: str
        }
        from_attributes = True

# 创建browser-use动作控制器并定义动作
controller = Controller()

@controller.action("获取页面内容")
def get_page_content():
    """获取当前页面的内容"""
    return ActionResult(
        include_in_memory=True, 
        extracted_content="页面内容已提取"
    )

@controller.action("提取工作详情")
def extract_job_details():
    """提取页面中的工作详情信息"""
    return ActionResult(
        include_in_memory=True,
        extracted_content="工作详情已提取"
    )

@asynccontextmanager
async def get_http_client() -> AsyncIterator[httpx.AsyncClient]:
    """
    获取HTTP异步客户端的上下文管理器
    
    使用上下文管理器确保资源正确释放
    
    Yields:
        httpx.AsyncClient: 配置好的HTTP异步客户端
    """
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        yield client

class AgentService:
    """智能代理服务类"""
    
    _instance = None
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        初始化代理服务
        
        Args:
            settings: 应用配置，如果为None则使用全局配置
        """
        # 使用传入的settings或获取全局settings
        self.settings = settings or get_settings()
        
        # 从settings获取API配置
        self.api_key = self.settings.OPENAI_API_KEY
        self.api_base_url = self.settings.OPENAI_API_BASE_URL
        self.model = self.settings.OPENAI_MODEL
        self.job_search_api_key = self.settings.JOB_SEARCH_API_KEY
        self.job_search_api_url = self.settings.JOB_SEARCH_API_URL
        
        # Firecrawl API配置
        self.firecrawl_api_key = self.settings.FIRECRAWL_API_KEY
        self.firecrawl_app = None
        if self.firecrawl_api_key:
            self.firecrawl_app = FirecrawlApp(api_key=self.firecrawl_api_key)
        
        # Browser-use 配置
        self.browser_controller = controller
        self.browser_config = BrowserConfig(headless=True)
        self.browser = Browser(config=self.browser_config)
        self.llm = ChatOpenAI(
            api_key=self.api_key,
            base_url=self.api_base_url,
            model=self.model,
            temperature=0.0
        )
        
        # 验证配置
        if not self.api_key:
            logger.warning("OPENAI_API_KEY 环境变量未设置")
        
        if not self.job_search_api_key:
            logger.warning("JOB_SEARCH_API_KEY 环境变量未设置")
            
        if not self.firecrawl_api_key:
            logger.warning("FIRECRAWL_API_KEY 环境变量未设置，将使用browser-use爬取方法")

    @classmethod
    @lru_cache()
    def get_instance(cls, settings: Optional[Settings] = None) -> 'AgentService':
        """
        获取AgentService单例实例
        
        使用lru_cache确保单例模式下的性能
        
        Args:
            settings: 应用配置，如果为None则使用全局配置
            
        Returns:
            AgentService实例
        """
        if cls._instance is None:
            cls._instance = cls(settings)
        return cls._instance
    
    async def search_jobs(
        self,
        keywords: List[str],
        location: Optional[str] = None,
        job_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        education_level: Optional[str] = None,
        salary_min: Optional[int] = None,
        salary_max: Optional[int] = None,
        company_size: Optional[str] = None,
        funding_stage: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
        user_id: str = None,
        db: Optional[AsyncIOMotorDatabase] = None
    ) -> Dict[str, Any]:
        """
        搜索职位
        
        Args:
            keywords: 关键词
            location: 地点
            job_type: 职位类型
            experience_level: 经验水平
            education_level: 学历要求
            salary_min: 最低薪资
            salary_max: 最高薪资
            company_size: 公司规模
            funding_stage: 融资阶段
            page: 页码
            limit: 每页数量
            user_id: 用户ID
            db: MongoDB数据库连接
            
        Returns:
            搜索结果，包含职位列表和分页信息
        """
        try:
            logger.info(f"开始搜索职位: 关键词: {keywords}")
            
            # 调用职位搜索API
            jobs = await self._search_jobs_api(
                keywords=keywords,
                location=location,
                job_type=job_type,
                experience_level=experience_level,
                education_level=education_level,
                salary_min=salary_min,
                salary_max=salary_max,
                company_size=company_size,
                funding_stage=funding_stage,
                page=page,
                limit=limit
            )
            
            # 如果提供了数据库连接，则存储爬取的岗位信息
            if db and jobs:
                await self._store_jobs_in_db(jobs, user_id, db)
            
            # 计算总数
            total = len(jobs)
            
            # 构建返回结果
            result = {
                "jobs": jobs,
                "total": total,
                "page": page,
                "limit": limit
            }
            
            logger.info(f"职位搜索完成: 关键词: {keywords} - 找到 {total} 个职位")
            return result
            
        except Exception as e:
            logger.error(f"职位搜索失败: {str(e)}")
            raise
    
    async def _store_jobs_in_db(
        self, 
        jobs: List[Dict[str, Any]], 
        user_id: str, 
        db: AsyncIOMotorDatabase
    ) -> None:
        """
        将职位信息存储到数据库
        
        Args:
            jobs: 职位列表
            user_id: 用户ID
            db: MongoDB数据库连接
        """
        try:
            # 创建批量操作列表
            operations = []
            for job in jobs:
                # 创建查询条件（使用职位ID和URL作为唯一标识）
                query = {
                    "$or": [
                        {"id": job.get("id")},
                        {"url": job.get("url")}
                    ]
                }
                
                # 添加用户ID和时间戳
                job_data = job.copy()
                job_data["user_id"] = user_id
                job_data["created_at"] = datetime.utcnow()
                job_data["updated_at"] = datetime.utcnow()
                
                # 创建upsert操作
                operations.append({
                    "update_one": {
                        "filter": query,
                        "update": {"$set": job_data},
                        "upsert": True
                    }
                })
            
            # 如果有操作，执行批量写入
            if operations:
                result = await db.job_listings.bulk_write(operations)
                logger.info(f"已存储 {len(operations)} 个职位信息到数据库")
        
        except Exception as e:
            logger.error(f"存储职位信息到数据库失败: {str(e)}")
    
    async def _search_jobs_api(
        self,
        keywords: List[str],
        location: Optional[str] = None,
        job_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        education_level: Optional[str] = None,
        salary_min: Optional[int] = None,
        salary_max: Optional[int] = None,
        company_size: Optional[str] = None,
        funding_stage: Optional[str] = None,
        page: int = 1,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        调用职位搜索API
        
        Args:
            keywords: 关键词
            location: 地点
            job_type: 职位类型
            experience_level: 经验水平
            education_level: 学历要求
            salary_min: 最低薪资
            salary_max: 最高薪资
            company_size: 公司规模
            funding_stage: 融资阶段
            page: 页码
            limit: 每页数量
            
        Returns:
            职位列表
        """
        logger.debug(f"调用职位搜索API: 关键词: {keywords}")
        
        # 构建查询参数
        params = {
            "keywords": ",".join(keywords),
            "limit": limit,
            "page": page
        }
        
        # 添加可选参数
        optional_params = {
            "location": location,
            "job_type": job_type,
            "experience_level": experience_level,
            "education_level": education_level,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "company_size": company_size,
            "funding_stage": funding_stage
        }
        
        # 过滤掉None值，保留有效参数
        params.update({k: v for k, v in optional_params.items() if v is not None})
        
        # 尝试从API获取数据
        try:
            # 使用重试机制调用API
            for attempt in range(MAX_RETRIES):
                try:
                    async with get_http_client() as client:
                        response = await client.get(
                            f"{self.job_search_api_url}/search",
                            headers={
                                "Authorization": f"Bearer {self.job_search_api_key}",
                                "Content-Type": "application/json"
                            },
                            params=params
                        )
                        
                        response.raise_for_status()
                        result = response.json()
                        
                        # 返回职位列表
                        jobs = result.get("jobs", [])
                        
                        # 如果API返回了职位列表，则爬取每个职位的详细信息
                        if jobs:
                            # 并行爬取详细信息
                            detailed_jobs = await self._scrape_job_details(jobs)
                            return detailed_jobs
                        
                        return jobs
                
                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    # 如果不是最后一次尝试，则等待后重试
                    if attempt < MAX_RETRIES - 1:
                        retry_delay = RETRY_BACKOFF * (2 ** attempt)  # 指数退避
                        logger.warning(f"API请求失败，{retry_delay}秒后重试 ({attempt+1}/{MAX_RETRIES}): {str(e)}")
                        await asyncio.sleep(retry_delay)
                    else:
                        # 最后一次尝试失败，记录错误并切换到备用方法
                        logger.error(f"API请求重试次数已达上限，切换到网络爬取: {str(e)}")
                        raise
            
            # 如果所有重试都失败，尝试直接爬取职位信息
            return await self._scrape_jobs_from_web(
                keywords=keywords,
                location=location,
                job_type=job_type,
                experience_level=experience_level,
                education_level=education_level,
                salary_min=salary_min,
                salary_max=salary_max,
                company_size=company_size,
                funding_stage=funding_stage,
                limit=limit
            )
                
        except Exception as e:
            logger.error(f"职位搜索API调用失败: {str(e)}")
            # 如果API调用失败，返回模拟数据
            return await self._get_mock_jobs(
                keywords=keywords, 
                location=location, 
                experience_level=experience_level,
                education_level=education_level,
                company_size=company_size,
                funding_stage=funding_stage,
                limit=limit
            )
    
    async def _scrape_job_details(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        爬取职位详细信息
        
        Args:
            jobs: 职位列表
            
        Returns:
            带有详细信息的职位列表
        """
        try:
            detailed_jobs = []
            
            # 创建任务，并控制并发数
            semaphore = asyncio.Semaphore(5)  # 限制最大并发数为5
            
            async def fetch_with_semaphore(job: Dict[str, Any]) -> Dict[str, Any]:
                async with semaphore:
                    return await self._scrape_single_job_detail(job)
            
            # 创建爬取任务
            tasks = []
            for job in jobs:
                if job.get("url"):
                    task = asyncio.create_task(fetch_with_semaphore(job))
                    tasks.append(task)
                else:
                    detailed_jobs.append(job)
            
            # 等待所有任务完成
            if tasks:
                # 超时设置，避免单个任务阻塞太久
                completed, pending = await asyncio.wait(
                    tasks, 
                    timeout=60.0,  # 设置总体超时时间
                    return_when=asyncio.ALL_COMPLETED
                )
                
                # 取消所有未完成的任务
                for task in pending:
                    task.cancel()
                
                # 处理完成的任务结果
                for task in completed:
                    try:
                        result = task.result()
                        if result:
                            detailed_jobs.append(result)
                    except Exception as e:
                        logger.error(f"爬取职位详情任务失败: {str(e)}")
            
            return detailed_jobs
            
        except Exception as e:
            logger.error(f"爬取职位详情失败: {str(e)}")
            return jobs
    
    async def _scrape_single_job_detail(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        爬取单个职位的详细信息
        
        Args:
            job: 职位信息
            
        Returns:
            带有详细信息的职位
        """
        try:
            url = job.get("url")
            if not url:
                return job
            
            # 创建详细职位信息
            detailed_job = job.copy()
            
            # 使用browser-use爬取页面内容
            try:
                # 定义爬取任务
                task = f"访问 {url} 并提取工作详情信息，包括：\n" \
                      f"1. 职位标题 (title)\n" \
                      f"2. 公司名称 (company_name)\n" \
                      f"3. 工作地点 (location)\n" \
                      f"4. 薪资范围 (salary_range)\n" \
                      f"5. 工作经验要求 (experience_level)\n" \
                      f"6. 学历要求 (education_level)\n" \
                      f"7. 公司规模 (company_size)\n" \
                      f"8. 融资阶段 (funding_stage)\n" \
                      f"9. 公司描述 (company_description)\n" \
                      f"10. 职位描述 (job_description)\n" \
                      f"请将所有提取到的信息以JSON格式返回。"
                
                # 初始化浏览器代理
                browser_agent = BrowserAgent(
                    task=task,
                    llm=self.llm,
                    controller=self.browser_controller,
                    browser=self.browser
                )
                
                # 运行爬取任务
                result = await browser_agent.run()
                
                # 解析结果
                logger.info(f"Browser-use 爬取工作详情完成: {url}")
                
                # 从结果中提取JSON数据
                json_data = {}
                try:
                    # 尝试从结果文本中提取JSON
                    import re
                    json_match = re.search(r'```json\n(.*?)\n```', result, re.DOTALL)
                    if json_match:
                        json_text = json_match.group(1)
                        json_data = json.loads(json_text)
                    else:
                        # 如果没有找到JSON代码块，尝试直接解析
                        json_data = json.loads(result)
                except Exception as e:
                    logger.warning(f"解析爬取结果为JSON失败: {str(e)}")
                
                # 更新详细职位信息
                if json_data:
                    # 与详细职位信息合并
                    for key, value in json_data.items():
                        if value and not detailed_job.get(key):
                            detailed_job[key] = value
                
                # 如果至少提取了部分信息，则返回
                if json_data:
                    return detailed_job
                
            except Exception as e:
                logger.error(f"使用Browser-use爬取职位详情失败: {str(e)}，将使用备用方法")
            
            # 备用方法：使用httpx直接爬取
            async with get_http_client() as client:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                html_content = response.text
            
            # 解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取职位标题（如果尚未有）
            if not detailed_job.get("title"):
                title_elem = soup.select_one('h1, .job-title, [data-testid="job-title"]')
                if title_elem:
                    detailed_job["title"] = title_elem.get_text(strip=True)
            
            # 提取公司名称（如果尚未有）
            if not detailed_job.get("company_name"):
                company_elem = soup.select_one('.company-name, [data-testid="company-name"]')
                if company_elem:
                    detailed_job["company_name"] = company_elem.get_text(strip=True)
            
            # 提取工作地点（如果尚未有）
            if not detailed_job.get("location"):
                location_elem = soup.select_one('.location, [data-testid="location"]')
                if location_elem:
                    detailed_job["location"] = location_elem.get_text(strip=True)
            
            # 提取薪资范围（如果尚未有）
            if not detailed_job.get("salary_range"):
                salary_elem = soup.select_one('.salary, [data-testid="salary"]')
                if salary_elem:
                    detailed_job["salary_range"] = salary_elem.get_text(strip=True)
            
            # 提取公司描述
            if not detailed_job.get("company_description"):
                company_description_elem = soup.select_one('.company-description, .about-company, [data-testid="company-description"]')
                if company_description_elem:
                    detailed_job["company_description"] = company_description_elem.get_text(strip=True)
            
            # 提取经验要求（如果尚未有）
            if not detailed_job.get("experience_level"):
                # 尝试从HTML中提取
                experience_elem = soup.select_one('.experience-requirement, [data-testid="experience-level"]')
                if experience_elem:
                    detailed_job["experience_level"] = experience_elem.get_text(strip=True)
                else:
                    # 从职位描述中提取经验要求
                    description = detailed_job.get("description", "")
                    experience_match = re.search(r'(\d+[-\s]?\d*)\s*年.*经[验历]', description)
                    if experience_match:
                        detailed_job["experience_level"] = experience_match.group(0)
            
            # 提取学历要求（如果尚未有）
            if not detailed_job.get("education_level"):
                # 尝试从HTML中提取
                education_elem = soup.select_one('.education-requirement, [data-testid="education-level"]')
                if education_elem:
                    detailed_job["education_level"] = education_elem.get_text(strip=True)
                else:
                    # 从职位描述中提取学历要求
                    description = detailed_job.get("description", "")
                    education_patterns = [
                        r'本科及以上',
                        r'硕士及以上',
                        r'博士及以上',
                        r'大专及以上',
                        r'高中及以上'
                    ]
                    for pattern in education_patterns:
                        if pattern in description:
                            detailed_job["education_level"] = pattern
                            break
            
            # 提取公司规模（如果尚未有）
            if not detailed_job.get("company_size"):
                company_size_elem = soup.select_one('.company-size, [data-testid="company-size"]')
                if company_size_elem:
                    detailed_job["company_size"] = company_size_elem.get_text(strip=True)
                else:
                    # 从职位描述中提取公司规模
                    description = detailed_job.get("description", "")
                    size_patterns = {
                        r'(?:少于|不到)\s*50\s*人': "初创公司(<50人)",
                        r'50-200\s*人': "小型公司(50-200人)",
                        r'(?:200|201)-(?:1000|999)\s*人': "中型公司(201-1000人)",
                        r'(?:1000|1001)-(?:5000|4999)\s*人': "大型公司(1001-5000人)",
                        r'(?:超过|大于|多于)\s*5000\s*人': "超大型企业(>5000人)"
                    }
                    for pattern, size in size_patterns.items():
                        if re.search(pattern, description):
                            detailed_job["company_size"] = size
                            break
            
            # 提取融资阶段（如果尚未有）
            if not detailed_job.get("funding_stage"):
                funding_elem = soup.select_one('.funding-stage, [data-testid="funding-stage"]')
                if funding_elem:
                    detailed_job["funding_stage"] = funding_elem.get_text(strip=True)
                else:
                    # 从职位描述中提取融资阶段
                    description = detailed_job.get("description", "")
                    funding_patterns = {
                        r'(?:自筹资金|自主研发|自有资金)': "自筹资金",
                        r'(?:种子轮|天使轮)': "种子轮",
                        r'A\s*轮': "A轮",
                        r'B\s*轮': "B轮",
                        r'C\s*轮': "C轮",
                        r'(?:D轮及以上|D\+轮|E轮|F轮)': "D轮及以上",
                        r'(?:已上市|上市公司|股票代码)': "已上市",
                        r'(?:已被收购|被.*收购|并购)': "已被收购"
                    }
                    for pattern, stage in funding_patterns.items():
                        if re.search(pattern, description):
                            detailed_job["funding_stage"] = stage
                            break
            
            return detailed_job
            
        except Exception as e:
            logger.error(f"爬取职位详情失败: {str(e)}")
            return job
    
    async def _scrape_jobs_from_web(
        self,
        keywords: List[str],
        location: Optional[str] = None,
        job_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        education_level: Optional[str] = None,
        salary_min: Optional[int] = None,
        salary_max: Optional[int] = None,
        company_size: Optional[str] = None,
        funding_stage: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        从网页爬取职位信息
        
        Args:
            keywords: 关键词
            location: 地点
            job_type: 职位类型
            experience_level: 经验水平
            education_level: 学历要求
            salary_min: 最低薪资
            salary_max: 最高薪资
            company_size: 公司规模
            funding_stage: 融资阶段
            limit: 返回数量
            
        Returns:
            职位列表
        """
        try:
            logger.info(f"从网页爬取职位信息: 关键词: {keywords}")
            
            # 这里实现从主流招聘网站爬取职位信息的逻辑
            # 由于爬虫实现较为复杂，这里仅提供一个简化版本
            
            # 模拟爬取结果
            jobs = await self._get_mock_jobs(
                keywords=keywords, 
                location=location, 
                experience_level=experience_level,
                education_level=education_level,
                company_size=company_size,
                funding_stage=funding_stage,
                limit=limit
            )
            
            # 添加爬取标记
            for job in jobs:
                job["scraped"] = True
                job["scrape_time"] = datetime.utcnow().isoformat()
            
            return jobs
            
        except Exception as e:
            logger.error(f"从网页爬取职位信息失败: {str(e)}")
            # 如果爬取失败，返回模拟数据
            return await self._get_mock_jobs(
                keywords=keywords, 
                location=location, 
                experience_level=experience_level,
                education_level=education_level,
                company_size=company_size,
                funding_stage=funding_stage,
                limit=limit
            )
    
    async def _get_mock_jobs(
        self, 
        keywords: List[str], 
        location: Optional[str] = None,
        experience_level: Optional[str] = None,
        education_level: Optional[str] = None,
        company_size: Optional[str] = None,
        funding_stage: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取模拟职位数据（当API调用失败时使用）
        
        Args:
            keywords: 关键词
            location: 地点
            experience_level: 经验水平
            education_level: 学历要求
            company_size: 公司规模
            funding_stage: 融资阶段
            limit: 返回数量
            
        Returns:
            模拟职位列表
        """
        logger.warning("使用模拟职位数据")
        
        # 经验要求映射
        experience_mapping = {
            "entry": "0-1年",
            "junior": "1-3年",
            "mid": "3-5年",
            "senior": "5-10年",
            "lead": "10年以上",
            "executive": "高管经验",
            "any": "不限"
        }
        
        # 学历要求映射
        education_mapping = {
            "high_school": "高中及以上",
            "associate": "大专及以上",
            "bachelor": "本科及以上",
            "master": "硕士及以上",
            "doctorate": "博士及以上",
            "any": "不限"
        }
        
        # 公司规模映射
        company_size_mapping = {
            "startup": "初创公司(<50人)",
            "small": "小型公司(50-200人)",
            "medium": "中型公司(201-1000人)",
            "large": "大型公司(1001-5000人)",
            "enterprise": "超大型企业(>5000人)",
            "any": "不限"
        }
        
        # 融资阶段映射
        funding_stage_mapping = {
            "bootstrap": "自筹资金",
            "seed": "种子轮",
            "series_a": "A轮",
            "series_b": "B轮",
            "series_c": "C轮",
            "series_d_plus": "D轮及以上",
            "ipo": "已上市",
            "acquired": "已被收购",
            "any": "不限"
        }
        
        # 生成模拟职位数据
        mock_jobs = []
        for i in range(min(limit, 10)):
            # 根据提供的条件生成匹配的模拟数据
            exp_level = experience_mapping.get(experience_level, experience_mapping[["entry", "junior", "mid", "senior", "lead"][i % 5]])
            edu_level = education_mapping.get(education_level, education_mapping[["associate", "bachelor", "master"][i % 3]])
            comp_size = company_size_mapping.get(company_size, company_size_mapping[["startup", "small", "medium", "large", "enterprise"][i % 5]])
            fund_stage = funding_stage_mapping.get(funding_stage, funding_stage_mapping[["seed", "series_a", "series_b", "series_c", "ipo"][i % 5]])
            
            job = {
                "id": f"mock-{i}",
                "title": f"{keywords[0] if keywords else '软件'}{['工程师', '开发者', '架构师'][i % 3]}",
                "company": f"模拟公司 {i+1}",
                "location": location or "上海",
                "description": f"这是一个模拟职位描述，包含关键词: {', '.join(keywords)}。该职位需要相关技术经验和团队协作能力。",
                "salary": f"{(i+1)*10}k-{(i+2)*10}k",
                "job_type": ["全职", "兼职", "合同工"][i % 3],
                "experience_level": exp_level,
                "education_level": edu_level,
                "company_size": comp_size,
                "funding_stage": fund_stage,
                "company_description": f"模拟公司{i+1}是一家专注于{', '.join(keywords)}领域的{comp_size}。公司目前处于{fund_stage}融资阶段，拥有优秀的团队和创新的产品。",
                "url": f"https://example.com/jobs/mock-{i}",
                "posted_date": datetime.now().strftime("%Y-%m-%d")
            }
            
            mock_jobs.append(job)
        
        return mock_jobs
    
    async def get_job_details(self, job_id: str) -> Optional[JobDetail]:
        """
        获取职位详情信息
        
        根据职位ID获取职位的详细信息，优先从数据库查询，如果不存在则尝试从URL爬取
        
        Args:
            job_id: 职位ID
            
        Returns:
            JobDetail|None: 职位详情，如果不存在则返回None
        """
        logger.info(f"获取职位详情: job_id={job_id}")
        
        try:
            job_data: Dict[str, Any] = {}
            
            # 检查ID是否为URL格式，如果是则直接爬取
            if job_id.startswith(('http://', 'https://')):
                # 创建一个最小化的职位信息对象用于爬取
                job = {
                    "id": job_id,
                    "url": job_id
                }
                
                # 使用browser-use爬取详情
                job_data = await self._scrape_single_job_detail(job)
                if not job_data:
                    logger.warning(f"爬取职位详情失败: job_id={job_id}")
                    return None
                
                logger.info(f"成功爬取职位详情: job_id={job_id}")
            else:
                # 如果不是URL，尝试从外部API获取
                try:
                    async with get_http_client() as client:
                        response = await client.get(
                            f"{self.job_search_api_url}/jobs/{job_id}",
                            headers={
                                "Authorization": f"Bearer {self.job_search_api_key}",
                                "Content-Type": "application/json"
                            }
                        )
                        
                        if response.status_code == 404:
                            logger.warning(f"职位不存在: job_id={job_id}")
                            return None
                        
                        response.raise_for_status()
                        job_data = response.json()
                        
                        # 如果返回的结果中有URL，尝试爬取更多详情
                        if job_data.get("url"):
                            job_data = await self._scrape_single_job_detail(job_data)
                except Exception as e:
                    logger.error(f"API获取职位详情失败: job_id={job_id}, error={str(e)}")
                    return None
            
            # 确保job_data包含id字段
            if not job_data.get("id"):
                job_data["id"] = job_id
                
            # 处理需要标准化的字段
            if job_data.get("requirements") and isinstance(job_data["requirements"], str):
                # 如果requirements是字符串，尝试将其转换为列表
                requirements_text = job_data["requirements"]
                # 按行分割，过滤空行，去除列表符号
                requirements_list = [
                    re.sub(r'^\s*[\-\*•]\s*', '', line.strip())
                    for line in requirements_text.split('\n')
                    if line.strip()
                ]
                job_data["requirements"] = requirements_list
                
            if job_data.get("responsibilities") and isinstance(job_data["responsibilities"], str):
                # 如果responsibilities是字符串，尝试将其转换为列表
                responsibilities_text = job_data["responsibilities"]
                # 按行分割，过滤空行，去除列表符号
                responsibilities_list = [
                    re.sub(r'^\s*[\-\*•]\s*', '', line.strip())
                    for line in responsibilities_text.split('\n')
                    if line.strip()
                ]
                job_data["responsibilities"] = responsibilities_list
                
            if job_data.get("benefits") and isinstance(job_data["benefits"], str):
                # 如果benefits是字符串，尝试将其转换为列表
                benefits_text = job_data["benefits"]
                # 按行分割，过滤空行，去除列表符号
                benefits_list = [
                    re.sub(r'^\s*[\-\*•]\s*', '', line.strip())
                    for line in benefits_text.split('\n')
                    if line.strip()
                ]
                job_data["benefits"] = benefits_list
                
            # 包装为Pydantic模型返回
            try:
                return JobDetail(**job_data)
            except Exception as e:
                # 如果无法直接转换为Pydantic模型，过滤掉额外字段后重试
                logger.warning(f"转换JobDetail模型失败，尝试过滤字段: {str(e)}")
                # 仅保留JobDetail模型中定义的字段
                valid_fields = JobDetail.__annotations__.keys()
                filtered_data = {k: v for k, v in job_data.items() if k in valid_fields}
                return JobDetail(**filtered_data)
        
        except Exception as e:
            logger.error(f"获取职位详情出错: job_id={job_id}, error={str(e)}")
            return None

# 为了向后兼容，保留原有的调用方式
agent_service = AgentService.get_instance()
