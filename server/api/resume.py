"""
简历相关的API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Path, Body
from fastapi.responses import FileResponse
from typing import Dict, Any, List, Annotated, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import os
import uuid
import logging
from datetime import datetime
from bson import ObjectId

from models.database import get_mongo_db
from middleware.auth import AuthMiddleware
from utils.response import ApiResponse, ResponseModel, PaginatedResponseModel
from models.resume import ResumeModel, ResumeCreate, ResumeUpdate, ResumeResponse
from utils.request_id import get_request_id

# 配置日志
logger = logging.getLogger(__name__)

# 配置上传目录
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "resumes")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 允许的文件类型
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}

router = APIRouter(tags=["简历"], prefix="/resumes")

def allowed_file(filename: str) -> bool:
    """
    检查文件类型是否允许上传
    
    Args:
        filename: 文件名
        
    Returns:
        是否允许上传
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@router.post(
    "/upload", 
    response_model=ResponseModel,
    status_code=status.HTTP_201_CREATED,
    summary="上传简历",
    description="上传新简历文件并保存相关元数据",
    responses={
        201: {"description": "简历上传成功"},
        400: {"description": "文件类型不允许"},
        500: {"description": "文件保存失败"}
    }
)
async def upload_resume(
    resume_file: Annotated[UploadFile, File(...)],
    title: Annotated[str, Form(...)],
    description: Annotated[Optional[str], Form(None)],
    current_user: Annotated[Dict[str, Any], Depends(AuthMiddleware.get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)],
    request_id: str = Depends(get_request_id)
):
    """
    上传简历
    
    Args:
        resume_file: 简历文件（PDF、DOC或DOCX）
        title: 简历标题
        description: 简历描述（可选）
        current_user: 当前登录用户信息
        db: MongoDB数据库连接
        request_id: 请求ID
    
    Returns:
        JSONResponse: 上传的简历信息
    """
    logger.info(f"处理简历上传请求: {resume_file.filename} - 用户: {current_user.get('email')} - 请求ID: {request_id}")
    
    try:
        # 检查文件类型
        if not allowed_file(resume_file.filename):
            logger.warning(f"上传失败: 不支持的文件类型 {resume_file.filename} - 请求ID: {request_id}")
            return ApiResponse.validation_error(
                message=f"不支持的文件类型，允许的类型: {', '.join(ALLOWED_EXTENSIONS)}",
                errors=[{"field": "resume_file", "message": "不支持的文件类型"}],
                request_id=request_id
            )
        
        # 生成唯一文件名
        file_ext = resume_file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # 保存文件
        try:
            contents = await resume_file.read()
            with open(file_path, "wb") as f:
                f.write(contents)
        except Exception as e:
            logger.error(f"文件保存失败: {str(e)} - 请求ID: {request_id}")
            return ApiResponse.server_error(
                message="文件保存失败",
                exc=e,
                request_id=request_id
            )
        
        # 创建简历记录
        resume_data = ResumeCreate(
            title=title,
            description=description,
            file_name=resume_file.filename,
            file_path=unique_filename,
            file_size=len(contents),
            file_type=file_ext,
            user_id=current_user["_id"]
        )
        
        resume = ResumeModel(
            **resume_data.model_dump(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # 保存到数据库
        result = await db.resumes.insert_one(resume.model_dump(by_alias=True))
        
        # 查询新创建的简历
        created_resume = await db.resumes.find_one({"_id": result.inserted_id})
        if not created_resume:
            logger.error(f"简历创建后无法检索: {result.inserted_id} - 请求ID: {request_id}")
            return ApiResponse.server_error(
                message="简历创建失败",
                request_id=request_id
            )
        
        logger.info(f"简历上传成功: {resume_file.filename} - ID: {result.inserted_id} - 请求ID: {request_id}")
        
        # 返回简历信息
        return ApiResponse.success(
            message="简历上传成功",
            data=created_resume,
            status_code=status.HTTP_201_CREATED,
            request_id=request_id
        )
    
    except Exception as e:
        logger.exception(f"简历上传过程中发生错误: {str(e)} - 请求ID: {request_id}")
        return ApiResponse.server_error(
            message="简历上传失败",
            exc=e,
            request_id=request_id
        )

@router.get(
    "/", 
    response_model=PaginatedResponseModel,
    status_code=status.HTTP_200_OK,
    summary="获取简历列表",
    description="获取当前用户的所有简历",
    responses={
        200: {"description": "获取简历列表成功"}
    }
)
async def get_resumes(
    page: Annotated[int, Query(1, ge=1, description="页码")],
    limit: Annotated[int, Query(10, ge=1, le=100, description="每页数量")],
    current_user: Annotated[Dict[str, Any], Depends(AuthMiddleware.get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)],
    request_id: str = Depends(get_request_id)
):
    """
    获取简历列表
    
    Args:
        page: 页码，默认为1
        limit: 每页数量，默认为10
        current_user: 当前登录用户信息
        db: MongoDB数据库连接
        request_id: 请求ID
    
    Returns:
        JSONResponse: 简历列表和分页信息
    """
    logger.info(f"获取简历列表: 用户: {current_user.get('email')} - 页码: {page}, 每页: {limit} - 请求ID: {request_id}")
    
    try:
        # 计算跳过的记录数
        skip = (page - 1) * limit
        
        # 查询条件
        query = {"user_id": current_user["_id"]}
        
        # 获取总记录数
        total = await db.resumes.count_documents(query)
        
        # 获取简历列表
        cursor = db.resumes.find(query).sort("created_at", -1).skip(skip).limit(limit)
        resumes = await cursor.to_list(length=limit)
        
        logger.info(f"获取简历列表成功: 找到 {len(resumes)} 条记录，共 {total} 条 - 请求ID: {request_id}")
        
        # 返回简历列表
        return ApiResponse.paginated(
            items=resumes,
            total=total,
            page=page,
            limit=limit,
            message="获取简历列表成功",
            request_id=request_id
        )
    except Exception as e:
        logger.exception(f"获取简历列表过程中发生错误: {str(e)} - 请求ID: {request_id}")
        return ApiResponse.server_error(
            message="获取简历列表失败",
            exc=e,
            request_id=request_id
        )

@router.get(
    "/{resume_id}", 
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="获取简历详情",
    description="获取指定ID的简历详情",
    responses={
        200: {"description": "获取简历成功"},
        404: {"description": "简历不存在"},
        403: {"description": "无权访问该简历"}
    }
)
async def get_resume(
    resume_id: Annotated[str, Path(..., description="简历ID")],
    current_user: Annotated[Dict[str, Any], Depends(AuthMiddleware.get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)],
    request_id: str = Depends(get_request_id)
):
    """
    获取简历详情
    
    Args:
        resume_id: 简历ID
        current_user: 当前登录用户信息
        db: MongoDB数据库连接
        request_id: 请求ID
    
    Returns:
        JSONResponse: 简历详情
    """
    logger.info(f"获取简历详情: ID: {resume_id} - 用户: {current_user.get('email')} - 请求ID: {request_id}")
    
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
        
        logger.info(f"获取简历详情成功: {resume_id} - 请求ID: {request_id}")
        return ApiResponse.success(
            message="获取简历成功",
            data=resume,
            request_id=request_id
        )
    except Exception as e:
        logger.exception(f"获取简历详情过程中发生错误: {str(e)} - 请求ID: {request_id}")
        return ApiResponse.server_error(
            message="获取简历详情失败",
            exc=e,
            request_id=request_id
        )

@router.get(
    "/{resume_id}/download", 
    response_class=FileResponse,
    summary="下载简历",
    description="下载指定ID的简历文件",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "返回简历文件"},
        404: {"description": "简历或文件不存在"},
        403: {"description": "无权访问该简历"}
    }
)
async def download_resume(
    resume_id: Annotated[str, Path(..., description="简历ID")],
    current_user: Annotated[Dict[str, Any], Depends(AuthMiddleware.get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)],
    request_id: str = Depends(get_request_id)
):
    """
    下载简历文件
    
    Args:
        resume_id: 简历ID
        current_user: 当前登录用户信息
        db: MongoDB数据库连接
        request_id: 请求ID
    
    Returns:
        FileResponse: 简历文件
    """
    logger.info(f"下载简历: ID: {resume_id} - 用户: {current_user.get('email')} - 请求ID: {request_id}")
    
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
        
        # 获取文件路径
        file_path = os.path.join(UPLOAD_DIR, resume["file_path"])
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.warning(f"简历文件不存在: {file_path} - 请求ID: {request_id}")
            return ApiResponse.not_found(
                message="简历文件不存在",
                resource="文件",
                request_id=request_id
            )
        
        # 记录下载信息
        await db.resume_downloads.insert_one({
            "user_id": ObjectId(current_user["_id"]),
            "resume_id": ObjectId(resume_id),
            "download_time": datetime.utcnow(),
            "request_id": request_id
        })
        
        logger.info(f"简历下载成功: {resume_id} - 文件: {resume['file_name']} - 请求ID: {request_id}")
        
        # 返回文件响应
        return FileResponse(
            path=file_path, 
            filename=resume["file_name"],
            media_type=f"application/{resume['file_type']}"
        )
    except Exception as e:
        logger.exception(f"下载简历过程中发生错误: {str(e)} - 请求ID: {request_id}")
        return ApiResponse.server_error(
            message="下载简历失败",
            exc=e,
            request_id=request_id
        )

