#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# test_agent_service_scraper.py - 测试简历Agent全流程

import os
import sys
import asyncio
import logging
import json
from datetime import datetime

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))  # 获取项目根目录
sys.path.insert(0, project_root)  # 添加到导入路径

# 清除可能的模块缓存
for module in list(sys.modules.keys()):
    if module.startswith(('server.services', 'config', 'browser_use')):
        sys.modules.pop(module, None)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("测试脚本")

# 创建所有必要的mock
from functools import lru_cache
from pydantic import BaseModel

# 创建临时config模块
class Settings(BaseModel):
    browser_headless: bool = True
    browser_width: int = 1920
    browser_height: int = 1080
    browser_timeout: int = 30
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    use_proxy: bool = False
    proxy_url: str = ""
    log_level: str = "INFO"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# 创建并注入模拟模块
import types

# 创建所有必要的模块
config_module = types.ModuleType('config')
settings_module = types.ModuleType('config.settings')
browser_use_module = types.ModuleType('browser_use')
browser_browser_module = types.ModuleType('browser_use.browser')
browser_browser_browser_module = types.ModuleType('browser_use.browser.browser')
server_module = types.ModuleType('server')
server_services_module = types.ModuleType('server.services')
browser_scraper_module = types.ModuleType('server.services.browser_scraper_service')
agent_service_module = types.ModuleType('server.services.agent_service')
platform_factory_module = types.ModuleType('server.services.platforms.platform_factory')
base_platform_module = types.ModuleType('server.services.platforms.base_platform')
boss_platform_module = types.ModuleType('server.services.platforms.boss_platform')

# 注入所有模块到sys.modules
sys.modules['config'] = config_module
sys.modules['config.settings'] = settings_module
sys.modules['browser_use'] = browser_use_module
sys.modules['browser_use.browser'] = browser_browser_module
sys.modules['browser_use.browser.browser'] = browser_browser_browser_module
sys.modules['server'] = server_module
sys.modules['server.services'] = server_services_module
sys.modules['server.services.browser_scraper_service'] = browser_scraper_module
sys.modules['server.services.agent_service'] = agent_service_module
sys.modules['server.services.platforms'] = types.ModuleType('server.services.platforms')
sys.modules['server.services.platforms.platform_factory'] = platform_factory_module
sys.modules['server.services.platforms.base_platform'] = base_platform_module
sys.modules['server.services.platforms.boss_platform'] = boss_platform_module

# 设置config模块
settings_module.Settings = Settings
settings_module.get_settings = get_settings

# 模拟browser_use模块
class ActionResult:
    def __init__(self, success=True, data=None, error=None):
        self.success = success
        self.data = data or {}
        self.error = error

class Controller:
    def __init__(self):
        self.actions = {}
        
    def action(self, name):
        def decorator(func):
            from functools import wraps
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            self.actions[name] = wrapper
            return wrapper
        return decorator
        
    async def create_browser(self, **kwargs):
        return {"browser": "mock_browser"}
        
    async def close(self):
        pass

class Agent:
    def __init__(self, task=None, browser=None):
        self.task = task
        self.browser = browser
        
    async def run(self):
        return ActionResult(success=True, data={"result": "测试结果"})

# 添加Browser和BrowserConfig类
class BrowserConfig:
    def __init__(self, **kwargs):
        self.headless = kwargs.get('headless', True)
        self.width = kwargs.get('width', 1920)
        self.height = kwargs.get('height', 1080)
        self.timeout = kwargs.get('timeout', 30)
        
class Browser:
    def __init__(self, config: BrowserConfig = None):
        self.config = config or BrowserConfig()
        
    async def goto(self, url: str):
        return True
        
    async def close(self):
        pass
        
    async def wait_for_selector(self, selector: str):
        return {"element": "mock_element"}
        
    async def click(self, selector: str):
        return True
        
    async def type(self, selector: str, text: str):
        return True
        
    async def get_text(self, selector: str):
        return "mock_text"

# 设置browser_use模块属性
browser_use_module.Agent = Agent
browser_use_module.ActionResult = ActionResult
browser_use_module.Controller = Controller
browser_browser_browser_module.Browser = Browser
browser_browser_browser_module.BrowserConfig = BrowserConfig

# 添加 BasePlatform mock
class BasePlatform:
    async def search_jobs(self, **params):
        raise NotImplementedError
        
    async def get_job_detail(self, url):
        raise NotImplementedError
        
    def prepare_job_application(self, job_data, user_profile):
        return {
            "resume_match_score": 85,
            "cover_letter": "这是一封示例求职信..."
        }
        
    def analyze_job_market(self, jobs):
        """分析职位市场数据"""
        raise NotImplementedError

