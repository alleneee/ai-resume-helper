from typing import Optional, Dict, Any
from browser_use import Agent as BrowserAgent, ActionResult, Controller
from browser_use.browser.browser import Browser, BrowserConfig
from config.settings import Settings, get_settings
import logging

logger = logging.getLogger(__name__)

class BrowserScraperService:
    _instance = None
    
    def __init__(self):
        self.settings = get_settings()
        self.controller = Controller()
        browser_settings = self.settings.browser_settings
        self.browser_config = BrowserConfig(
            headless=browser_settings["headless"],
            # 注意：BrowserConfig不支持width、height和timeout参数
            # 这些参数可能需要在其他地方使用
            disable_security=True
        )
        # 保存其他设置供后续使用
        self.browser_width = browser_settings["width"]
        self.browser_height = browser_settings["height"]
        self.browser_timeout = browser_settings["timeout"]
    
    @classmethod
    def get_instance(cls) -> 'BrowserScraperService':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def create_browser_agent(self, task: str, browser: Optional[Dict[str, Any]] = None) -> BrowserAgent:
        """创建浏览器代理"""
        return BrowserAgent(task=task, browser=browser)
    
    async def get_browser(self) -> Browser:
        """获取浏览器实例"""
        return await self.controller.create_browser(config=self.browser_config)
    
    async def close(self):
        """关闭浏览器控制器"""
        await self.controller.close()
    
    async def scrape_job_detail(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """爬取职位详情"""
        task = f"""
        任务目标: 获取职位详细信息
        
        步骤:
        1. 访问职位详情页面: {job['url']}
        2. 等待页面加载完成
        3. 提取以下信息:
           - 职位标题
           - 公司名称
           - 工作地点
           - 薪资范围
           - 职位描述
           - 任职要求
           - 公司信息
        4. 返回JSON格式数据
        """
        
        try:
            async with self.get_browser() as browser:
                agent = await self.create_browser_agent(task=task, browser=browser)
                result = await agent.run()
                
                if result.success:
                    return {**job, **result.data}
                else:
                    logger.error(f"获取职位详情失败: {result.error}")
                    return job
                    
        except Exception as e:
            logger.error(f"爬取职位详情时发生错误: {str(e)}")
            return job
    
    def _extract_json_from_result(self, result: str) -> Dict[str, Any]:
        """从结果文本中提取JSON数据"""
        try:
            # 尝试直接解析JSON
            import json
            return json.loads(result)
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试从文本中提取JSON部分
            import re
            json_pattern = r'\{[\s\S]*\}'
            match = re.search(json_pattern, result)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    logger.error("无法从文本中提取有效的JSON数据")
                    return {}
            return {} 