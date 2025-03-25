"""
智能代理相关的API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Path
from typing import Dict, Any, List, Optional, Annotated
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from datetime import datetime
from bson import ObjectId

from models.database import get_mongo_db
from middleware.auth import AuthMiddleware
from utils.response import ApiResponse, ResponseModel
from services.agent_service import AgentService
from models.agent import (
    ResumeOptimizationRequest, 
    JobMatchRequest, 
    CoverLetterRequest,
    JobSearchRequest,
    AgentResponse
)

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(tags=["智能代理"], prefix="/agent")

@router.post(
    "/optimize-resume", 
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="优化简历",
    description="使用AI分析和优化简历内容"
)
async def optimize_resume(
    request: Annotated[ResumeOptimizationRequest, Body(...)],
    current_user: Annotated[Dict[str, Any], Depends(AuthMiddleware.get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)],
    agent_service: Annotated[AgentService, Depends(AgentService.get_instance)]
):
    """
    优化简历
    
    - **request**: 优化请求，包含简历ID和目标职位
    - 需要认证令牌
    - 返回：优化后的简历内容和建议
    
    可能的错误：
    - 404: 简历不存在
    - 403: 无权访问该简历
    - 400: 请求参数无效
    """
    try:
        logger.info(f"处理简历优化请求: 用户: {current_user.get('email')} - 简历ID: {request.resume_id}")
        
        # 查询简历
        resume = await db.resumes.find_one({"_id": ObjectId(request.resume_id)})
        if not resume:
            logger.warning(f"简历不存在: {request.resume_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="简历不存在"
            )
        
        # 检查权限
        if str(resume["user_id"]) != str(current_user["_id"]):
            logger.warning(f"无权访问简历: {request.resume_id} - 用户: {current_user.get('email')}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问该简历"
            )
        
        # 调用代理服务
        result = await agent_service.optimize_resume(
            resume_id=request.resume_id,
            resume_data=resume,
            job_description=request.job_description,
            user_id=str(current_user["_id"])
        )
        
        # 记录操作日志
        await db.agent_logs.insert_one({
            "user_id": current_user["_id"],
            "action": "optimize_resume",
            "resume_id": request.resume_id,
            "job_description": request.job_description,
            "created_at": datetime.utcnow()
        })
        
        logger.info(f"简历优化成功: {request.resume_id}")
        
        # 返回优化结果
        return ApiResponse.success(
            message="简历优化成功",
            data=result
        )
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"简历优化过程中发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"简历优化失败: {str(e)}"
        )

@router.post(
    "/match-jobs", 
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="职位匹配",
    description="根据简历内容匹配合适的职位"
)
async def match_jobs(
    request: Annotated[JobMatchRequest, Body(...)],
    current_user: Annotated[Dict[str, Any], Depends(AuthMiddleware.get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)],
    agent_service: Annotated[AgentService, Depends(AgentService.get_instance)]
):
    """
    职位匹配
    
    - **request**: 匹配请求，包含简历ID和匹配参数
    - 需要认证令牌
    - 返回：匹配的职位列表
    
    可能的错误：
    - 404: 简历不存在
    - 403: 无权访问该简历
    - 400: 请求参数无效
    """
    try:
        logger.info(f"处理职位匹配请求: 用户: {current_user.get('email')} - 简历ID: {request.resume_id}")
        
        # 查询简历
        resume = await db.resumes.find_one({"_id": ObjectId(request.resume_id)})
        if not resume:
            logger.warning(f"简历不存在: {request.resume_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="简历不存在"
            )
        
        # 检查权限
        if str(resume["user_id"]) != str(current_user["_id"]):
            logger.warning(f"无权访问简历: {request.resume_id} - 用户: {current_user.get('email')}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问该简历"
            )
        
        # 调用代理服务
        result = await agent_service.match_jobs(
            resume_id=request.resume_id,
            resume_data=resume,
            location=request.location,
            job_type=request.job_type,
            keywords=request.keywords,
            limit=request.limit,
            user_id=str(current_user["_id"])
        )
        
        # 记录操作日志
        await db.agent_logs.insert_one({
            "user_id": current_user["_id"],
            "action": "match_jobs",
            "resume_id": request.resume_id,
            "parameters": request.model_dump(exclude={"resume_id"}),
            "created_at": datetime.utcnow()
        })
        
        logger.info(f"职位匹配成功: {request.resume_id} - 找到 {len(result.get('jobs', []))} 个匹配职位")
        
        # 返回匹配结果
        return ApiResponse.success(
            message="职位匹配成功",
            data=result
        )
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"职位匹配过程中发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"职位匹配失败: {str(e)}"
        )

@router.post(
    "/generate-cover-letter", 
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="生成求职信",
    description="根据简历和职位描述生成个性化求职信"
)
async def generate_cover_letter(
    request: Annotated[CoverLetterRequest, Body(...)],
    current_user: Annotated[Dict[str, Any], Depends(AuthMiddleware.get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)],
    agent_service: Annotated[AgentService, Depends(AgentService.get_instance)]
):
    """
    生成求职信
    
    - **request**: 求职信请求，包含简历ID、职位描述和公司信息
    - 需要认证令牌
    - 返回：生成的求职信内容
    
    可能的错误：
    - 404: 简历不存在
    - 403: 无权访问该简历
    - 400: 请求参数无效
    """
    try:
        logger.info(f"处理求职信生成请求: 用户: {current_user.get('email')} - 简历ID: {request.resume_id}")
        
        # 查询简历
        resume = await db.resumes.find_one({"_id": ObjectId(request.resume_id)})
        if not resume:
            logger.warning(f"简历不存在: {request.resume_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="简历不存在"
            )
        
        # 检查权限
        if str(resume["user_id"]) != str(current_user["_id"]):
            logger.warning(f"无权访问简历: {request.resume_id} - 用户: {current_user.get('email')}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问该简历"
            )
        
        # 调用代理服务
        result = await agent_service.generate_cover_letter(
            resume_id=request.resume_id,
            resume_data=resume,
            job_description=request.job_description,
            company_name=request.company_name,
            company_info=request.company_info,
            tone=request.tone,
            user_id=str(current_user["_id"])
        )
        
        # 记录操作日志
        await db.agent_logs.insert_one({
            "user_id": current_user["_id"],
            "action": "generate_cover_letter",
            "resume_id": request.resume_id,
            "parameters": request.model_dump(exclude={"resume_id"}),
            "created_at": datetime.utcnow()
        })
        
        logger.info(f"求职信生成成功: {request.resume_id}")
        
        # 返回生成结果
        return ApiResponse.success(
            message="求职信生成成功",
            data=result
        )
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"求职信生成过程中发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"求职信生成失败: {str(e)}"
        )

@router.post(
    "/search-jobs", 
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="搜索职位",
    description="根据关键词和筛选条件搜索职位"
)
async def search_jobs(
    request: Annotated[JobSearchRequest, Body(...)],
    current_user: Annotated[Dict[str, Any], Depends(AuthMiddleware.get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)],
    agent_service: Annotated[AgentService, Depends(AgentService.get_instance)]
):
    """
    搜索职位
    
    - **request**: 搜索请求，包含关键词和筛选条件
    - 需要认证令牌
    - 返回：搜索到的职位列表
    
    可能的错误：
    - 400: 请求参数无效
    """
    try:
        logger.info(f"处理职位搜索请求: 用户: {current_user.get('email')} - 关键词: {request.keywords}")
        
        # 调用代理服务
        result = await agent_service.search_jobs(
            keywords=request.keywords,
            location=request.location,
            job_type=request.job_type,
            experience_level=request.experience_level,
            salary_min=request.salary_min,
            salary_max=request.salary_max,
            page=request.page,
            limit=request.limit,
            user_id=str(current_user["_id"])
        )
        
        # 记录操作日志
        await db.agent_logs.insert_one({
            "user_id": current_user["_id"],
            "action": "search_jobs",
            "parameters": request.model_dump(),
            "created_at": datetime.utcnow()
        })
        
        logger.info(f"职位搜索成功: 关键词: {request.keywords} - 找到 {len(result.get('jobs', []))} 个职位")
        
        # 返回搜索结果
        return ApiResponse.success(
            message="职位搜索成功",
            data=result
        )
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"职位搜索过程中发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"职位搜索失败: {str(e)}"
        )

@router.get("/jobs", response_model=Dict[str, Any])
async def search_jobs(
    job_title: str = Query(..., description="职位标题"),
    location: Optional[str] = Query(None, description="位置"),
    count: int = Query(5, description="结果数量"),
    current_user: Dict[str, Any] = Depends(AuthMiddleware.get_current_user)
):
    """
    搜索职位列表
    
    Args:
        job_title: 职位标题
        location: 位置
        count: 结果数量
        current_user: 当前用户信息
        
    Returns:
        职位列表
    """
    try:
        # 验证必要参数
        if not job_title:
            return ApiResponse.validation_error(message="jobTitle 查询参数是必需的")
        
        # 调用爬虫Agent获取职位列表
        result = await agent_service.run({
            "action": "search",
            "jobTitle": job_title,
            "location": location,
            "count": count,
            "userId": str(current_user["_id"])
        })
        
        return ApiResponse.success(
            message="职位搜索成功",
            data=result
        )
    except Exception as e:
        return ApiResponse.error(message=f"职位搜索失败: {str(e)}")

@router.get("/jobs/{job_id}", response_model=Dict[str, Any])
async def get_job_details(
    job_id: str = Path(..., description="职位ID"),
    current_user: Dict[str, Any] = Depends(AuthMiddleware.get_current_user)
):
    """
    获取职位详情
    
    Args:
        job_id: 职位ID
        current_user: 当前用户信息
        
    Returns:
        职位详情
    """
    try:
        if not job_id:
            return ApiResponse.validation_error(message="jobId 参数是必需的")
        
        # 调用爬虫Agent获取职位详情
        result = await agent_service.run({
            "action": "details",
            "jobId": job_id,
            "userId": str(current_user["_id"])
        })
        
        return ApiResponse.success(
            message="获取职位详情成功",
            data=result
        )
    except Exception as e:
        return ApiResponse.error(message=f"获取职位详情失败: {str(e)}")

@router.post("/analyze-resume", response_model=Dict[str, Any])
async def analyze_resume(
    request_data: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(AuthMiddleware.get_current_user)
):
    """
    分析简历与职位匹配度
    
    Args:
        request_data: 请求数据，包含resumeId, jobId
        current_user: 当前用户信息
        
    Returns:
        分析结果
    """
    try:
        resume_id = request_data.get("resumeId")
        job_id = request_data.get("jobId")
        
        # 验证必要参数
        if not resume_id:
            return ApiResponse.validation_error(message="resumeId 是必需的")
        
        if not job_id:
            return ApiResponse.validation_error(message="jobId 是必需的")
        
        # 1. 获取简历数据
        resume_data = await agent_service.run({
            "action": "get_resume",
            "resumeId": resume_id,
            "userId": str(current_user["_id"])
        })
        
        # 2. 获取职位详情
        job_data = await agent_service.run({
            "action": "details",
            "jobId": job_id,
            "userId": str(current_user["_id"])
        })
        
        # 3. 分析匹配度
        result = await agent_service.run({
            "action": "analyze_resume",
            "resumeData": resume_data,
            "jobData": job_data,
            "userId": str(current_user["_id"])
        })
        
        return ApiResponse.success(
            message="简历分析成功",
            data=result
        )
    except Exception as e:
        return ApiResponse.error(message=f"简历分析失败: {str(e)}")
