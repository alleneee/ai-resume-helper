"""
主应用程序入口
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
import uvicorn
from typing import Dict, Any, List

# 导入API路由
from server.api import auth, resume, agent, agent_v2
from server.models.database import close_mongo_connection, connect_to_mongo
from server.utils.response import ApiResponse, CustomJSONResponse, HttpExceptionHandler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger(__name__)

# 应用程序生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用程序生命周期管理
    
    在应用程序启动时连接数据库，在应用程序关闭时断开连接
    """
    # 启动时执行
    logger.info("应用程序启动中...")
    
    # 连接到MongoDB
    await connect_to_mongo()
    logger.info("已连接到MongoDB")
    
    # 创建上传目录
    upload_dir = os.path.join(os.getcwd(), "uploads")
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        logger.info(f"已创建上传目录: {upload_dir}")
    
    yield
    
    # 关闭时执行
    logger.info("应用程序关闭中...")
    
    # 关闭MongoDB连接
    await close_mongo_connection()
    logger.info("已关闭MongoDB连接")

# 创建FastAPI应用程序
app = FastAPI(
    title="AI简历助手API",
    description="AI驱动的简历优化和职位匹配系统",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该指定具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误"""
    # 使用HttpExceptionHandler中的方法处理验证错误，确保一致的错误处理
    return await HttpExceptionHandler.validation_exception_handler(request, exc)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """处理全局异常"""
    # 使用HttpExceptionHandler中的方法处理全局异常，确保一致的错误处理
    return await HttpExceptionHandler.internal_exception_handler(request, exc)

# 注册路由
app.include_router(auth.router, prefix="/api")
app.include_router(resume.router, prefix="/api")
app.include_router(agent.router, prefix="/api")
app.include_router(agent_v2.router, prefix="/api")

# 静态文件服务
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 健康检查端点
@app.get("/api/health", tags=["健康检查"])
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "version": app.version}

# 主入口
if __name__ == "__main__":
    uvicorn.run(
        "server.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