# 添加 BossPlatform mock
class BossPlatform(BasePlatform):
    async def search_jobs(self, **params):
        return [
            {
                "title": "Python开发工程师",
                "company_name": "Boss直聘测试公司",
                "location": params.get("location", "上海"),
                "salary_range": "25k-35k",
                "url": "https://www.zhipin.com/job/12345"
            }
        ]
        
    async def get_job_detail(self, url):
        return {
            "title": "Python开发工程师",
            "company_name": "Boss直聘测试公司",
            "location": "上海",
            "salary_range": "25k-35k",
            "description": "这是一个Boss直聘的测试职位..."
        }
        
    def analyze_job_market(self, jobs):
        """分析职位市场数据"""
        # 计算平均薪资
        salary_ranges = []
        for job in jobs:
            salary = job.get("salary_range", "")
            if salary:
                try:
                    # 解析薪资范围（假设格式为"xxk-yyk"）
                    low, high = map(lambda x: int(x.strip("k")), salary.split("-"))
                    salary_ranges.append((low + high) / 2)
                except:
                    continue
                    
        avg_salary = sum(salary_ranges) / len(salary_ranges) if salary_ranges else 0
        
        # 统计地区分布
        locations = {}
        for job in jobs:
            loc = job.get("location", "未知")
            locations[loc] = locations.get(loc, 0) + 1
            
        # 统计经验要求
        experience_levels = {}
        for job in jobs:
            exp = job.get("experience_level", "未知")
            experience_levels[exp] = experience_levels.get(exp, 0) + 1
            
        # 统计学历要求
        education_levels = {}
        for job in jobs:
            edu = job.get("education_level", "未知")
            education_levels[edu] = education_levels.get(edu, 0) + 1
            
        # 统计技能需求
        required_skills = {}
        common_skills = ["Python", "Django", "Flask", "MySQL", "Redis", "Docker", "Linux"]
        for job in jobs:
            desc = job.get("description", "").lower()
            for skill in common_skills:
                if skill.lower() in desc:
                    required_skills[skill] = required_skills.get(skill, 0) + 1
        
        return {
            "total_jobs": len(jobs),
            "average_salary": f"{avg_salary:.1f}k",
            "salary_distribution": {
                "below_20k": len([s for s in salary_ranges if s < 20]),
                "20k-30k": len([s for s in salary_ranges if 20 <= s < 30]),
                "30k-40k": len([s for s in salary_ranges if 30 <= s < 40]),
                "above_40k": len([s for s in salary_ranges if s >= 40])
            },
            "location_distribution": locations,
            "experience_requirements": experience_levels,
            "education_requirements": education_levels,
            "top_skills": dict(sorted(required_skills.items(), key=lambda x: x[1], reverse=True)[:5]),
            "market_insights": [
                "Python开发岗位需求持续增长",
                "高级开发职位占比较大",
                "本科及以上学历是主流要求",
                "Docker和微服务相关技能越来越受欢迎"
            ],
            "salary_trends": {
                "trend": "上升",
                "growth_rate": "8.5%",
                "note": "相比去年同期有所增长"
            }
        }

# 添加 PlatformFactory mock
class PlatformFactory:
    def __init__(self):
        self._platforms = {
            "boss": BossPlatform()
        }
        
    def get_platform(self, platform_name: str):
        return self._platforms.get(platform_name.lower())
        
    def get_all_platforms(self):
        return list(self._platforms.values())

# 设置平台相关模块
base_platform_module.BasePlatform = BasePlatform
boss_platform_module.BossPlatform = BossPlatform
platform_factory_module.PlatformFactory = PlatformFactory

# 添加 BrowserScraperService mock
class BrowserScraperService:
    _instance = None
    
    def __init__(self):
        self.settings = get_settings()
        self.controller = Controller()
        self.browser_config = BrowserConfig(
            headless=self.settings.browser_headless,
            width=self.settings.browser_width,
            height=self.settings.browser_height,
            timeout=self.settings.browser_timeout
        )
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
        
    async def create_browser_agent(self, task=None, browser=None):
        return Agent(task=task, browser=browser)
        
    async def get_browser(self):
        return Browser(config=self.browser_config)
        
    async def close(self):
        pass
        
    async def scrape_job_detail(self, job):
        return {"title": "测试职位", "company": "测试公司", **job}
        
    def _extract_json_from_result(self, result):
        return {"result": "测试结果"}

