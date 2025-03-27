"""
招聘平台基础适配器
提供统一的接口定义，供具体平台实现
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BasePlatform(ABC):
    """招聘平台基础适配器抽象类"""
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """平台名称"""
        pass
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        """平台基础URL"""
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def get_job_detail(self, job_id_or_url: str) -> Optional[Dict[str, Any]]:
        """
        获取职位详情
        
        Args:
            job_id_or_url: 职位ID或URL
            
        Returns:
            职位详情
        """
        pass
    
    @abstractmethod
    async def get_company_info(self, company_id_or_url: str) -> Optional[Dict[str, Any]]:
        """
        获取公司信息
        
        Args:
            company_id_or_url: 公司ID或URL
            
        Returns:
            公司信息
        """
        pass
    
    @abstractmethod
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
        pass
    
    def get_job_task_prompt(self, url: str) -> str:
        """
        获取职位爬取任务提示词
        
        Args:
            url: 职位URL
            
        Returns:
            任务提示词
        """
        return f"""
        任务目标: 爬取{self.platform_name}职位详情页面
        
        步骤:
        1. 访问: {url}
        2. 提取职位信息，包括职位标题、公司名称、工作地点等
        3. 输出JSON格式结果
        
        特定提示:
        - 该平台的职位标题通常位于页面的h1标签或者具有特定class的元素中
        - 薪资信息通常在标题附近
        - 职位描述通常在页面的主体部分
        """
    
    def get_company_task_prompt(self, url: str) -> str:
        """
        获取公司爬取任务提示词
        
        Args:
            url: 公司URL
            
        Returns:
            任务提示词
        """
        return f"""
        任务目标: 爬取{self.platform_name}公司详情页面
        
        步骤:
        1. 访问: {url}
        2. 提取公司信息，包括公司名称、规模、融资阶段等
        3. 输出JSON格式结果
        
        特定提示:
        - 该平台的公司名称通常位于页面的顶部
        - 公司规模和融资阶段通常在公司简介部分
        - 公司描述通常在页面的主体部分
        """ 