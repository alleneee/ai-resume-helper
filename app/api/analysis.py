from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_database, get_current_user
from app.services.analyzer import ResumeAnalysisService
from app.models.analysis import ResumeAnalysis, AnalysisRequest, JobSpecificMatch


router = APIRouter(
    prefix="/analysis",
    tags=["analysis"],
    responses={404: {"description": "Not found"}},
)


@router.post("/resume/{resume_id}", response_model=ResumeAnalysis)
async def analyze_resume(
    resume_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    分析简历，提供评分和优化建议
    """
    # 从数据库获取简历信息
    resume_file = await db.resume_files.find_one({
        "id": resume_id,
        "user_id": current_user["id"]
    })
    
    if not resume_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="简历未找到"
        )
    
    if not resume_file.get("parsed") or not resume_file.get("parsed_data"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="简历尚未解析完成，无法分析"
        )
    
    # 创建分析服务实例
    analysis_service = ResumeAnalysisService()
    
    # 进行分析
    analysis_result = await analysis_service.analyze_resume(
        resume_data=resume_file["parsed_data"],
        resume_id=resume_id
    )
    
    # 将分析结果保存到数据库
    analysis_dict = analysis_result.model_dump()
    
    # 检查是否已存在分析结果，如果存在则更新
    existing_analysis = await db.resume_analyses.find_one({
        "resume_id": resume_id
    })
    
    if existing_analysis:
        await db.resume_analyses.update_one(
            {"resume_id": resume_id},
            {"$set": analysis_dict}
        )
    else:
        await db.resume_analyses.insert_one(analysis_dict)
    
    return analysis_result


@router.post("/job-match", response_model=JobSpecificMatch)
async def analyze_job_match(
    request: AnalysisRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    分析简历与特定职位的匹配度
    """
    if not request.job_description:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="职位描述不能为空"
        )
    
    # 从数据库获取简历信息
    resume_file = await db.resume_files.find_one({
        "id": request.resume_id,
        "user_id": current_user["id"]
    })
    
    if not resume_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="简历未找到"
        )
    
    if not resume_file.get("parsed") or not resume_file.get("parsed_data"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="简历尚未解析完成，无法分析"
        )
    
    # 创建分析服务实例
    analysis_service = ResumeAnalysisService()
    
    # 进行职位匹配分析
    match_result = await analysis_service.analyze_job_match(
        resume_data=resume_file["parsed_data"],
        job_description=request.job_description
    )
    
    return match_result


@router.get("/resume/{resume_id}", response_model=ResumeAnalysis)
async def get_resume_analysis(
    resume_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取已有的简历分析结果
    """
    # 从数据库获取简历所有权
    resume_file = await db.resume_files.find_one({
        "id": resume_id,
        "user_id": current_user["id"]
    })
    
    if not resume_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="简历未找到"
        )
    
    # 查询分析结果
    analysis = await db.resume_analyses.find_one({
        "resume_id": resume_id
    })
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析结果未找到，请先进行分析"
        )
    
    return analysis 