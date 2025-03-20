import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=config.PROJECT_NAME,
    description="AI驱动的简历优化与职位匹配服务",
    version=config.VERSION,
    docs_url=f"{config.API_PREFIX}/docs",
    redoc_url=f"{config.API_PREFIX}/redoc",
    openapi_url=f"{config.API_PREFIX}/openapi.json",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入API路由
from api.resume import router as resume_router
from api.jobs import router as jobs_router

# 注册API路由
app.include_router(resume_router, prefix=f"{config.API_PREFIX}/resume")
app.include_router(jobs_router, prefix=f"{config.API_PREFIX}/jobs")

@app.get("/")
async def root():
    return {"message": "Welcome to AI Resume Helper API"}

@app.get(f"{config.API_PREFIX}/health")
async def health_check():
    return {
        "status": "healthy",
        "version": config.VERSION,
        "environment": "development" if config.DEBUG else "production"
    }

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting {config.PROJECT_NAME} API server")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower(),
    )
