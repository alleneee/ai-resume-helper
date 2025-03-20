import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.config import get_settings


def create_app() -> FastAPI:
    """创建和配置FastAPI应用"""
    settings = get_settings()
    
    # 创建应用
    app = FastAPI(
        title=settings.APP_NAME,
        description="AI简历优化与一键投递系统API",
        version="0.1.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 在生产环境中应该限制为特定的域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # 配置静态文件
    uploads_dir = settings.UPLOAD_DIR
    os.makedirs(uploads_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # 添加全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        if isinstance(exc, HTTPException):
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail}
            )
        return JSONResponse(
            status_code=500,
            content={"detail": f"内部服务器错误: {str(exc)}"}
        )
    
    # 简单的健康检查
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}
    
    return app


app = create_app() 