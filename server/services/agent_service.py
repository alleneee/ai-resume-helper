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
from server.config.settings import Settings, get_settings
from langchain_openai import ChatOpenAI
from browser_use import Agent as BrowserAgent, ActionResult, Controller
from browser_use.browser.browser import Browser, BrowserConfig
from pydantic import BaseModel, Field, HttpUrl
from server.services.browser_scraper_service import BrowserScraperService
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
    
    _instance = None

    @classmethod
    def get_instance(cls, 
                    controller: Controller = None,
                    browser_config: Optional[BrowserConfig] = None,
                    llm_factory: Optional[LLMFactory] = None,
                    api_key: Optional[str] = None,
                    api_base_url: Optional[str] = None,
                    model: str = "gpt-4o-mini",
                    browser_pool_size: int = 3):
        """
        获取浏览器爬虫服务单例
        
        Args:
            controller: browser-use控制器，默认使用全局controller
            browser_config: 浏览器配置
            llm_factory: LLM工厂实例
            api_key: OpenAI API密钥
            api_base_url: OpenAI API基础URL
            model: 模型名称
            browser_pool_size: 浏览器实例池大小
            
        Returns:
            BrowserScraperService: 浏览器爬虫服务单例
        """
        if cls._instance is None:
            cls._instance = cls(
                controller=controller or globals().get('controller'),
                browser_config=browser_config,
                llm_factory=llm_factory,
                api_key=api_key,
                api_base_url=api_base_url,
                model=model,
                browser_pool_size=browser_pool_size
            )
        return cls._instance
    
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
        任务目标: 详细分析职位详情页面并提取完整结构化信息
        
        步骤:
        1. 访问职位详情页面: {url}
        2. 等待页面完全加载，包括动态内容
        3. 如有必要，关闭弹窗或接受Cookie提示
        4. 分析并提取以下核心信息:
           - 职位标题 (title)
           - 公司名称 (company_name)
           - 工作地点 (location) - 包括远程选项信息
           - 薪资范围 (salary_range)
           - 工作类型 (job_type) - 如全职、兼职、合同工等
           - 发布日期 (posting_date)
           - 截止日期 (deadline) - 如有
           - 工作经验要求 (experience_level)
           - 学历要求 (education_level)
           - 所需技能 (required_skills) - 列表形式
           - 公司规模 (company_size)
           - 融资阶段 (funding_stage)
           - 行业领域 (industry)
        5. 提取详细描述内容:
           - 职位描述 (job_description)
           - 工作职责 (responsibilities) - 列表形式
           - 岗位要求 (requirements) - 列表形式
           - 公司描述 (company_description)
           - 福利待遇 (benefits) - 列表形式
        6. 记录应用信息:
           - 应用流程 (application_process)
           - 直接申请链接 (application_link)
           - 联系信息 (contact_info) - 如有
        7. 输出格式: 结构化JSON对象
        
        注意事项:
        - 尽可能提取所有信息，但不要捏造不存在的内容
        - 如果找不到某项信息，对应字段返回null
        - 对于列表类型的字段，提取为数组形式
        - 确保JSON格式正确，无语法错误
        - 注意甄别真实信息与广告内容
        - 尝试使用精确的CSS选择器定位元素: .job-title, .company-name, .location, .salary 等
        - 如果页面需要登录，尝试找到游客可见的信息部分
        """
    
    def _create_job_search_task_template(self) -> str:
        """创建职位搜索任务模板"""
        return """
        任务目标: 在招聘网站上搜索并提取符合条件的职位列表信息
        
        步骤:
        1. 访问招聘网站：{url}
        2. 等待页面完全加载
        3. 执行搜索操作:
           a. 输入搜索关键词：{keywords}
           b. 选择地点：{location}
           c. 应用经验筛选：{experience_level}（如适用）
           d. 应用薪资范围筛选：{salary_range}（如适用）
           e. 应用工作类型筛选：{job_type}（如适用）
           f. 应用其他相关筛选条件（如有）
           g. 点击搜索按钮
        4. 处理搜索结果:
           a. 等待结果加载完成
           b. 检查是否有结果，如无结果尝试放宽搜索条件
           c. 如有分页，确保获取足够的结果页面
        5. 提取至少{limit}个职位信息（如有），每个职位包括:
           - 职位标题 (title)
           - 公司名称 (company_name)
           - 工作地点 (location) - 注明是否支持远程
           - 薪资范围 (salary_range)
           - 工作类型 (job_type)
           - 发布日期 (posting_date)
           - 经验要求 (experience_level)
           - 教育要求 (education_level)
           - 关键技能要求 (key_skills) - 如有明确列出
           - 职位简介摘要 (short_description) - 如有
           - 公司信息摘要 (company_brief)
           - 职位详情页面链接 (url)
        6. 评估结果质量:
           - 对每个职位添加相关度评分 (relevance_score: 1-5)，根据与搜索条件的匹配程度
           - 标记特别符合条件的优质职位 (is_recommended: true/false)
        7. 输出格式: 包含所有职位的JSON数组
        
        注意事项:
        - 优先获取最新发布的职位
        - 确保所有链接是完整的绝对URL路径
        - 应对常见反爬措施，如滚动加载更多结果时等待页面元素出现
        - 处理可能出现的登录提示或Cookie通知
        - 如果搜索结果过少，可考虑放宽部分筛选条件并记录此调整
        - 确保输出的JSON格式正确，字段名称统一
        """
    
    def _create_company_info_task_template(self) -> str:
        """创建公司信息爬取任务模板"""
        return """
        任务目标: 全面分析公司信息页面并提取详细结构化数据
        
        步骤:
        1. 访问公司页面：{url}
        2. 等待页面完全加载，包括动态内容
        3. 如有必要，关闭弹窗或接受Cookie提示
        4. 提取基本公司信息：
           - 公司名称 (company_name)
           - 公司logo URL (logo_url)
           - 公司官网 (website)
           - 公司规模 (company_size) - 员工人数范围
           - 公司类型 (company_type) - 如私企、国企、外企等
           - 融资阶段 (funding_stage)
           - 融资信息 (funding_info) - 如有详细轮次和金额
           - 成立时间 (founded_year)
           - 行业领域 (industry)
           - 公司总部 (headquarters)
           - 办公地点 (office_locations) - 可能有多个
        5. 提取详细描述内容:
           - 公司简介 (company_description)
           - 公司使命/愿景 (mission_statement)
           - 公司文化 (company_culture)
           - 产品或服务介绍 (products_services)
           - 公司发展历程 (company_history)
        6. 提取领导团队信息:
           - 创始人信息 (founders) - 姓名和头衔
           - 高管团队 (executive_team) - 如有列出
        7. 提取其他相关信息:
           - 公司福利 (benefits)
           - 工作环境 (work_environment)
           - 公司荣誉/奖项 (awards)
           - 社交媒体链接 (social_media)
           - 招聘相关政策 (hiring_policy)
        8. 输出格式: 结构化JSON对象
        
        注意事项:
        - 尽可能提取所有信息，但不要捏造不存在的内容
        - 如果找不到某项信息，对应字段返回null
        - 区分公司自述信息与客观数据
        - 注意识别和提取结构化数据，如公司规模通常有特定格式
        - 如可能，验证关键信息的准确性（如通过多个页面部分）
        - 如果页面需要登录，尝试获取游客可见的部分信息
        - 确保JSON格式正确，字段命名统一
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
                # 这里需要额外的错误处理，因为直接解析可能失败
                try:
                    json_data = json.loads(result)
                except json.JSONDecodeError:
                     logger.warning(f"直接解析结果为JSON失败。结果非标准JSON格式。")
                     # 或者尝试其他提取方式
                     json_data = {} # 重置为默认值
                except Exception as inner_e: # 捕获其他可能的错误
                    logger.warning(f"直接解析结果时发生未知错误: {inner_e}")
                    json_data = {} # 重置为默认值
        except json.JSONDecodeError as json_e: # 更具体的异常捕获
             logger.warning(f"解析提取的JSON文本失败: {json_e}")
             json_data = {} # 确保失败时有默认值
        except Exception as e: # 捕获其他查找或加载错误
            logger.warning(f"提取或解析JSON时发生错误: {e}")
            json_data = {} # 确保失败时有默认值
        
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
            logger.warning(f"职位缺少URL，无法爬取详情: {job.get('title', '未知标题')}")
            return job
        
        detailed_job = job.copy()
        logger.debug(f"开始爬取职位详情: {url}")
        
        # 使用browser-use爬取页面内容
        browser_use_successful = False
        try:
            task = self._create_job_detail_task(url)
            logger.debug(f"创建 browser-use 任务: {task[:100]}...") # Log a snippet
            
            async with self.get_browser() as browser:
                logger.debug(f"获取到浏览器实例用于: {url}")
                browser_agent = await self.create_browser_agent(
                    task=task,
                    browser=browser
                )
                logger.debug(f"创建 browser-use agent 完成")
                
                result = await browser_agent.run()
                logger.info(f"Browser-use 爬取完成: {url}. 结果长度: {len(result)}")
                
                json_data = self._extract_json_from_result(result)
                
                if json_data:
                    logger.info(f"Browser-use 成功提取到 JSON 数据，共 {len(json_data)} 个字段")
                    # 与详细职位信息合并，优先保留已有的或更新非空值
                    for key, value in json_data.items():
                        if value: # Only merge non-empty values from scraped data
                           detailed_job[key] = value # Overwrite or add
                    browser_use_successful = True # 标记 browser-use 成功提取了数据
                    return detailed_job # 成功提取，直接返回
                else:
                     logger.warning(f"Browser-use 运行完成但未能提取有效 JSON 数据: {url}")

        except Exception as e:
            logger.error(f"使用 Browser-use 爬取职位详情失败: {e}", exc_info=True)
            # 不在此处返回，允许尝试备用方法
        
        # 如果 browser-use 未成功提取数据，则使用备用方法
        if not browser_use_successful:
             logger.info(f"Browser-use 未能提取数据，尝试使用 HTTP 备用方法: {url}")
             return await self._scrape_with_http(url, detailed_job)
        else:
             # 理论上不应到达这里，因为成功时已返回
             # 但为防万一，返回已更新（或未更新）的 detailed_job
             logger.warning(f"代码逻辑异常，browser_use 标记成功但未返回，返回当前 job: {url}")
             return detailed_job
    
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
    
    def __init__(self):
        self.browser_scraper = BrowserScraperService.get_instance()
        self.platform_factory = PlatformFactory()

# 为了向后兼容，保留原有的调用方式
agent_service = AgentService()
