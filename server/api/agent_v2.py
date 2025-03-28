"""
基于OpenAI Agents SDK的智能代理API路由
提供简历优化、职位匹配、求职信生成和职位搜索等功能
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Path, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Any, List, Optional, Annotated, Union
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
import logging
from bson import ObjectId
import uuid

from models.database import get_mongo_db
from middleware.auth import AuthMiddleware, get_current_user_with_permissions
from utils.response import (
    ApiResponse, 
    ResponseModel, 
    PaginatedResponseModel,
    ErrorDetail,
    ErrorCode,
    create_http_exception
)
from utils.request_id import get_request_id
from models.agent import (
    ResumeOptimizationRequest, 
    JobMatchRequest, 
    CoverLetterRequest,
    JobSearchRequest,
    ResumeOptimizationResult,
    JobSearchResult,
    CoverLetterResult
)

# 导入智能代理服务
from services.agents.resume_agent import optimize_resume as agent_optimize_resume, analyze_resume as agent_analyze_resume
from services.agents.job_agent import search_jobs as agent_search_jobs, match_job as agent_match_job
# TODO: 待实现求职信生成功能
# from services.agents.cover_letter_agent import generate_cover_letter as agent_generate_cover_letter

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(tags=["智能代理V2"], prefix="/agent/v2")

# 依赖函数：检查简历访问权限
async def verify_resume_access(
    resume_id: str,
    current_user: Dict[str, Any],
    db: AsyncIOMotorDatabase
) -> Dict[str, Any]:
    """
    验证用户是否有权限访问指定简历
    
    Args:
        resume_id: 简历ID
        current_user: 当前用户信息
        db: 数据库连接
        
    Returns:
        Dict: 简历数据
        
    Raises:
        HTTPException: 
            - 404: 简历不存在
            - 403: 无权访问该简历
    """
    try:
        resume = await db.resumes.find_one({"_id": ObjectId(resume_id)})
        if not resume:
            raise create_http_exception(
                status_code=status.HTTP_404_NOT_FOUND,
                message="简历不存在",
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                details=[ErrorDetail(
                    field="resume_id",
                    message="指定的简历ID不存在"
                )]
            )
        
        # 检查权限
        if str(resume.get("user_id")) != str(current_user.get("_id")):
            raise create_http_exception(
                status_code=status.HTTP_403_FORBIDDEN,
                message="无权访问该简历",
                error_code=ErrorCode.PERMISSION_DENIED,
                details=[ErrorDetail(
                    field="resume_id",
                    message="您没有权限访问该简历"
                )]
            )
            
        return resume
    except ValidationError as e:
        raise create_http_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="无效的简历ID格式",
            error_code=ErrorCode.VALIDATION_ERROR,
            details=[ErrorDetail(
                field="resume_id",
                message=str(e)
            )]
        )

@router.post(
    "/optimize-resume", 
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="优化简历",
    description="使用OpenAI Agents分析和优化简历内容，针对特定职位提供改进建议",
    responses={
        200: {"description": "简历优化成功"},
        400: {"description": "请求参数无效"},
        403: {"description": "无权访问该简历"},
        404: {"description": "简历不存在"},
        500: {"description": "服务器内部错误"}
    }
)
async def optimize_resume(
    request: Annotated[ResumeOptimizationRequest, Body(...)],
    current_user: Annotated[Dict[str, Any], Depends(get_current_user_with_permissions(["resume:read", "resume:write"]))],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)],
    request_id: str = Depends(get_request_id)
):
    """
    优化简历 API端点
    
    使用OpenAI Agents分析职位描述和简历内容，生成针对特定职位的简历优化建议
    
    Args:
        request: 优化请求，包含简历ID和目标职位描述
        current_user: 当前登录用户信息
        db: MongoDB数据库连接
        request_id: 请求ID
    
    Returns:
        JSONResponse: 优化后的简历内容和建议
    """
    logger.info(f"处理简历优化请求 - 用户:{current_user.get('email')} - 简历ID:{request.resume_id} - 请求ID:{request_id}")
    
    try:
        # 验证简历访问权限
        resume = await verify_resume_access(request.resume_id, current_user, db)
        
        # 调用智能代理优化简历
        result = await agent_optimize_resume(
            request=request,
            resume_content=resume.get("content", "")
        )
        
        if not result.get("success"):
            # 处理代理返回的错误
            error_code = result.get("error_code", ErrorCode.INTERNAL_ERROR)
            return ApiResponse.error(
                message=result.get("message", "简历优化失败"),
                error_code=error_code,
                data=result.get("data"),
                request_id=request_id
            )
        
        # 记录优化历史
        optimization_data = {
            "user_id": ObjectId(current_user["_id"]),
            "resume_id": ObjectId(request.resume_id),
            "job_description": request.job_description,
            "original_content": resume.get("content", ""),
            "optimized_content": result["data"].optimized_content,
            "suggestions": result["data"].suggestions,
            "keywords": result["data"].keywords,
            "created_at": datetime.utcnow(),
            "request_id": request_id
        }
        
        await db.resume_optimizations.insert_one(optimization_data)
        
        logger.info(f"简历优化成功 - 用户:{current_user.get('email')} - 简历ID:{request.resume_id} - 请求ID:{request_id}")
        
        return ApiResponse.success(
            message="简历优化成功",
            data=result["data"],
            request_id=request_id
        )
        
    except HTTPException as he:
        # 重新抛出HTTP异常
        raise he
    except Exception as e:
        logger.exception(f"简历优化过程中发生错误 - 请求ID:{request_id}")
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
    description="根据简历内容匹配合适的职位，提供匹配度评分和申请建议",
    responses={
        200: {"description": "职位匹配成功"},
        400: {"description": "请求参数无效"},
        403: {"description": "无权访问该简历"},
        404: {"description": "简历不存在"},
        500: {"description": "服务器内部错误"}
    }
)
async def match_jobs(
    request: Annotated[JobMatchRequest, Body(...)],
    current_user: Annotated[Dict[str, Any], Depends(get_current_user_with_permissions(["resume:read"]))],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)],
    request_id: str = Depends(get_request_id)
):
    """
    职位匹配 API端点
    
    根据简历内容匹配合适的职位，提供匹配度评分和申请建议
    
    Args:
        request: 职位匹配请求
        current_user: 当前登录用户信息
        db: MongoDB数据库连接
        request_id: 请求ID
    
    Returns:
        JSONResponse: 匹配职位列表和匹配度分析
    """
    logger.info(f"处理职位匹配请求 - 用户:{current_user.get('email')} - 简历ID:{request.resume_id} - 请求ID:{request_id}")
    
    try:
        # 验证简历访问权限
        resume = await verify_resume_access(request.resume_id, current_user, db)
        
        # 根据关键词搜索职位
        search_params = JobSearchRequest(
            keywords=request.keywords or ["python", "developer"],
            location=request.location,
            job_type=request.job_type,
            limit=request.limit
        )
        
        search_result = await agent_search_jobs(request=search_params)
        
        if not search_result.get("success"):
            # 处理搜索错误
            error_code = search_result.get("error_code", ErrorCode.INTERNAL_ERROR)
            return ApiResponse.error(
                message=search_result.get("message", "职位搜索失败"),
                error_code=error_code,
                data=search_result.get("data"),
                request_id=request_id
            )
        
        jobs = search_result["data"].jobs if isinstance(search_result["data"], JobSearchResult) else []
        
        # 对每个职位进行匹配分析
        matched_jobs = []
        for job in jobs[:min(len(jobs), request.limit)]:
            # 调用智能代理进行匹配分析
            match_result = await agent_match_job(
                request=request,
                resume_content=resume.get("content", ""),
                job_description=job.description
            )
            
            if match_result.get("success"):
                # 将匹配结果添加到职位信息中
                job_with_match = job.model_copy()
                job_with_match.match_score = match_result["data"].get("match_score", 0)
                matched_jobs.append(job_with_match)
        
        # 按匹配分数排序
        matched_jobs.sort(key=lambda j: j.match_score if j.match_score is not None else 0, reverse=True)
        
        # 创建结果
        result = JobSearchResult(
            jobs=matched_jobs,
            total=len(matched_jobs),
            page=1,
            limit=request.limit
        )
        
        logger.info(f"职位匹配成功 - 用户:{current_user.get('email')} - 简历ID:{request.resume_id} - 匹配职位数:{len(matched_jobs)} - 请求ID:{request_id}")
        
        return ApiResponse.success(
            message="职位匹配成功",
            data=result,
            request_id=request_id
        )
        
    except HTTPException as he:
        # 重新抛出HTTP异常
        raise he
    except Exception as e:
        logger.exception(f"职位匹配过程中发生错误 - 请求ID:{request_id}")
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
    description="根据简历内容、职位描述和公司信息生成个性化求职信",
    responses={
        200: {"description": "求职信生成成功"},
        400: {"description": "请求参数无效"},
        403: {"description": "无权访问该简历"},
        404: {"description": "简历不存在"},
        500: {"description": "服务器内部错误"}
    }
)
async def generate_cover_letter(
    request: Annotated[CoverLetterRequest, Body(...)],
    current_user: Annotated[Dict[str, Any], Depends(get_current_user_with_permissions(["resume:read"]))],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)],
    request_id: str = Depends(get_request_id)
):
    """
    生成求职信 API端点
    
    根据简历内容、职位描述和公司信息生成个性化求职信
    
    Args:
        request: 求职信请求，包含简历ID、职位描述和公司信息
        current_user: 当前登录用户信息
        db: MongoDB数据库连接
        request_id: 请求ID
    
    Returns:
        JSONResponse: 生成的求职信内容
    """
    logger.info(f"处理求职信生成请求 - 用户:{current_user.get('email')} - 简历ID:{request.resume_id} - 公司:{request.company_name} - 请求ID:{request_id}")
    
    try:
        # 验证简历访问权限
        resume = await verify_resume_access(request.resume_id, current_user, db)
        
        # TODO: 求职信生成功能尚未实现，返回临时响应
        # 在cover_letter_agent实现后将使用以下代码
        # result = await agent_generate_cover_letter(
        #    request=request,
        #    resume_content=resume.get("content", "")
        # )
        
        # 临时响应
        result = {
            "success": True,
            "data": {
                "cover_letter": "尊敬的{}招聘团队\n\n我对贵公司的{}职位非常感兴趣...功能开发中".format(
                    request.company_name, 
                    request.job_title or "相关"
                ),
                "tone": request.tone or "professional",
                "sections": [
                    "自我介绍",
                    "专业技能与经验",
                    "对公司的了解与兴趣",
                    "结词"
                ]
            }
        }
        
        if not result.get("success"):
            # 处理代理返回的错误
            error_code = result.get("error_code", ErrorCode.INTERNAL_ERROR)
            return ApiResponse.error(
                message=result.get("message", "求职信生成失败"),
                error_code=error_code,
                data=result.get("data"),
                request_id=request_id
            )
        
        # 记录求职信历史
        cover_letter_data = {
            "user_id": ObjectId(current_user["_id"]),
            "resume_id": ObjectId(request.resume_id),
            "job_description": request.job_description,
            "company_name": request.company_name,
            "company_info": request.company_info,
            "tone": request.tone.value,
            "content": result["data"].content,
            "created_at": datetime.utcnow(),
            "request_id": request_id
        }
        
        await db.cover_letters.insert_one(cover_letter_data)
        
        logger.info(f"求职信生成成功 - 用户:{current_user.get('email')} - 简历ID:{request.resume_id} - 公司:{request.company_name} - 请求ID:{request_id}")
        
        return ApiResponse.success(
            message="求职信生成成功",
            data=result["data"],
            request_id=request_id
        )
        
    except HTTPException as he:
        # 重新抛出HTTP异常
        raise he
    except Exception as e:
        logger.exception(f"求职信生成过程中发生错误 - 请求ID:{request_id}")
        return ApiResponse.server_error(
            message="求职信生成处理失败",
            exc=e,
            request_id=request_id
        )

@router.post(
    "/search-jobs", 
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="搜索职位",
    description="根据关键词、地点、职位类型等条件搜索职位",
    responses={
        200: {"description": "职位搜索成功"},
        400: {"description": "请求参数无效"},
        500: {"description": "服务器内部错误"}
    }
)
async def search_jobs(
    request: Annotated[JobSearchRequest, Body(...)],
    current_user: Annotated[Dict[str, Any], Depends(get_current_user_with_permissions())],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)],
    request_id: str = Depends(get_request_id)
):
    """
    搜索职位 API端点
    
    根据关键词、地点、职位类型等条件搜索职位
    
    Args:
        request: 职位搜索请求
        current_user: 当前登录用户信息
        db: MongoDB数据库连接
        request_id: 请求ID
    
    Returns:
        JSONResponse: 职位搜索结果
    """
    logger.info(f"处理职位搜索请求 - 用户:{current_user.get('email')} - 关键词:{request.keywords} - 地点:{request.location} - 请求ID:{request_id}")
    
    try:
        # 调用智能代理搜索职位
        result = await agent_search_jobs(
            request=request,
            db_client=db
        )
        
        if not result.get("success"):
            # 处理代理返回的错误
            error_code = result.get("error_code", ErrorCode.INTERNAL_ERROR)
            return ApiResponse.error(
                message=result.get("message", "职位搜索失败"),
                error_code=error_code,
                data=result.get("data"),
                request_id=request_id
            )
        
        # 记录搜索历史
        search_history = {
            "user_id": ObjectId(current_user["_id"]),
            "keywords": request.keywords,
            "location": request.location,
            "job_type": request.job_type.value if request.job_type else None,
            "experience_level": request.experience_level.value if request.experience_level else None,
            "education_level": request.education_level.value if request.education_level else None,
            "salary_range": f"{request.salary_min}-{request.salary_max}" if request.salary_min and request.salary_max else None,
            "company_size": request.company_size.value if request.company_size else None,
            "funding_stage": request.funding_stage.value if request.funding_stage else None,
            "result_count": len(result["data"].jobs) if isinstance(result["data"], JobSearchResult) else 0,
            "created_at": datetime.utcnow(),
            "request_id": request_id
        }
        
        await db.job_search_history.insert_one(search_history)
        
        logger.info(f"职位搜索成功 - 用户:{current_user.get('email')} - 关键词:{request.keywords} - 结果数:{len(result['data'].jobs) if isinstance(result['data'], JobSearchResult) else 0} - 请求ID:{request_id}")
        
        return ApiResponse.success(
            message="职位搜索成功",
            data=result["data"],
            request_id=request_id
        )
        
    except ValidationError as e:
        logger.error(f"职位搜索请求参数验证失败 - 请求ID:{request_id}")
        return ApiResponse.validation_error(
            message="请求参数验证失败",
            exc=e,
            request_id=request_id
        )
    except Exception as e:
        logger.exception(f"职位搜索过程中发生错误 - 请求ID:{request_id}")
        return ApiResponse.server_error(
            message="职位搜索处理失败",
            exc=e,
            request_id=request_id
        )

@router.post(
    "/analyze-resume", 
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="分析简历",
    description="分析简历内容，提取优势、劣势和关键技能",
    responses={
        200: {"description": "简历分析成功"},
        400: {"description": "请求参数无效"},
        403: {"description": "无权访问该简历"},
        404: {"description": "简历不存在"},
        500: {"description": "服务器内部错误"}
    }
)
async def analyze_resume(
    resume_id: Annotated[str, Body(..., description="简历ID")],
    current_user: Annotated[Dict[str, Any], Depends(get_current_user_with_permissions(["resume:read"]))],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)],
    request_id: str = Depends(get_request_id)
):
    """
    分析简历 API端点
    
    分析简历内容，提取优势、劣势和关键技能
    
    Args:
        resume_id: 简历ID
        current_user: 当前登录用户信息
        db: MongoDB数据库连接
        request_id: 请求ID
    
    Returns:
        JSONResponse: 简历分析结果
    """
    logger.info(f"处理简历分析请求 - 用户:{current_user.get('email')} - 简历ID:{resume_id} - 请求ID:{request_id}")
    
    try:
        # 验证简历访问权限
        resume = await verify_resume_access(resume_id, current_user, db)
        
        # 调用智能代理分析简历
        result = await agent_analyze_resume(
            resume_content=resume.get("content", "")
        )
        
        if not result.get("success"):
            # 处理代理返回的错误
            error_code = result.get("error_code", ErrorCode.INTERNAL_ERROR)
            return ApiResponse.error(
                message=result.get("message", "简历分析失败"),
                error_code=error_code,
                data=result.get("data"),
                request_id=request_id
            )
        
        logger.info(f"简历分析成功 - 用户:{current_user.get('email')} - 简历ID:{resume_id} - 请求ID:{request_id}")
        
        return ApiResponse.success(
            message="简历分析成功",
            data=result["data"],
            request_id=request_id
        )
        
    except HTTPException as he:
        # 重新抛出HTTP异常
        raise he
    except Exception as e:
        logger.exception(f"简历分析过程中发生错误 - 请求ID:{request_id}")
        return ApiResponse.server_error(
            message="简历分析处理失败",
            exc=e,
            request_id=request_id
        )
