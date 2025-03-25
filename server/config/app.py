"""
应用配置和初始化
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from contextlib import asynccontextmanager
import logging

from .settings import get_settings, Settings
from server.utils.response import ApiResponse, register_exception_handlers

# 配置日志
logger = logging.getLogger(__name__)

# 创建API速率限制器
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理器
    
    负责应用启动和关闭时的资源初始化和清理
    
    Args:
        app: FastAPI应用实例
    """
    # 应用启动时执行
    logger.info("应用正在启动...")
    
    # 在这里可以添加资源初始化逻辑
    # 例如连接数据库、初始化缓存等
    
    yield  # 应用运行期间
    
    # 应用关闭时执行
    logger.info("应用正在关闭...")
    
    # 在这里可以添加资源清理逻辑
    # 例如关闭数据库连接、释放资源等
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        logger.info("MongoDB连接已关闭")

def create_app() -> FastAPI:
    """
    创建并配置FastAPI应用
    
    Returns:
        FastAPI: 配置好的FastAPI应用实例
    """
    settings = get_settings()
    
    # 创建FastAPI应用
    app = FastAPI(
        title="AI简历助手API",
        description="提供简历优化、职位匹配和求职信生成等功能的API",
        version="1.0.0",
        debug=settings.DEBUG,
        lifespan=lifespan
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 配置受信任主机
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["*"] if settings.is_development else [settings.SERVER_HOST]
    )
    
    # 配置速率限制
    if settings.RATE_LIMIT_ENABLED:
        app.state.limiter = limiter
        app.add_middleware(SlowAPIMiddleware)
    
    # 注册全局异常处理器
    register_exception_handlers(app)
    
    # 注册速率限制异常处理器
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        """速率限制异常处理器"""
        request_id = request.headers.get("X-Request-ID")
        return ApiResponse.rate_limit(
            message="请求过于频繁，请稍后再试",
            retry_after=getattr(exc, "retry_after", 60),
            request_id=request_id
        )
    
    return app


# MongoDB客户端单例
mongodb_client = None

async def get_db() -> AsyncIOMotorDatabase:
    """
    数据库连接依赖
    
    Yields:
        AsyncIOMotorDatabase: MongoDB数据库连接
    """
    global mongodb_client
    settings = get_settings()
    
    # 懒加载MongoDB客户端
    if mongodb_client is None:
        mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
        logger.info("MongoDB连接已初始化")
    
    return mongodb_client[settings.MONGODB_DB]

async def get_settings_async() -> Settings:
    """
    异步获取应用配置
    
    用于依赖注入
    
    Returns:
        Settings: 应用配置实例
    """
    return get_settings()
