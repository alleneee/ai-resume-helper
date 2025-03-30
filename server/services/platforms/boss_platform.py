"""
Boss直聘平台适配器实现
"""
import logging
import re
import json
from typing import Dict, Any, List, Optional
from urllib.parse import quote

from server.services.platforms.base_platform import BasePlatform
from server.services.browser_scraper_service import BrowserScraperService

logger = logging.getLogger(__name__)

class BossPlatform(BasePlatform):
    """Boss直聘平台适配器实现"""
    
    def __init__(self):
        self.browser_scraper = BrowserScraperService.get_instance()
        # 父类初始化
        super().__init__(
            browser_service=self.browser_scraper,
            logger=logger
        )
        self._selectors = {
            "job_title": ".job-title, .name, h1",
            "company_name": ".company-name, .boss-name-info",
            "salary": ".salary, .badge",
            "job_description": ".job-sec-text, .job-detail, .text"
        }
    
    @property
    def platform_name(self) -> str:
        """平台名称"""
        return "boss"
    
    @property
    def base_url(self) -> str:
        """平台基础URL"""
        return "https://www.zhipin.com"
        
    @property
    def search_base_url(self) -> str:
        """搜索基础URL"""
        return self._search_base_url
        
    @search_base_url.setter
    def search_base_url(self, value: str):
        """设置搜索基础URL"""
        self._search_base_url = value
    
    def get_search_url(self, keywords: List[str], location: Optional[str] = None, **filters) -> str:
        """
        生成搜索URL
        
        Args:
            keywords: 搜索关键词
            location: 地点
            filters: 其他筛选条件
            
        Returns:
            搜索URL
        """
        keywords_str = " ".join(keywords)
        encoded_keywords = quote(keywords_str)
        
        url = f"{self.base_url}/web/geek/search?query={encoded_keywords}"
        
        if location:
            url += f"&city={quote(location)}"
        
        # 添加其他筛选条件
        if "experience" in filters:
            url += f"&experience={filters['experience']}"
        if "degree" in filters:
            url += f"&degree={filters['degree']}"
        if "salary" in filters:
            url += f"&salary={filters['salary']}"
        
        return url
    
    async def search_jobs(
        self, 
        keywords: List[str], 
        location: Optional[str] = None,
        **filters
    ) -> List[Dict[str, Any]]:
        """
        搜索职位
        
        Args:
            keywords: 搜索关键词
            location: 地点
            filters: 其他筛选条件
            
        Returns:
            职位列表
        """
        # 生成搜索URL
        search_url = self.get_search_url(keywords, location, **filters)
        
        # 构建搜索任务
        limit = filters.get("limit", 10)
        keywords_str = ", ".join(keywords)
        location_str = location or "全国"
        
        task = f"""
        任务目标: 在BOSS直聘搜索职位并提取结果
        
        步骤:
        1. 访问网址: {search_url}
        2. 等待页面加载完成
        3. 提取搜索结果中的前{limit}个职位信息，包括:
           - 职位标题 (title)
           - 公司名称 (company_name)
           - 薪资范围 (salary_range)
           - 工作地点 (location)
           - 职位链接 (url)
           - 经验要求 (experience_level) - 如有
           - 学历要求 (education_level) - 如有
        4. 将提取的信息组织成JSON数组格式返回
        
        特别注意:
        - 检查是否有登录弹窗，如有请关闭
        - BOSS直聘的职位卡片通常位于.job-list > .job-primary或类似选择器下
        - 职位链接格式通常为/job_detail/{job_id}.html
        """
        
        try:
            # 获取一个浏览器实例执行搜索
            async with self.browser_scraper.get_browser() as browser:
                # 使用browser-use执行搜索任务
                browser_agent = await self.browser_scraper.create_browser_agent(
                    task=task,
                    browser=browser
                )
                
                result = await browser_agent.run()
                
                # 解析JSON结果
                jobs = []
                try:
                    # 尝试从结果文本中提取JSON
                    json_data = self.browser_scraper._extract_json_from_result(result)
                    if isinstance(json_data, list):
                        jobs = json_data
                    elif isinstance(json_data, dict) and "jobs" in json_data:
                        jobs = json_data["jobs"]
                    else:
                        logger.warning("无法从搜索结果中提取职位列表")
                except Exception as e:
                    logger.error(f"解析搜索结果失败: {str(e)}")
                
                # 标准化职位数据
                standardized_jobs = self._standardize_job_data(jobs)
                
                # 如果获取的职位数量不足，可以考虑翻页获取更多
                if len(standardized_jobs) < limit and len(standardized_jobs) > 0:
                    logger.info(f"获取到{len(standardized_jobs)}个职位，少于请求的{limit}个")
                
                return standardized_jobs[:limit]
        
        except Exception as e:
            logger.error(f"BOSS直聘搜索职位失败: {str(e)}")
            return []
    
    async def get_job_detail(self, job_id_or_url: str) -> Optional[Dict[str, Any]]:
        """
        获取职位详情
        
        Args:
            job_id_or_url: 职位ID或URL
            
        Returns:
            职位详情
        """
        # 构建URL (如果传入的是ID)
        if not job_id_or_url.startswith(('http://', 'https://')):
            url = f"{self.base_url}/job_detail/{job_id_or_url}.html"
        else:
            url = job_id_or_url
        
        # 构建任务提示
        task = self.get_job_task_prompt(url)
        task += f"""
        特别说明:
        - BOSS直聘的职位详情页通常有以下特点:
          - 职位标题通常在页面顶部的h1或.job-title元素中
          - 薪资范围通常在标题旁边的.salary元素中
          - 公司信息通常在.company-info区域
          - 职位描述通常在.job-sec或.text-gray区域
        """
        
        try:
            # 创建一个最小化的职位信息对象
            job = {
                "id": job_id_or_url,
                "url": url,
                "platform": self.platform_name
            }
            
            # 调用browser_scraper的爬取方法
            detailed_job = await self.browser_scraper.scrape_job_detail(job)
            
            # 返回标准化的数据
            return self._standardize_job_detail(detailed_job)
        
        except Exception as e:
            logger.error(f"获取BOSS直聘职位详情失败: {str(e)}")
            return None
    
    async def get_company_info(self, company_id_or_url: str) -> Optional[Dict[str, Any]]:
        """
        获取公司信息
        
        Args:
            company_id_or_url: 公司ID或URL
            
        Returns:
            公司信息
        """
        # 构建URL (如果传入的是ID)
        if not company_id_or_url.startswith(('http://', 'https://')):
            url = f"{self.base_url}/gongsi/{company_id_or_url}.html"
        else:
            url = company_id_or_url
        
        # 构建任务提示
        task = self.get_company_task_prompt(url)
        task += f"""
        特别说明:
        - BOSS直聘的公司详情页通常有以下特点:
          - 公司名称通常在页面顶部的h1或.company-name元素中
          - 公司规模等信息通常在.info-primary区域
          - 公司简介通常在.job-sec或.text-gray区域
        """
        
        try:
            async with self.browser_scraper.get_browser() as browser:
                # 使用browser-use执行爬取任务
                browser_agent = await self.browser_scraper.create_browser_agent(
                    task=task,
                    browser=browser
                )
                
                result = await browser_agent.run()
                
                # 解析JSON结果
                company_info = {}
                try:
                    company_info = self.browser_scraper._extract_json_from_result(result)
                except Exception as e:
                    logger.error(f"解析公司信息失败: {str(e)}")
                
                # 标准化公司数据
                return self._standardize_company_data(company_info)
        
        except Exception as e:
            logger.error(f"获取BOSS直聘公司信息失败: {str(e)}")
            return None
    
    def _standardize_job_data(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        标准化职位数据
        
        Args:
            jobs: 原始职位数据列表
            
        Returns:
            标准化后的职位数据列表
        """
        standardized_jobs = []
        
        for job in jobs:
            # 确保URL是完整的
            if job.get("url") and not job["url"].startswith(('http://', 'https://')):
                job["url"] = f"{self.base_url}{job['url']}"
            
            # 提取ID (如果URL中包含)
            if job.get("url") and not job.get("id"):
                id_match = re.search(r'/job_detail/([^.]+)\.html', job["url"])
                if id_match:
                    job["id"] = id_match.group(1)
            
            # 添加平台信息
            job["platform"] = self.platform_name
            
            # 标准化字段名
            field_mapping = {
                "position": "title",
                "company": "company_name",
                "salary": "salary_range",
                "address": "location",
                "experience": "experience_level",
                "education": "education_level"
            }
            
            standardized_job = {}
            for old_field, new_field in field_mapping.items():
                if old_field in job:
                    standardized_job[new_field] = job[old_field]
                elif new_field in job:
                    standardized_job[new_field] = job[new_field]
            
            # 保留其他字段
            for field, value in job.items():
                if field not in field_mapping.keys() and field not in standardized_job:
                    standardized_job[field] = value
            
            # 确保必要字段存在
            if "title" in standardized_job:
                standardized_jobs.append(standardized_job)
        
        return standardized_jobs
    
    def _standardize_job_detail(self, job_detail: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化职位详情数据
        
        Args:
            job_detail: 原始职位详情数据
            
        Returns:
            标准化后的职位详情数据
        """
        # 对单个职位执行标准化
        return self._standardize_job_data([job_detail])[0] if job_detail else {}
    
    def _standardize_company_data(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化公司数据
        
        Args:
            company_data: 原始公司数据
            
        Returns:
            标准化后的公司数据
        """
        # 标准化字段名
        field_mapping = {
            "name": "company_name",
            "scale": "company_size",
            "financingStage": "funding_stage",
            "introduction": "company_description",
            "address": "company_address",
            "industry": "industry",
            "website": "website"
        }
        
        standardized_data = {}
        for old_field, new_field in field_mapping.items():
            if old_field in company_data:
                standardized_data[new_field] = company_data[old_field]
            elif new_field in company_data:
                standardized_data[new_field] = company_data[new_field]
        
        # 保留其他字段
        for field, value in company_data.items():
            if field not in field_mapping.keys() and field not in standardized_data:
                standardized_data[field] = value
        
        # 添加平台信息
        standardized_data["platform"] = self.platform_name
        
        return standardized_data 