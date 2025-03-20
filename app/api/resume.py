from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from typing import Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid

from app.dependencies import get_resume_parser_service, get_database, get_current_user
from app.services.parser_service import ResumeParserService
from app.models.resume import ResumeUploadResponse, ResumeData, ResumeFile


router = APIRouter(
    prefix="/resumes",
    tags=["resumes"],
    responses={404: {"description": "Not found"}},
)


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    parser_service: ResumeParserService = Depends(get_resume_parser_service),
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    上传并解析简历文件
    """
    try:
        # 解析简历文件
        resume_file, parsed_data = await parser_service.parse_resume_file(file, current_user["id"])
        
        # 将简历信息保存到数据库
        resume_dict = resume_file.model_dump()
        await db.resume_files.insert_one(resume_dict)
        
        return ResumeUploadResponse(
            resume_id=resume_file.id,
            filename=resume_file.filename,
            file_type=resume_file.file_type,
            message="简历上传并解析成功"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"简历上传处理失败: {str(e)}"
        )


@router.get("/{resume_id}", response_model=ResumeData)
async def get_resume_data(
    resume_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取简历解析数据
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
            detail="简历尚未解析完成"
        )
    
    return resume_file["parsed_data"]


@router.get("/", response_model=List[ResumeFile])
async def get_user_resumes(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取用户所有简历
    """
    # 从数据库获取用户所有简历
    cursor = db.resume_files.find({"user_id": current_user["id"]})
    resumes = await cursor.to_list(None)
    
    return resumes 