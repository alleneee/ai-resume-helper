import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from services.job_search import JobSearchService
from services.job_match import JobMatchService

# 创建路由器
router = APIRouter(tags=["Jobs"])
logger = logging.getLogger(__name__)

# 依赖项
def get_job_search_service():
    return JobSearchService()

def get_job_match_service():
    return JobMatchService()

@router.get("/search")
async def search_jobs(
    query: str = Query(..., description="搜索关键词"),
    location: Optional[str] = Query(None, description="位置"),iy
    page: int = Query(1, description="页码", ge=1),
    limit: int = Query(20, description="每页结果数", ge=1, le=100),
    job_search_service: JobSearchService = Depends(get_job_search_service)
):
    """
    根据关键词和位置搜索职位
    """
    logger.info(f"搜索职位: {query}, 位置: {location}")
    
    try:
        results = await job_search_service.search_jobs(
            query=query,
            location=location,
            page=page,
            limit=limit
        )
        
        return {
            "status": "success",
            "message": "职位搜索成功",
            "data": results
        }
    except Exception as e:
        logger.error(f"职位搜索失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"职位搜索失败: {str(e)}"
        )

@router.get("/{job_id}")
async def get_job_details(
    job_id: str,
    job_search_service: JobSearchService = Depends(get_job_search_service)
):
    """
    获取职位详情
    """
    logger.info(f"获取职位详情: {job_id}")
    
    try:
        job_details = await job_search_service.get_job_details(job_id=job_id)
        
        if not job_details:
            raise HTTPException(
                status_code=404,
                detail=f"未找到ID为{job_id}的职位"
            )
        
        return {
            "status": "success",
            "message": "获取职位详情成功",
            "data": job_details
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取职位详情失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取职位详情失败: {str(e)}"
        )

@router.post("/match")
async def match_resume_to_job(
    resume_data: dict,
    job_id: Optional[str] = None,
    job_description: Optional[str] = None,
    job_match_service: JobMatchService = Depends(get_job_match_service)
):
    """
    分析简历与特定工作的匹配度
    """
    logger.info(f"匹配简历与工作: {job_id if job_id else '通过描述'}")
    
    if not job_id and not job_description:
        raise HTTPException(
            status_code=400,
            detail="必须提供job_id或job_description之一"
        )
    
    try:
        match_result = await job_match_service.match_resume_to_job(
            resume_data=resume_data,
            job_id=job_id,
            job_description=job_description
        )
        
        return {
            "status": "success",
            "message": "简历匹配分析成功",
            "data": match_result
        }
    except Exception as e:
        logger.error(f"简历匹配分析失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"简历匹配分析失败: {str(e)}"
        ) 