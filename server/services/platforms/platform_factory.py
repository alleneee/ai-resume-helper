"""
招聘平台工厂类，用于创建和管理不同的招聘平台适配器
"""
import logging
from typing import Dict, Type, List, Optional, Any

from server.services.platforms.base_platform import BasePlatform
from server.services.platforms.boss_platform import BossPlatform
from server.services.agent_service import BrowserScraperService

logger = logging.getLogger(__name__)

class PlatformFactory:
    """招聘平台工厂类"""
    
    # 平台类映射
    _platform_classes = {
        "boss": BossPlatform,
        # 以下为待实现的平台
        # "lagou": LagouPlatform,  
        # "zhilian": ZhilianPlatform,
        # "51job": Job51Platform,
    }
    
    def __init__(self, browser_scraper: BrowserScraperService):
        """
        初始化平台工厂
        
        Args:
            browser_scraper: 浏览器爬虫服务实例
        """
        self.browser_scraper = browser_scraper
        self._platform_instances = {}
    
    def get_platform(self, platform_name: str) -> Optional[BasePlatform]:
        """
        获取平台实例
        
        Args:
            platform_name: 平台名称
            
        Returns:
            平台实例
        """
        # 规范化平台名称
        platform_name = platform_name.lower()
        
        # 检查是否已创建实例
        if platform_name in self._platform_instances:
            return self._platform_instances[platform_name]
        
        # 检查是否支持该平台
        if platform_name not in self._platform_classes:
            logger.warning(f"不支持的平台: {platform_name}")
            return None
        
        # 创建平台实例
        try:
            platform_class = self._platform_classes[platform_name]
            platform = platform_class(self.browser_scraper)
            self._platform_instances[platform_name] = platform
            logger.info(f"创建平台实例: {platform_name}")
            return platform
        except Exception as e:
            logger.error(f"创建平台实例失败: {platform_name}, 错误: {str(e)}")
            return None
    
    def get_all_platforms(self) -> List[BasePlatform]:
        """
        获取所有支持的平台实例
        
        Returns:
            平台实例列表
        """
        platforms = []
        for platform_name in self._platform_classes.keys():
            platform = self.get_platform(platform_name)
            if platform:
                platforms.append(platform)
        return platforms
    
    @classmethod
    def register_platform(cls, name: str, platform_class: Type[BasePlatform]) -> None:
        """
        注册新的平台类
        
        Args:
            name: 平台名称
            platform_class: 平台类
        """
        cls._platform_classes[name.lower()] = platform_class
        logger.info(f"注册平台类: {name}")
    
    def search_all_platforms(self, keywords: List[str], **params) -> Dict[str, List[Dict[str, Any]]]:
        """
        在所有支持的平台上搜索职位
        
        Args:
            keywords: 搜索关键词
            params: 其他搜索参数
            
        Returns:
            各平台的搜索结果
        """
        # 这里实现的是一个同步版本，实际使用时应该使用异步版本
        results = {}
        for platform_name in self._platform_classes.keys():
            platform = self.get_platform(platform_name)
            if not platform:
                continue
                
            try:
                platform_results = platform.search_jobs(keywords, **params)
                results[platform_name] = platform_results
            except Exception as e:
                logger.error(f"平台搜索失败: {platform_name}, 错误: {str(e)}")
                results[platform_name] = []
                
        return results 