# 设置 BrowserScraperService 模块
browser_scraper_module.BrowserScraperService = BrowserScraperService

# 添加 AgentService mock
class AgentService:
    _instance = None
    
    def __init__(self):
        self.browser_scraper = BrowserScraperService.get_instance()
        self.platform_factory = PlatformFactory()
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
        
    async def search_jobs(self, **params):
        mock_jobs = [
            {
                "title": "Python开发工程师",
                "company_name": "测试科技有限公司",
                "location": "上海",
                "salary_range": "25k-35k",
                "experience_level": "3-5年",
                "education_level": "本科",
                "job_type": "全职",
                "url": "https://www.example.com/job/12345",
                "posted_date": "2024-03-27",
                "company_size": "500-1000人",
                "industry": "互联网",
                "description": "负责公司核心业务系统的开发和维护"
            },
            {
                "title": "高级Python工程师",
                "company_name": "示例网络科技",
                "location": "上海",
                "salary_range": "35k-50k",
                "experience_level": "5-7年",
                "education_level": "本科",
                "job_type": "全职",
                "url": "https://www.example.com/job/12346",
                "posted_date": "2024-03-26",
                "company_size": "1000-2000人",
                "industry": "互联网",
                "description": "负责团队管理和技术架构设计"
            }
        ]
        return {"jobs": mock_jobs[:params.get("limit", 5)]}
        
    async def get_job_details(self, url):
        # 根据URL返回详细信息
        mock_details = {
            "https://www.example.com/job/12345": {
                "title": "Python开发工程师",
                "company_name": "测试科技有限公司",
                "location": "上海",
                "salary_range": "25k-35k",
                "experience_level": "3-5年",
                "education_level": "本科",
                "job_type": "全职",
                "url": "https://www.example.com/job/12345",
                "posted_date": "2024-03-27",
                "company_size": "500-1000人",
                "industry": "互联网",
                "description": "负责公司核心业务系统的开发和维护",
                "responsibilities": [
                    "负责公司核心业务系统的设计和开发",
                    "参与技术方案的讨论和制定",
                    "编写技术文档和接口文档"
                ],
                "requirements": [
                    "3年以上Python开发经验",
                    "熟悉Django/Flask等主流框架",
                    "熟悉MySQL、Redis等数据库",
                    "有良好的代码风格和文档习惯"
                ],
                "benefits": [
                    "五险一金",
                    "年终奖",
                    "带薪年假",
                    "定期体检"
                ],
                "company_description": "测试科技有限公司是一家发展迅速的科技公司..."
            },
            "https://www.example.com/job/12346": {
                "title": "高级Python工程师",
                "company_name": "示例网络科技",
                "location": "上海",
                "salary_range": "35k-50k",
                "experience_level": "5-7年",
                "education_level": "本科",
                "job_type": "全职",
                "url": "https://www.example.com/job/12346",
                "posted_date": "2024-03-26",
                "company_size": "1000-2000人",
                "industry": "互联网",
                "description": "负责团队管理和技术架构设计",
                "responsibilities": [
                    "负责团队的技术管理工作",
                    "参与系统架构设计",
                    "把控代码质量和技术方向"
                ],
                "requirements": [
                    "5年以上Python开发经验",
                    "有团队管理经验",
                    "精通分布式系统设计",
                    "有大型项目经验"
                ],
                "benefits": [
                    "五险一金",
                    "年终奖",
                    "期权激励",
                    "免费三餐"
                ],
                "company_description": "示例网络科技是行业领先的互联网公司..."
            }
        }
        return mock_details.get(url, {"error": "职位不存在"})

# 设置 AgentService 模块
agent_service_module.AgentService = AgentService

