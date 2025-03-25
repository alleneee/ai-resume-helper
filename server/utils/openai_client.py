"""
OpenAI客户端工具类

提供全局可用的OpenAI客户端实例，使用依赖注入模式
"""
import logging
import os
from functools import lru_cache
from typing import Optional

from openai import OpenAI, AsyncOpenAI
from openai_agents import AgentsApi, OpenAICredentials

from config.settings import get_settings, Settings

# 配置日志
logger = logging.getLogger(__name__)

class OpenAIClientManager:
    """OpenAI客户端管理器"""
    
    _instance = None
    _sync_client: Optional[OpenAI] = None
    _async_client: Optional[AsyncOpenAI] = None
    _agents_client: Optional[AgentsApi] = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(OpenAIClientManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, api_key: str = None, organization: str = None):
        """初始化OpenAI客户端"""
        if not self._initialized:
            self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
            self._organization = organization or os.environ.get("OPENAI_ORGANIZATION")
            
            if not self._api_key:
                logger.warning("未设置OPENAI_API_KEY")
            
            # 初始化客户端
            self._init_clients()
            self._initialized = True
    
    def _init_clients(self):
        """初始化所有客户端"""
        try:
            # 同步客户端
            self._sync_client = OpenAI(
                api_key=self._api_key,
                organization=self._organization
            )
            
            # 异步客户端
            self._async_client = AsyncOpenAI(
                api_key=self._api_key,
                organization=self._organization
            )
            
            # 代理客户端
            self._agents_client = AgentsApi(
                credentials=OpenAICredentials(
                    api_key=self._api_key,
                    organization_id=self._organization
                )
            )
            
            logger.info("OpenAI客户端初始化成功")
        except Exception as e:
            logger.error(f"OpenAI客户端初始化失败: {str(e)}")
            raise
    
    @property
    def client(self) -> OpenAI:
        """获取同步客户端"""
        if not self._sync_client:
            self._init_clients()
        return self._sync_client
    
    @property
    def async_client(self) -> AsyncOpenAI:
        """获取异步客户端"""
        if not self._async_client:
            self._init_clients()
        return self._async_client
    
    @property
    def agents_client(self) -> AgentsApi:
        """获取代理客户端"""
        if not self._agents_client:
            self._init_clients()
        return self._agents_client
    
    def reset_clients(self, api_key: str = None, organization: str = None):
        """重置客户端实例"""
        self._api_key = api_key or self._api_key
        self._organization = organization or self._organization
        self._init_clients()
        logger.info("OpenAI客户端已重置")

@lru_cache()
def get_openai_client(settings: Settings = None) -> OpenAIClientManager:
    """
    获取OpenAI客户端管理器实例
    
    使用lru_cache确保只创建一个实例
    
    Args:
        settings: 应用配置
        
    Returns:
        OpenAIClientManager: OpenAI客户端管理器实例
    """
    if settings is None:
        settings = get_settings()
    
    return OpenAIClientManager(
        api_key=settings.openai_api_key,
        organization=settings.openai_organization
    )

def get_openai_sync_client(settings: Settings = None) -> OpenAI:
    """
    获取OpenAI同步客户端
    
    Args:
        settings: 应用配置
        
    Returns:
        OpenAI: OpenAI同步客户端
    """
    return get_openai_client(settings).client

def get_openai_async_client(settings: Settings = None) -> AsyncOpenAI:
    """
    获取OpenAI异步客户端
    
    Args:
        settings: 应用配置
        
    Returns:
        AsyncOpenAI: OpenAI异步客户端
    """
    return get_openai_client(settings).async_client

def get_openai_agents_client(settings: Settings = None) -> AgentsApi:
    """
    获取OpenAI代理客户端
    
    Args:
        settings: 应用配置
        
    Returns:
        AgentsApi: OpenAI代理API客户端
    """
    return get_openai_client(settings).agents_client
