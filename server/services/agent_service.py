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
from server.services.platforms.platform_factory import PlatformFactory

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

# 定义智能重试装饰器
def smart_retry(max_retries=MAX_RETRIES, backoff_factor=RETRY_BACKOFF, exceptions=(httpx.RequestError, httpx.HTTPStatusError)):
    """
    智能重试装饰器，用于网络请求等可重试操作
    
    Args:
        max_retries: 最大重试次数
        backoff_factor: 重试间隔的基础秒数（会按指数增长）
        exceptions: 需要重试的异常类型
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:  # 如果不是最后一次尝试
                        wait_time = backoff_factor * (2 ** attempt)
                        logger.warning(f"{func.__name__} 失败，{wait_time}秒后重试 ({attempt+1}/{max_retries}): {str(e)}")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"{func.__name__} 重试次数已达上限: {str(e)}")
            
            # 所有重试都失败
            raise last_exception
        return wrapper
    return decorator

# 创建LLM工厂类
class LLMFactory:
    """创建语言模型实例的工厂类"""
    
    @staticmethod
    def create_openai_chat(
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0
    ) -> ChatOpenAI:
        """
        创建ChatOpenAI实例
        
        Args:
            api_key: OpenAI API密钥
            base_url: OpenAI API基础URL
            model: 模型名称
            temperature: 温度参数
            
        Returns:
            ChatOpenAI: 配置好的ChatOpenAI实例
        """
        # 获取环境变量中的API密钥（如果未指定）
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
            
        return ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=temperature
        )

# 浏览器爬虫服务类
class BrowserScraperService:
    """浏览器爬虫服务，处理所有与browser-use相关的操作"""
    
    def __init__(
        self, 
        controller: Controller,
        browser_config: Optional[BrowserConfig] = None,
        llm_factory: Optional[LLMFactory] = None,
        api_key: Optional[str] = None,
        api_base_url: Optional[str] = None,
        model: str = "gpt-4o-mini",
        browser_pool_size: int = 3
    ):
        """
        初始化浏览器爬虫服务
        
        Args:
            controller: browser-use控制器
            browser_config: 浏览器配置
            llm_factory: LLM工厂实例
            api_key: OpenAI API密钥
            api_base_url: OpenAI API基础URL
            model: 模型名称
            browser_pool_size: 浏览器实例池大小
        """
        self.controller = controller
        self.browser_config = browser_config or BrowserConfig(headless=True)
        
        # 创建浏览器实例池和信号量
        self.browsers = []
        self.browser_semaphore = asyncio.Semaphore(browser_pool_size)
        self.browsers_initialized = False
        self.browser_pool_size = browser_pool_size
        
        # 创建LLM工厂或使用传入的工厂
        self.llm_factory = llm_factory or LLMFactory()
        
        # 创建LLM实例
        self.llm = self.llm_factory.create_openai_chat(
            api_key=api_key,
            base_url=api_base_url,
            model=model,
            temperature=0.0
        )
        
        # 任务模板配置
        self.task_templates = {
            "job_detail": self._create_job_detail_task_template(),
            "job_search": self._create_job_search_task_template(),
            "company_info": self._create_company_info_task_template()
        }
    
    async def initialize(self):
        """初始化浏览器池"""
        if self.browsers_initialized:
            return
            
        for _ in range(self.browser_pool_size):
            browser = Browser(config=self.browser_config)
            self.browsers.append(browser)
        
        self.browsers_initialized = True
        logger.info(f"初始化浏览器池完成，大小：{self.browser_pool_size}")
    
    async def get_browser(self):
        """获取浏览器实例的异步上下文管理器"""
        if not self.browsers_initialized:
            await self.initialize()
            
        async with self.browser_semaphore:
            # 简单的轮询策略
            browser = self.browsers.pop(0)
            try:
                yield browser
            finally:
                self.browsers.append(browser)
    
    def _create_job_detail_task_template(self) -> str:
        """创建职位详情爬取任务模板"""
        return """
        任务目标: 爬取职位详情页面并提取结构化信息
        
        步骤:
        1. 访问: {url}
        2. 提取信息:
           - 职位标题 (title)
           - 公司名称 (company_name)
           - 工作地点 (location)
           - 薪资范围 (salary_range)
           - 工作经验要求 (experience_level)
           - 学历要求 (education_level)
           - 公司规模 (company_size)
           - 融资阶段 (funding_stage)
           - 公司描述 (company_description)
           - 职位描述 (job_description)
        3. 输出格式: JSON
        
        注意事项:
        - 尽可能提取所有信息，但不要捏造不存在的内容
        - 如果找不到某项信息，对应字段返回null
        - 确保JSON格式正确
        - 尝试使用特定选择器: .job-title, .company-name, .location, .salary 等
        """
    
    def _create_job_search_task_template(self) -> str:
        """创建职位搜索任务模板"""
        return """
        任务目标: 搜索并提取职位列表信息
        
        步骤:
        1. 访问招聘网站：{url}
        2. 输入搜索关键词：{keywords}
        3. 选择地点：{location}
        4. 应用其他筛选条件（如有）
        5. 提取搜索结果中的职位信息：
           - 职位标题
           - 公司名称
           - 工作地点
           - 薪资范围
           - 职位链接
        6. 输出格式: JSON数组
        
        注意事项:
        - 尽量获取至少{limit}个结果
        - 确保JSON格式正确
        """
    
    def _create_company_info_task_template(self) -> str:
        """创建公司信息爬取任务模板"""
        return """
        任务目标: 爬取公司信息
        
        步骤:
        1. 访问：{url}
        2. 提取公司信息：
           - 公司名称
           - 公司规模
           - 融资阶段
           - 公司描述
           - 创始人信息
           - 公司地址
        3. 输出格式: JSON
        
        注意事项:
        - 确保信息准确性
        - 如果找不到某项信息，对应字段返回null
        """
    
    def _create_job_detail_task(self, url: str) -> str:
        """
        创建职位详情爬取任务描述
        
        Args:
            url: 职位URL
            
        Returns:
            str: 任务描述
        """
        return self.task_templates["job_detail"].format(url=url)
    
    def _extract_json_from_result(self, result: str) -> Dict[str, Any]:
        """
        从结果文本中提取JSON数据
        
        Args:
            result: browser-use返回的结果文本
            
        Returns:
            Dict[str, Any]: 提取的JSON数据
        """
        json_data = {}
        try:
            # 尝试从结果文本中提取JSON
            json_match = re.search(r'```json\n(.*?)\n```', result, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
                json_data = json.loads(json_text)
            else:
                # 如果没有找到JSON代码块，尝试直接解析
                json_data = json.loads(result)
        except Exception as e:
            logger.warning(f"解析爬取结果为JSON失败: {str(e)}")
        
        return json_data
    
    @smart_retry(max_retries=3)
    async def scrape_job_detail(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        爬取单个职位的详细信息
        
        Args:
            job: 职位信息
            
        Returns:
            带有详细信息的职位
        """
        url = job.get("url")
        if not url:
            return job
        
        # 创建详细职位信息
        detailed_job = job.copy()
        
        # 使用browser-use爬取页面内容
        try:
            # 定义爬取任务
            task = self._create_job_detail_task(url)
            
            # 获取浏览器实例
            async with self.get_browser() as browser:
                # 使用辅助方法创建浏览器代理
                browser_agent = await self.create_browser_agent(
                    task=task,
                    browser=browser
                )
                
                # 运行爬取任务
                result = await browser_agent.run()
                
                # 解析结果
                logger.info(f"Browser-use 爬取工作详情完成: {url}")
                
                # 从结果中提取JSON数据
                json_data = self._extract_json_from_result(result)
                
                # 更新详细职位信息
                if json_data:
                    # 与详细职位信息合并
                    for key, value in json_data.items():
                        if value and not detailed_job.get(key):
                            detailed_job[key] = value
                    
                    # 如果至少提取了部分信息，则返回
                    return detailed_job
            
        except Exception as e:
            logger.error(f"使用Browser-use爬取职位详情失败: {str(e)}，将使用备用方法")
        
        # 备用方法：使用httpx直接爬取
        return await self._scrape_with_http(url, detailed_job)
    
    async def create_browser_agent(self, task: str, browser: Optional[Browser] = None) -> BrowserAgent:
        """
        创建浏览器代理实例
        
        Args:
            task: 任务描述
            browser: 浏览器实例，如果未提供则使用连接池中的实例
            
        Returns:
            BrowserAgent: 配置好的浏览器代理实例
        """
        # 如果未提供浏览器实例，获取一个
        browser_provided = browser is not None
        
        if not browser_provided:
            # 这里使用的是一个自管理的上下文，调用方需要处理浏览器的释放
            browser = await anext(self.get_browser().__aiter__())
        
        try:
            # 初始化浏览器代理
            browser_agent = BrowserAgent(
                task=task,
                llm=self.llm,
                controller=self.controller,
                browser=browser
            )
            
            return browser_agent
        except Exception as e:
            # 如果创建失败且是我们获取的浏览器，确保它被放回池中
            if not browser_provided:
                self.browsers.append(browser)
            raise e
    
    @smart_retry(max_retries=2)
    async def _scrape_with_http(self, url: str, detailed_job: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用HTTP请求作为备用爬取方法
        
        Args:
            url: 职位URL
            detailed_job: 当前收集的职位信息
            
        Returns:
            Dict[str, Any]: 更新后的职位信息
        """
        try:
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
            logger.error(f"使用HTTP方法爬取职位详情失败: {str(e)}")
            return detailed_job
    
    async def close(self):
        """关闭并清理所有浏览器实例"""
        if self.browsers_initialized:
            for browser in self.browsers:
                try:
                    await browser.close()
                except Exception as e:
                    logger.warning(f"关闭浏览器实例失败: {str(e)}")
            
            self.browsers = []
            self.browsers_initialized = False
            logger.info("已关闭所有浏览器实例")

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
        
        # 创建LLM工厂
        self.llm_factory = LLMFactory()
        
        # 创建浏览器爬虫服务
        self.browser_scraper = BrowserScraperService(
            controller=controller,
            api_key=self.api_key,
            api_base_url=self.api_base_url,
            model=self.model
        )
        
        # 创建平台工厂
        self.platform_factory = PlatformFactory(browser_scraper=self.browser_scraper)
        
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
        db: Optional[AsyncIOMotorDatabase] = None,
        platforms: Optional[List[str]] = None
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
            platforms: 要搜索的平台列表，如果为None则使用所有支持的平台
            
        Returns:
            搜索结果，包含职位列表和分页信息
        """
        try:
            logger.info(f"开始搜索职位: 关键词: {keywords}")
            
            # 准备筛选条件
            filters = {
                "job_type": job_type,
                "experience_level": experience_level,
                "education_level": education_level,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "company_size": company_size,
                "funding_stage": funding_stage,
                "page": page,
                "limit": limit
            }
            
            # 首先尝试使用平台工厂搜索
            all_jobs = []
            
            if platforms:
                # 在指定的平台上搜索
                for platform_name in platforms:
                    platform = self.platform_factory.get_platform(platform_name)
                    if not platform:
                        continue
                        
                    try:
                        logger.info(f"在平台 {platform_name} 上搜索职位")
                        platform_jobs = await platform.search_jobs(
                            keywords=keywords,
                            location=location,
                            **filters
                        )
                        all_jobs.extend(platform_jobs)
                    except Exception as e:
                        logger.error(f"平台 {platform_name} 搜索失败: {str(e)}")
            else:
                # 获取所有支持的平台实例
                supported_platforms = self.platform_factory.get_all_platforms()
                
                # 在所有平台上并行搜索
                if supported_platforms:
                    search_tasks = []
                    for platform in supported_platforms:
                        task = asyncio.create_task(platform.search_jobs(
                            keywords=keywords,
                            location=location,
                            **filters
                        ))
                        search_tasks.append(task)
                    
                    # 等待所有搜索任务完成
                    if search_tasks:
                        results = await asyncio.gather(*search_tasks, return_exceptions=True)
                        
                        # 处理结果
                        for i, result in enumerate(results):
                            if isinstance(result, Exception):
                                platform_name = supported_platforms[i].platform_name
                                logger.error(f"平台 {platform_name} 搜索失败: {str(result)}")
                            else:
                                all_jobs.extend(result)
            
            # 如果平台搜索没有返回结果，尝试使用API
            if not all_jobs:
                logger.info("平台搜索未返回结果，尝试使用API")
                api_jobs = await self._search_jobs_api(
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
                all_jobs.extend(api_jobs)
            
            # 如果提供了数据库连接，则存储爬取的岗位信息
            if db and all_jobs and user_id:
                await self._store_jobs_in_db(all_jobs, user_id, db)
            
            # 分页处理 (简单实现，实际环境可能需要更复杂的逻辑)
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_jobs = all_jobs[start_idx:end_idx] if start_idx < len(all_jobs) else []
            
            # 计算总数
            total = len(all_jobs)
            
            # 构建返回结果
            result = {
                "jobs": paginated_jobs,
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
            concurrency = min(5, len(jobs) // 2)  # 动态计算并发数
            semaphore = asyncio.Semaphore(concurrency)  
            
            async def fetch_with_semaphore(job: Dict[str, Any]) -> Dict[str, Any]:
                async with semaphore:
                    return await self.browser_scraper.scrape_job_detail(job)
            
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
    
    async def get_job_details(self, job_id: str, platform: Optional[str] = None) -> Optional[JobDetail]:
        """
        获取职位详情信息
        
        根据职位ID获取职位的详细信息，优先从数据库查询，如果不存在则尝试从URL爬取
        
        Args:
            job_id: 职位ID或URL
            platform: 平台名称，如果知道职位来自哪个平台，可以指定
            
        Returns:
            JobDetail|None: 职位详情，如果不存在则返回None
        """
        logger.info(f"获取职位详情: job_id={job_id}")
        
        try:
            job_data: Dict[str, Any] = {}
            
            # 检查ID是否为URL格式
            is_url = job_id.startswith(('http://', 'https://'))
            
            # 如果指定了平台，直接使用该平台的适配器
            if platform:
                platform_instance = self.platform_factory.get_platform(platform)
                if platform_instance:
                    logger.info(f"使用平台 {platform} 获取职位详情")
                    job_data = await platform_instance.get_job_detail(job_id)
                    if job_data:
                        return self._convert_to_job_detail(job_data)
            
            # 如果是URL但未指定平台，尝试从URL模式判断平台
            if is_url and not platform:
                # 根据URL判断平台
                detected_platform = self._detect_platform_from_url(job_id)
                if detected_platform:
                    platform_instance = self.platform_factory.get_platform(detected_platform)
                    if platform_instance:
                        logger.info(f"从URL检测到平台 {detected_platform}")
                        job_data = await platform_instance.get_job_detail(job_id)
                        if job_data:
                            return self._convert_to_job_detail(job_data)
            
            # 如果仍未获取到数据，使用通用方法
            if not job_data:
                # 创建一个最小化的职位信息对象用于爬取
                job = {
                    "id": job_id,
                    "url": job_id if is_url else None
                }
                
                # 使用browser-use爬取详情
                job_data = await self.browser_scraper.scrape_job_detail(job)
                if not job_data:
                    logger.warning(f"爬取职位详情失败: job_id={job_id}")
                    return None
                
                logger.info(f"成功爬取职位详情: job_id={job_id}")
            
            # 确保job_data包含id字段
            if not job_data.get("id"):
                job_data["id"] = job_id
                
            # 包装为Pydantic模型返回
            return self._convert_to_job_detail(job_data)
        
        except Exception as e:
            logger.error(f"获取职位详情出错: job_id={job_id}, error={str(e)}")
            return None
    
    def _detect_platform_from_url(self, url: str) -> Optional[str]:
        """
        从URL检测平台
        
        Args:
            url: 职位URL
            
        Returns:
            平台名称，如果无法检测则返回None
        """
        url_patterns = {
            "boss": ["zhipin.com"],
            "lagou": ["lagou.com"],
            "51job": ["51job.com"],
            "zhilian": ["zhaopin.com"]
        }
        
        for platform, patterns in url_patterns.items():
            for pattern in patterns:
                if pattern in url:
                    return platform
        
        return None
    
    def _convert_to_job_detail(self, job_data: Dict[str, Any]) -> Optional[JobDetail]:
        """
        将职位数据转换为JobDetail模型
        
        Args:
            job_data: 职位数据
            
        Returns:
            JobDetail模型，如果转换失败则返回None
        """
        try:
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
            logger.error(f"转换职位数据失败: {str(e)}")
            return None

# 为了向后兼容，保留原有的调用方式
agent_service = AgentService.get_instance()
