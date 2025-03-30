"""
智能代理相关的API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Path, Request
from typing import Dict, Any, Annotated, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from datetime import datetime
from bson import ObjectId
from functools import lru_cache
import uuid

from server.models.database import get_mongo_db
from server.middleware.auth import AuthMiddleware, get_current_user
from server.utils.response import (
    ApiResponse, 
    ResponseModel, 
    PaginatedResponseModel,
    ErrorDetail,
    create_http_exception
)
from server.services.agent_service import AgentService
from server.config.settings import get_settings, Settings
from server.models.agent import (
    ResumeOptimizationRequest, 
    JobMatchRequest, 
    CoverLetterRequest,
    JobSearchRequest,
    AgentResponse,
    JobSearchResult,
    JobItem,
    JobDetail
)

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(tags=["智能代理"], prefix="/agent")

# 依赖函数：获取AgentService实例
@lru_cache()
def get_agent_service(settings: Annotated[Settings, Depends(get_settings)]) -> AgentService:
    """
    获取AgentService实例的依赖函数
    
    使用lru_cache确保只创建一个实例，提高性能
    
    Returns:
        AgentService: 代理服务实例
    """
    return AgentService.get_instance(settings)

# 依赖函数：获取请求ID
def get_request_id(request: Request) -> str:
    """
    获取或生成请求ID
    
    如果请求头中已有X-Request-ID，则使用该值；否则生成新的UUID
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        str: 请求ID
    """
    return request.headers.get("X-Request-ID", str(uuid.uuid4()))

@router.post(
    "/optimize-resume", 
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="优化简历",
    description="使用AI分析和优化简历内容",
    responses={
        200: {"description": "简历优化成功"},
        400: {"description": "请求参数无效"},
        403: {"description": "无权访问该简历"},
        404: {"description": "简历不存在"}
    }
)
async def optimize_resume(
    request: Annotated[ResumeOptimizationRequest, Body(description="优化请求参数")],
    current_user: Annotated[Dict[str, Any], Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)],
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
    request_id: str = Depends(get_request_id)
):
    """
    优化简历
    
    使用AI分析职位描述和简历内容，生成针对特定职位的简历优化建议
    
    Args:
        request: 优化请求，包含简历ID和目标职位描述
        current_user: 当前登录用户信息
        db: MongoDB数据库连接
        agent_service: 智能代理服务实例
        request_id: 请求ID
    
    Returns:
        CustomJSONResponse: 优化后的简历内容和建议
    """
    logger.info(f"处理简历优化请求: 用户: {current_user.get('email')} - 简历ID: {request.resume_id} - 请求ID: {request_id}")
    
    try:
        # 查询简历
        resume = await db.resumes.find_one({"_id": ObjectId(request.resume_id)})
        if not resume:
            logger.warning(f"简历不存在: {request.resume_id} - 请求ID: {request_id}")
            return ApiResponse.not_found(
                message="简历不存在",
                resource="简历",
                request_id=request_id
            )
        
        # 检查权限
        if str(resume["user_id"]) != str(current_user["_id"]):
            logger.warning(f"无权访问简历: {request.resume_id} - 用户: {current_user.get('email')} - 请求ID: {request_id}")
            return ApiResponse.forbidden(
                message="无权访问该简历",
                request_id=request_id
            )
        
        # 调用优化服务
        response = await agent_service.optimize_resume(
            resume_content=resume.get("content", ""),
            job_description=request.job_description,
            options=request.options
        )
        
        # 记录优化历史
        history = {
            "user_id": ObjectId(current_user["_id"]),
            "resume_id": ObjectId(request.resume_id),
            "job_description": request.job_description,
            "original_content": resume.get("content", ""),
            "optimized_content": response.optimized_content,
            "suggestions": response.suggestions,
            "created_at": datetime.utcnow(),
            "request_id": request_id
        }
        await db.resume_optimizations.insert_one(history)
        
        logger.info(f"简历优化成功: {request.resume_id} - 请求ID: {request_id}")
        return ApiResponse.success(
            message="简历优化成功",
            data=response.model_dump(),
            request_id=request_id
        )
    
    except Exception as e:
        logger.exception(f"简历优化失败: {str(e)} - 请求ID: {request_id}")
        if "AI服务" in str(e) or "LLM" in str(e):
            return ApiResponse.ai_service_error(
                message=f"AI服务调用失败: {str(e)}",
                request_id=request_id
            )
        return ApiResponse.server_error(
            message="简历优化处理失败",
            exc=e,
            request_id=request_id
        )

@router.post(
    "/match-jobs", 
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="职位匹配",
    description="根据简历内容匹配合适的职位",
    responses={
        200: {"description": "职位匹配成功"},
        400: {"description": "请求参数无效"},
        403: {"description": "无权访问该简历"},
        404: {"description": "简历不存在"}
    }
)
async def match_jobs(
    request: Annotated[JobMatchRequest, Body(description="匹配请求参数")],
    current_user: Annotated[Dict[str, Any], Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)],
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
    request_id: str = Depends(get_request_id)
):
    """
    职位匹配
    
    根据简历内容匹配合适的职位
    
    Args:
        request: 匹配请求，包含简历ID和匹配参数
        current_user: 当前登录用户信息
        db: MongoDB数据库连接
        agent_service: 智能代理服务实例
        request_id: 请求ID
    
    Returns:
        CustomJSONResponse: 匹配的职位列表
    """
    logger.info(f"处理职位匹配请求: 用户: {current_user.get('email')} - 简历ID: {request.resume_id} - 请求ID: {request_id}")
    
    try:
        # 查询简历
        resume = await db.resumes.find_one({"_id": ObjectId(request.resume_id)})
        if not resume:
            logger.warning(f"简历不存在: {request.resume_id} - 请求ID: {request_id}")
            return ApiResponse.not_found(
                message="简历不存在",
                resource="简历",
                request_id=request_id
            )
        
        # 检查权限
        if str(resume["user_id"]) != str(current_user["_id"]):
            logger.warning(f"无权访问简历: {request.resume_id} - 用户: {current_user.get('email')} - 请求ID: {request_id}")
            return ApiResponse.forbidden(
                message="无权访问该简历",
                request_id=request_id
            )
        
        # 调用匹配服务
        matches = await agent_service.match_jobs(
            resume_content=resume.get("content", ""),
            location=request.location,
            job_type=request.job_type,
            experience_level=request.experience_level,
            count=request.count
        )
        
        # 记录匹配历史
        history = {
            "user_id": ObjectId(current_user["_id"]),
            "resume_id": ObjectId(request.resume_id),
            "filters": request.model_dump(exclude={"resume_id"}),
            "matches": [match.model_dump() for match in matches],
            "created_at": datetime.utcnow(),
            "request_id": request_id
        }
        await db.job_matches.insert_one(history)
        
        logger.info(f"职位匹配成功: {request.resume_id} - 找到职位: {len(matches)} - 请求ID: {request_id}")
        return ApiResponse.success(
            message="职位匹配成功",
            data=[job.model_dump() for job in matches],
            request_id=request_id
        )
    
    except Exception as e:
        logger.exception(f"职位匹配失败: {str(e)} - 请求ID: {request_id}")
        if "API请求失败" in str(e) or "超过调用限制" in str(e):
            return ApiResponse.ai_service_error(
                message=f"职位搜索服务调用失败: {str(e)}",
                request_id=request_id
            )
        return ApiResponse.server_error(
            message="职位匹配处理失败",
            exc=e,
            request_id=request_id
        )

@router.post(
    "/generate-cover-letter", 
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="生成求职信",
    description="根据简历和职位描述生成个性化求职信",
    responses={
        200: {"description": "求职信生成成功"},
        400: {"description": "请求参数无效"},
        403: {"description": "无权访问该简历"},
        404: {"description": "简历不存在"}
    }
)
async def generate_cover_letter(
    request: Annotated[CoverLetterRequest, Body(description="求职信请求参数")],
    current_user: Annotated[Dict[str, Any], Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)],
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
    request_id: str = Depends(get_request_id)
):
    """
    生成求职信
    
    根据简历和职位描述生成个性化求职信
    
    Args:
        request: 求职信请求，包含简历ID、职位描述和公司信息
        current_user: 当前登录用户信息
        db: MongoDB数据库连接
        agent_service: 智能代理服务实例
        request_id: 请求ID
    
    Returns:
        CustomJSONResponse: 生成的求职信内容
    """
    logger.info(f"处理求职信生成请求: 用户: {current_user.get('email')} - 简历ID: {request.resume_id} - 请求ID: {request_id}")
    
    try:
        # 查询简历
        resume = await db.resumes.find_one({"_id": ObjectId(request.resume_id)})
        if not resume:
            logger.warning(f"简历不存在: {request.resume_id} - 请求ID: {request_id}")
            return ApiResponse.not_found(
                message="简历不存在",
                resource="简历",
                request_id=request_id
            )
        
        # 检查权限
        if str(resume["user_id"]) != str(current_user["_id"]):
            logger.warning(f"无权访问简历: {request.resume_id} - 用户: {current_user.get('email')} - 请求ID: {request_id}")
            return ApiResponse.forbidden(
                message="无权访问该简历",
                request_id=request_id
            )
        
        # 调用求职信服务
        cover_letter = await agent_service.generate_cover_letter(
            resume_content=resume.get("content", ""),
            job_description=request.job_description,
            company_name=request.company_name,
            company_info=request.company_info,
            recipient_name=request.recipient_name,
            recipient_title=request.recipient_title,
            style=request.style
        )
        
        # 记录生成历史
        history = {
            "user_id": ObjectId(current_user["_id"]),
            "resume_id": ObjectId(request.resume_id),
            "job_description": request.job_description,
            "company_name": request.company_name,
            "company_info": request.company_info,
            "style": request.style,
            "cover_letter": cover_letter.content,
            "created_at": datetime.utcnow(),
            "request_id": request_id
        }
        await db.cover_letters.insert_one(history)
        
        logger.info(f"求职信生成成功: {request.resume_id} - 请求ID: {request_id}")
        return ApiResponse.success(
            message="求职信生成成功",
            data=cover_letter.model_dump(),
            request_id=request_id
        )
    
    except Exception as e:
        logger.exception(f"求职信生成失败: {str(e)} - 请求ID: {request_id}")
        if "AI服务" in str(e) or "LLM" in str(e):
            return ApiResponse.ai_service_error(
                message=f"AI服务调用失败: {str(e)}",
                request_id=request_id
            )
        return ApiResponse.server_error(
            message="求职信生成处理失败",
            exc=e,
            request_id=request_id
        )

@router.post(
    "/search-jobs", 
    response_model=PaginatedResponseModel,
    status_code=status.HTTP_200_OK,
    summary="搜索职位",
    description="根据关键词和筛选条件搜索职位",
    responses={
        200: {"description": "职位搜索成功"},
        400: {"description": "请求参数无效"}
    }
)
async def search_jobs(
    request: Annotated[JobSearchRequest, Body(description="职位搜索请求参数")],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    agent_service: AgentService = Depends(get_agent_service),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(10, ge=1, le=50, description="每页数量"),
    request_id: str = Depends(get_request_id)
):
    """
    搜索职位
    
    根据关键词、地点、职位类型、经验水平、学历要求、薪资范围、公司规模和融资阶段等条件搜索职位
    
    Args:
        request: 职位搜索请求，包含关键词和筛选条件
        current_user: 当前登录用户信息
        db: MongoDB数据库连接
        agent_service: 智能代理服务实例
        page: 页码
        limit: 每页数量
        request_id: 请求ID
    
    Returns:
        JobSearchResult: 职位搜索结果
    
    Raises:
        HTTPException: 
            - 400: 请求参数无效
    """
    logger.info(f"处理职位搜索请求: 用户: {current_user.get('email')} - 关键词: {request.keywords} - 请求ID: {request_id}")
    
    try:
        # 调用搜索职位方法
        result = await agent_service.search_jobs(
            keywords=request.keywords,
            location=request.location,
            job_type=request.job_type.value if request.job_type else None,
            experience_level=request.experience_level.value if request.experience_level else None,
            education_level=request.education_level.value if request.education_level else None,
            salary_min=request.salary_min,
            salary_max=request.salary_max,
            company_size=request.company_size.value if request.company_size else None,
            funding_stage=request.funding_stage.value if request.funding_stage else None,
            page=page,
            limit=limit,
            user_id=str(current_user["_id"]),
            db=db,  # 传递数据库连接，用于存储爬取的岗位信息
            request_id=request_id
        )
        
        # 构建响应
        jobs = []
        for job_data in result.get("jobs", []):
            # 创建JobItem对象
            job = JobItem(
                id=job_data.get("id", ""),
                title=job_data.get("title", ""),
                company=job_data.get("company", ""),
                location=job_data.get("location", ""),
                description=job_data.get("description", ""),
                salary=job_data.get("salary", ""),
                url=job_data.get("url", ""),
                job_type=job_data.get("job_type", ""),
                posted_date=job_data.get("posted_date", ""),
                match_score=job_data.get("match_score", 0.0),
                experience_level=job_data.get("experience_level", ""),
                education_level=job_data.get("education_level", ""),
                company_size=job_data.get("company_size", ""),
                funding_stage=job_data.get("funding_stage", ""),
                company_description=job_data.get("company_description", "")
            )
            jobs.append(job)
        
        # 返回响应
        return ApiResponse.paginated(
            items=[job.model_dump() for job in jobs],
            total=result.get("total", 0),
            page=page,
            limit=limit,
            message="职位搜索成功",
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"搜索职位失败: {str(e)} - 请求ID: {request_id}")
        raise HTTPException(status_code=500, detail=f"搜索职位失败: {str(e)}")

@router.get("/search-jobs-by-title", response_model=ResponseModel)
async def search_jobs_by_title(
    current_user: Dict[str, Any] = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
    job_title: str = Query(..., description="职位标题"),
    location: Optional[str] = Query(None, description="位置"),
    count: int = Query(5, description="结果数量"),
    request_id: str = Depends(get_request_id)
):
    """
    搜索职位列表
    
    Args:
        job_title: 职位标题
        location: 位置
        count: 结果数量
        current_user: 当前用户信息
        agent_service: 智能代理服务实例
        request_id: 请求ID
        
    Returns:
        CustomJSONResponse: 职位列表
    """
    logger.info(f"处理职位标题搜索请求: 用户: {current_user.get('email')} - 标题: {job_title} - 请求ID: {request_id}")
    
    try:
        # 调用搜索服务
        jobs = await agent_service.quick_search_jobs(
            job_title=job_title,
            location=location,
            count=count
        )
        
        logger.info(f"职位标题搜索成功: 标题: {job_title} - 找到职位: {len(jobs)} - 请求ID: {request_id}")
        return ApiResponse.success(
            message="职位搜索成功",
            data=[job.model_dump() for job in jobs],
            request_id=request_id
        )
    
    except Exception as e:
        logger.exception(f"职位标题搜索失败: {str(e)} - 请求ID: {request_id}")
        if "API请求失败" in str(e) or "超过调用限制" in str(e):
            return ApiResponse.ai_service_error(
                message=f"职位搜索服务调用失败: {str(e)}",
                request_id=request_id
            )
        return ApiResponse.server_error(
            message="职位搜索处理失败",
            exc=e,
            request_id=request_id
        )

@router.get(
    "/job/{job_id}", 
    response_model=JobDetail,
    status_code=status.HTTP_200_OK,
    summary="获取职位详情",
    description="根据职位ID获取详细信息",
    responses={
        200: {"description": "获取职位成功"},
        404: {"description": "职位不存在"}
    }
)
async def get_job_details(
    current_user: Dict[str, Any] = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
    job_id: str = Path(..., description="职位ID"),
    request_id: str = Depends(get_request_id)
) -> JobDetail:
    """
    获取职位详情
    
    Args:
        job_id: 职位ID
        current_user: 当前用户信息
        agent_service: 智能代理服务实例
        request_id: 请求ID
        
    Returns:
        JobDetail: 职位详情Pydantic模型
    """
    logger.info(f"处理获取职位详情请求: 用户: {current_user.get('email')} - 职位ID: {job_id} - 请求ID: {request_id}")
    
    try:
        # 调用详情服务
        job = await agent_service.get_job_details(job_id)
        
        if not job:
            logger.warning(f"职位不存在: {job_id} - 请求ID: {request_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="职位不存在"
            )
            
        return job
    except Exception as e:
        logger.error(f"获取职位详情失败: {str(e)} - 请求ID: {request_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取职位详情失败"
        )

@router.post(
    "/analyze-resume", 
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="分析简历与职位匹配度",
    description="分析简历内容与特定职位的匹配程度",
    responses={
        200: {"description": "分析成功"},
        400: {"description": "请求参数无效"},
        403: {"description": "无权访问该简历"},
        404: {"description": "简历或职位不存在"}
    }
)
async def analyze_resume(
    current_user: Dict[str, Any] = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
    request_data: Dict[str, Any] = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    request_id: str = Depends(get_request_id)
):
    """
    分析简历与职位匹配度
    
    Args:
        request_data: 请求数据，包含resumeId, jobId
        current_user: 当前用户信息
        agent_service: 智能代理服务实例
        db: MongoDB数据库连接
        request_id: 请求ID
        
    Returns:
        CustomJSONResponse: 分析结果
    """
    resume_id = request_data.get("resumeId")
    job_id = request_data.get("jobId")
    
    if not resume_id or not job_id:
        return ApiResponse.validation_error(
            message="请求参数无效",
            errors=[
                {"field": "resumeId" if not resume_id else None, "message": "简历ID不能为空"},
                {"field": "jobId" if not job_id else None, "message": "职位ID不能为空"}
            ],
            request_id=request_id
        )
    
    logger.info(f"处理简历分析请求: 用户: {current_user.get('email')} - 简历ID: {resume_id} - 职位ID: {job_id} - 请求ID: {request_id}")
    
    try:
        # 查询简历
        resume = await db.resumes.find_one({"_id": ObjectId(resume_id)})
        if not resume:
            logger.warning(f"简历不存在: {resume_id} - 请求ID: {request_id}")
            return ApiResponse.not_found(
                message="简历不存在",
                resource="简历",
                request_id=request_id
            )
        
        # 检查权限
        if str(resume["user_id"]) != str(current_user["_id"]):
            logger.warning(f"无权访问简历: {resume_id} - 用户: {current_user.get('email')} - 请求ID: {request_id}")
            return ApiResponse.forbidden(
                message="无权访问该简历",
                request_id=request_id
            )
        
        # 获取职位详情
        job = await agent_service.get_job_details(job_id)
        if not job:
            logger.warning(f"职位不存在: {job_id} - 请求ID: {request_id}")
            return ApiResponse.not_found(
                message="职位不存在",
                resource="职位",
                request_id=request_id
            )
        
        # 调用分析服务
        analysis = await agent_service.analyze_resume_job_match(
            resume_content=resume.get("content", ""),
            job_description=job.description
        )
        
        # 记录分析历史
        history = {
            "user_id": ObjectId(current_user["_id"]),
            "resume_id": ObjectId(resume_id),
            "job_id": job_id,
            "job_title": job.title,
            "company_name": job.company_name,
            "match_score": analysis.match_score,
            "strengths": analysis.strengths,
            "gaps": analysis.gaps,
            "suggestions": analysis.suggestions,
            "created_at": datetime.utcnow(),
            "request_id": request_id
        }
        await db.resume_analyses.insert_one(history)
        
        logger.info(f"简历分析成功: 简历ID: {resume_id} - 职位ID: {job_id} - 匹配得分: {analysis.match_score} - 请求ID: {request_id}")
        return ApiResponse.success(
            message="简历分析成功",
            data=analysis.model_dump(),
            request_id=request_id
        )
    
    except Exception as e:
        logger.exception(f"简历分析失败: {str(e)} - 请求ID: {request_id}")
        if "AI服务" in str(e) or "LLM" in str(e):
            return ApiResponse.ai_service_error(
                message=f"AI服务调用失败: {str(e)}",
                request_id=request_id
            )
        return ApiResponse.server_error(
            message="简历分析处理失败",
            exc=e,
            request_id=request_id
        )
