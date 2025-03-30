"""
API路由入口模块
"""
from fastapi import APIRouter
from server.api.auth import router as auth_router
from server.api.agent import router as agent_router
from server.api.resume import router as resume_router

def get_api_router():
    """
    获取API路由集合
    
    Returns:
        包含所有API路由的主路由
    """
    router = APIRouter()
    
    # 注册各个模块的路由
    router.include_router(auth_router, prefix="/auth", tags=["认证"])
    router.include_router(resume_router, prefix="/resume", tags=["简历"])
    router.include_router(agent_router, prefix="/agent", tags=["智能代理"])
    
    return router