@router.put(
    "/{resume_id}", 
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="更新简历",
    description="更新指定ID的简历信息",
    responses={
        200: {"description": "更新简历成功"},
        404: {"description": "简历不存在"},
        403: {"description": "无权更新该简历"},
        400: {"description": "请求参数无效"}
    }
)
async def update_resume(
    resume_id: Annotated[str, Path(..., description="简历ID")],
    resume_data: Annotated[ResumeUpdate, Body(...)],
    current_user: Annotated[Dict[str, Any], Depends(AuthMiddleware.get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)],
    request_id: str = Depends(get_request_id)
):
    """
    更新简历信息
    
    Args:
        resume_id: 简历ID
        resume_data: 更新的简历信息
        current_user: 当前登录用户信息
        db: MongoDB数据库连接
        request_id: 请求ID
    
    Returns:
        JSONResponse: 更新后的简历信息
    """
    logger.info(f"更新简历: ID: {resume_id} - 用户: {current_user.get('email')} - 请求ID: {request_id}")
    
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
            logger.warning(f"无权更新简历: {resume_id} - 用户: {current_user.get('email')} - 请求ID: {request_id}")
            return ApiResponse.forbidden(
                message="无权更新该简历",
                request_id=request_id
            )
        
        # 准备更新数据
        update_data = resume_data.model_dump(exclude_unset=True, exclude_none=True)
        if not update_data:
            logger.info(f"没有提供更新数据: {resume_id} - 请求ID: {request_id}")
            return ApiResponse.success(
                message="没有提供更新数据",
                data=resume,
                request_id=request_id
            )
        
        # 添加更新时间
        update_data["updated_at"] = datetime.utcnow()
        
        # 更新简历
        await db.resumes.update_one(
            {"_id": ObjectId(resume_id)},
            {"$set": update_data}
        )
        
        # 查询更新后的简历
        updated_resume = await db.resumes.find_one({"_id": ObjectId(resume_id)})
        
        logger.info(f"更新简历成功: {resume_id} - 请求ID: {request_id}")
        
        # 返回更新后的简历
        return ApiResponse.success(
            message="更新简历成功",
            data=updated_resume,
            request_id=request_id
        )
    
    except Exception as e:
        logger.exception(f"更新简历过程中发生错误: {str(e)} - 请求ID: {request_id}")
        return ApiResponse.server_error(
            message="更新简历失败",
            exc=e,
            request_id=request_id
        )

