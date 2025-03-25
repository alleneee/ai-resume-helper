"""
MongoDB连接模块
提供异步MongoDB连接和依赖注入功能
"""
import os
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from fastapi import Depends
import logging
from functools import lru_cache

# 配置日志
logger = logging.getLogger(__name__)

# MongoDB连接配置
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://host.docker.internal:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "ai_resume_helper")

# 全局客户端实例，使用单例模式
_mongo_client: Optional[AsyncIOMotorClient] = None

@lru_cache()
def get_mongodb_settings() -> Dict[str, Any]:
    """
    获取MongoDB连接设置，使用lru_cache缓存结果
    """
    return {
        "url": MONGODB_URL,
        "db_name": MONGODB_DB_NAME
    }

async def get_mongo_client() -> AsyncIOMotorClient:
    """
    获取MongoDB客户端实例，使用单例模式
    """
    global _mongo_client
    
    if _mongo_client is None:
        settings = get_mongodb_settings()
        logger.info(f"创建MongoDB连接: {settings['url']}")
        
        # 创建异步客户端
        _mongo_client = AsyncIOMotorClient(
            settings["url"],
            maxPoolSize=10,  # 连接池大小
            minPoolSize=1,   # 最小连接数
            serverSelectionTimeoutMS=5000,  # 服务器选择超时
            connectTimeoutMS=5000,  # 连接超时
            socketTimeoutMS=30000,  # 套接字超时
            retryWrites=True,  # 重试写入
            w="majority"  # 写入确认级别
        )
        
        # 验证连接
        try:
            await _mongo_client.admin.command("ping")
            logger.info("MongoDB连接成功")
        except ConnectionFailure as e:
            logger.error(f"MongoDB连接失败: {str(e)}")
            raise
    
    return _mongo_client

async def get_db():
    """
    获取数据库实例，用于依赖注入
    """
    settings = get_mongodb_settings()
    client = await get_mongo_client()
    return client[settings["db_name"]]

async def close_mongo_connection():
    """
    关闭MongoDB连接，用于应用关闭时清理资源
    """
    global _mongo_client
    
    if _mongo_client is not None:
        logger.info("关闭MongoDB连接")
        _mongo_client.close()
        _mongo_client = None

# 用于FastAPI依赖注入的函数
async def get_db_dependency():
    """
    用于FastAPI依赖注入的数据库获取函数
    使用方法: db = Depends(get_db_dependency)
    """
    db = await get_db()
    try:
        yield db
    finally:
        # 这里不需要关闭连接，因为我们使用连接池
        pass

# 应用启动和关闭事件处理
def setup_mongodb_events(app):
    """
    设置FastAPI应用的MongoDB事件处理
    """
    @app.on_event("startup")
    async def startup_db_client():
        """应用启动时连接MongoDB"""
        await get_mongo_client()
    
    @app.on_event("shutdown")
    async def shutdown_db_client():
        """应用关闭时断开MongoDB连接"""
        await close_mongo_connection()
