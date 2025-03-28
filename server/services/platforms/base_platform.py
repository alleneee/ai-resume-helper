"""
招聘平台基础适配器
提供统一的接口定义，供具体平台实现
"""
from abc import ABC, abstractmethod
from logging import Logger
from typing import Dict, Any, List, Optional, Tuple, Union

class BasePlatform(ABC):
    """基础平台抽象类，所有招聘平台适配器必须继承此类"""
    
    def __init__(self, browser_service, logger: Logger):
        """
        初始化基础平台
        
        Args:
            browser_service: 浏览器服务实例
            logger: 日志记录器
        """
        self.browser_service = browser_service
        self.logger = logger
        self._search_base_url = ""
        
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
    def get_search_url(self, keywords: str, location: str, **filters) -> str:
        """
        构建搜索URL
        
        Args:
            keywords: 搜索关键词
            location: 地点
            **filters: 其他过滤条件
            
        Returns:
            str: 搜索URL
        """
        pass
    
    def process_search_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理和标准化搜索参数
        
        Args:
            params: 原始搜索参数
            
        Returns:
            Dict[str, Any]: 处理后的搜索参数
        """
        # 基础参数规范化
        processed = {}
        
        # 关键词处理: 确保移除多余空格，支持关键词组合
        if 'keywords' in params:
            processed['keywords'] = params['keywords'].strip()
        else:
            processed['keywords'] = ""
            
        # 地点处理: 标准化地点名称，支持多地点
        if 'location' in params:
            location = params['location'].strip()
            if isinstance(location, str) and location:
                processed['location'] = location
            else:
                processed['location'] = ""
        else:
            processed['location'] = ""
        
        # 经验要求: 标准化经验区间，支持范围和具体年限
        if 'experience_level' in params:
            experience = params['experience_level']
            if experience:
                processed['experience_level'] = experience
        
        # 薪资范围: 标准化薪资区间，支持范围和具体数值
        if 'salary_range' in params:
            salary = params['salary_range']
            if salary:
                processed['salary_range'] = salary
        
        # 工作类型处理: 如全职、兼职、实习等
        if 'job_type' in params:
            job_type = params['job_type']
            if job_type:
                processed['job_type'] = job_type
        
        # 学历要求处理: 如学士、硕士、博士等
        if 'education_level' in params:
            education = params['education_level']
            if education:
                processed['education_level'] = education
        
        # 搜索结果数量限制
        if 'limit' in params and isinstance(params['limit'], int) and params['limit'] > 0:
            processed['limit'] = params['limit']
        else:
            processed['limit'] = 10  # 默认搜索结果数量
        
        # 行业领域处理
        if 'industry' in params:
            industry = params['industry']
            if industry:
                processed['industry'] = industry
        
        # 公司规模处理
        if 'company_size' in params:
            company_size = params['company_size']
            if company_size:
                processed['company_size'] = company_size
        
        # 发布时间处理: 今天、三天内、一周内等
        if 'posting_date' in params:
            posting_date = params['posting_date']
            if posting_date:
                processed['posting_date'] = posting_date
        
        # 是否支持远程工作
        if 'remote' in params:
            remote = params['remote']
            if isinstance(remote, bool):
                processed['remote'] = remote
        
        return processed
    
    @abstractmethod
    def search_jobs(self, **search_params) -> Dict[str, Any]:
        """
        搜索职位
        
        Args:
            **search_params: 搜索参数
                keywords (str): 搜索关键词，如"Python 开发"
                location (str): 工作地点，如"北京"、"上海"
                experience_level (str): 工作经验要求，如"1-3年"、"3-5年"
                salary_range (str): 薪资范围，如"15k-30k"
                job_type (str): 工作类型，如"全职"、"兼职"
                education_level (str): 学历要求，如"本科"、"硕士"
                limit (int): 搜索结果数量限制，默认10
                industry (str): 行业领域，如"互联网"、"金融"
                company_size (str): 公司规模，如"500-1000人"
                posting_date (str): 发布时间，如"今天"、"三天内"
                remote (bool): 是否支持远程工作
            
        Returns:
            Dict[str, Any]: 搜索结果，包含职位列表和元数据
            {
                "platform": 平台名称,
                "keywords": 搜索关键词,
                "location": 地点,
                "total_count": 总结果数量,
                "returned_count": 返回结果数量,
                "jobs": [
                    {
                        "title": 职位标题,
                        "company_name": 公司名称,
                        "location": 工作地点,
                        "salary_range": 薪资范围,
                        "job_type": 工作类型,
                        "posting_date": 发布日期,
                        "experience_level": 经验要求,
                        "education_level": 教育要求,
                        "key_skills": 关键技能要求,
                        "short_description": 职位简介摘要,
                        "company_brief": 公司信息摘要,
                        "url": 职位详情页面链接,
                        "relevance_score": 相关度评分(1-5),
                        "is_recommended": 是否推荐
                    },
                    ...
                ],
                "filters_applied": 应用的筛选条件,
                "search_time": 搜索时间戳
            }
        """
        pass
    
    @abstractmethod
    def get_job_detail(self, url: str) -> Dict[str, Any]:
        """
        获取职位详细信息
        
        Args:
            url: 职位详情页URL
            
        Returns:
            Dict[str, Any]: 职位详细信息
            {
                "title": 职位标题,
                "company_name": 公司名称,
                "location": 工作地点,
                "salary_range": 薪资范围,
                "job_type": 工作类型,
                "posting_date": 发布日期,
                "deadline": 截止日期,
                "experience_level": 工作经验要求,
                "education_level": 学历要求,
                "required_skills": 所需技能列表,
                "company_size": 公司规模,
                "funding_stage": 融资阶段,
                "industry": 行业领域,
                "job_description": 职位描述,
                "responsibilities": 工作职责列表,
                "requirements": 岗位要求列表,
                "company_description": 公司描述,
                "benefits": 福利待遇列表,
                "application_process": 应用流程,
                "application_link": 直接申请链接,
                "contact_info": 联系信息
            }
        """
        pass
    
    @abstractmethod
    def get_company_info(self, url: str) -> Dict[str, Any]:
        """
        获取公司详细信息
        
        Args:
            url: 公司详情页URL
            
        Returns:
            Dict[str, Any]: 公司详细信息
            {
                "company_name": 公司名称,
                "logo_url": 公司logo URL,
                "website": 公司官网,
                "company_size": 公司规模,
                "company_type": 公司类型,
                "funding_stage": 融资阶段,
                "funding_info": 融资信息,
                "founded_year": 成立时间,
                "industry": 行业领域,
                "headquarters": 公司总部,
                "office_locations": 办公地点列表,
                "company_description": 公司简介,
                "mission_statement": 公司使命/愿景,
                "company_culture": 公司文化,
                "products_services": 产品或服务介绍,
                "company_history": 公司发展历程,
                "founders": 创始人信息,
                "executive_team": 高管团队,
                "benefits": 公司福利,
                "work_environment": 工作环境,
                "awards": 公司荣誉/奖项,
                "social_media": 社交媒体链接,
                "hiring_policy": 招聘相关政策
            }
        """
        pass
    
    def prepare_job_application(self, job_data: Dict[str, Any], user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据职位信息和用户简历，准备职位申请材料
        
        Args:
            job_data: 职位详细信息
            user_profile: 用户简历和背景信息
            
        Returns:
            Dict[str, Any]: 职位申请建议
            {
                "job_title": 职位标题,
                "company_name": 公司名称,
                "resume_match_score": 简历匹配分数(0-100),
                "skill_matches": 技能匹配情况列表,
                "skill_gaps": 技能差距列表,
                "resume_optimization": 简历优化建议,
                "cover_letter": 定制求职信内容,
                "application_strategy": 申请策略建议,
                "interview_preparation": 面试准备建议,
                "salary_negotiation": 薪资谈判建议
            }
        """
        # 这是一个可选实现，子类可以覆盖此方法提供平台特定的申请策略
        return {
            "job_title": job_data.get("title", ""),
            "company_name": job_data.get("company_name", ""),
            "resume_match_score": 0,
            "skill_matches": [],
            "skill_gaps": [],
            "resume_optimization": "",
            "cover_letter": "",
            "application_strategy": "",
            "interview_preparation": "",
            "salary_negotiation": ""
        }
    
    def analyze_job_market(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析职位市场情况，提供洞察
        
        Args:
            search_results: 多次搜索的结果列表
            
        Returns:
            Dict[str, Any]: 市场分析结果
            {
                "top_skills": 热门技能排名,
                "salary_trends": 薪资趋势,
                "in_demand_roles": 需求最高职位,
                "geographical_trends": 地域分布,
                "experience_requirements": 经验要求分析,
                "education_requirements": 学历要求分析,
                "industry_distribution": 行业分布,
                "company_sizes": 公司规模分布,
                "recommendations": 求职建议
            }
        """
        # 默认实现，子类可以覆盖此方法提供更精确的分析
        return {
            "top_skills": [],
            "salary_trends": {},
            "in_demand_roles": [],
            "geographical_trends": {},
            "experience_requirements": {},
            "education_requirements": {},
            "industry_distribution": {},
            "company_sizes": {},
            "recommendations": ""
        }
    
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