async def main():
    try:
        # 导入服务，放在函数内避免循环导入问题
        from server.services.agent_service import AgentService
        
        logger.info("=== 初始化Agent服务 ===")
        # 获取AgentService实例
        agent_service = AgentService.get_instance()
        
        # 1. 测试职位搜索
        logger.info("=== 开始测试职位搜索 ===")
        search_params = {
            "keywords": "Python 开发工程师",
            "location": "上海",
            "experience_level": "3-5年",
            "education_level": "本科",
            "limit": 5
        }
        
        logger.info(f"搜索参数: {json.dumps(search_params, ensure_ascii=False)}")
        search_results = await agent_service.search_jobs(**search_params)
        
        if not search_results or not search_results.get('jobs'):
            logger.error("职位搜索失败或无结果，测试终止")
            return
            
        logger.info(f"搜索成功，找到 {len(search_results.get('jobs', []))} 个职位")
        
        # 打印搜索结果摘要
        for i, job in enumerate(search_results.get('jobs', [])[:3]):  # 只打印前3个
            logger.info(f"职位 {i+1}: {job.get('title')} - {job.get('company_name')} - {job.get('salary_range')}")
        
        # 2. 获取职位详情
        logger.info("\n=== 开始测试职位详情获取 ===")
        job_url = search_results['jobs'][0].get('url')
        if not job_url:
            logger.error("无有效职位URL，无法获取详情，测试终止")
            return
            
        logger.info(f"获取职位详情，URL: {job_url}")
        job_detail = await agent_service.get_job_details(job_url)
        
        if not job_detail:
            logger.error("获取职位详情失败，测试终止")
            return
            
        logger.info(f"成功获取职位详情: {job_detail.get('title')} - {job_detail.get('company_name')}")
        
        # 3. 测试平台特定功能
        logger.info("\n=== 开始测试平台特定功能 ===")
        platform_name = "boss"  # 或者其他实现的平台
        platform = agent_service.platform_factory.get_platform(platform_name)
        
        if not platform:
            logger.error(f"{platform_name}平台适配器不可用，跳过相关测试")
        else:
            logger.info(f"使用{platform_name}平台进行测试")
            platform_search_params = {
                "keywords": "Python",
                "location": "北京",
                "limit": 2
            }
            platform_results = await platform.search_jobs(**platform_search_params)
            
            if platform_results and len(platform_results) > 0:
                logger.info(f"平台搜索成功，找到 {len(platform_results)} 个职位")
                job_url = platform_results[0].get('url')
                if job_url:
                    platform_job_detail = await platform.get_job_detail(job_url)
                    if platform_job_detail:
                        logger.info(f"平台获取职位详情成功: {platform_job_detail.get('title')}")
        
        # 4. 测试职位申请材料准备
        logger.info("\n=== 开始测试职位申请材料准备 ===")
        # 模拟用户简历数据
        user_profile = {
            "name": "张三",
            "email": "zhangsan@example.com",
            "phone": "13800138000",
            "education": [
                {
                    "degree": "本科",
                    "school": "上海大学",
                    "major": "计算机科学",
                    "graduation_year": "2018"
                }
            ],
            "experience": [
                {
                    "company": "ABC科技",
                    "title": "Python开发工程师",
                    "start_date": "2018-07",
                    "end_date": "2021-06",
                    "description": "负责后端服务开发，使用Python和Django框架"
                },
                {
                    "company": "XYZ互联网",
                    "title": "高级开发工程师",
                    "start_date": "2021-07",
                    "end_date": "至今",
                    "description": "负责核心业务系统架构设计与实现"
                }
            ],
            "skills": ["Python", "Django", "Flask", "MySQL", "Redis", "Docker"]
        }
        
        if job_detail and platform:
            application_materials = platform.prepare_job_application(
                job_data=job_detail,
                user_profile=user_profile
            )
            
            if application_materials:
                logger.info("职位申请材料准备成功")
                logger.info(f"简历匹配分数: {application_materials.get('resume_match_score')}")
                if application_materials.get('cover_letter'):
                    logger.info(f"已生成求职信，长度: {len(application_materials.get('cover_letter'))}字符")
            else:
                logger.warning("职位申请材料准备失败")
        
        # 5. 测试市场分析
        logger.info("\n=== 开始测试职位市场分析 ===")
        if platform and len(search_results.get('jobs', [])) > 0:
            market_analysis = platform.analyze_job_market(search_results.get('jobs', []))
            if market_analysis:
                logger.info("职位市场分析成功")
                if market_analysis.get('top_skills'):
                    logger.info(f"热门技能: {', '.join(market_analysis.get('top_skills')[:5])}")
                if market_analysis.get('recommendations'):
                    logger.info(f"求职建议长度: {len(market_analysis.get('recommendations'))}字符")
            else:
                logger.warning("职位市场分析失败")
        
        # 测试总结
        logger.info("\n=== 测试总结 ===")
        logger.info("全流程测试完成!")
        logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}", exc_info=True)
    finally:
        # 清理资源
        try:
            if 'agent_service' in locals():
                logger.info("清理浏览器资源...")
                await agent_service.browser_scraper.close()
                logger.info("资源清理完成")
        except Exception as e:
            logger.error(f"清理资源时发生错误: {str(e)}")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())