@router.delete(
    "/{resume_id}", 
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="删除简历",
    description="删除指定ID的简历及其文件"
)
async def delete_resume(
    resume_id: Annotated[str, Path(..., description="简历ID")],
    current_user: Annotated[Dict[str, Any], Depends(AuthMiddleware.get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)],
    request_id: str = Depends(get_request_id)
):
    """
    删除简历
    
    - **resume_id**: 简历ID
    - 需要认证令牌
    - 返回：删除结果
    
    可能的错误：
    - 404: 简历不存在
    - 403: 无权访问该简历
    """
    try:
        logger.info(f"删除简历: ID: {resume_id} - 用户: {current_user.get('email')} - 请求ID: {request_id}")
        
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
            logger.warning(f"无权删除简历: {resume_id} - 用户: {current_user.get('email')} - 请求ID: {request_id}")
            return ApiResponse.forbidden(
                message="无权删除该简历",
                request_id=request_id
            )
        
        # 删除文件
        file_path = os.path.join(UPLOAD_DIR, resume["file_path"])
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"删除文件失败: {file_path} - {str(e)} - 请求ID: {request_id}")
        
        # 删除数据库记录
        await db.resumes.delete_one({"_id": ObjectId(resume_id)})
        
        logger.info(f"删除简历成功: {resume_id} - 请求ID: {request_id}")
        
        # 返回删除结果
        return ApiResponse.success(
            message="删除简历成功",
            request_id=request_id
        )
    except Exception as e:
        logger.error(f"删除简历过程中发生错误: {str(e)} - 请求ID: {request_id}")
        return ApiResponse.server_error(
            message="删除简历失败",
            exc=e,
            request_id=request_id
        )
