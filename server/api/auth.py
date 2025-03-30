"""
认证相关的API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any, Annotated
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
import logging

from server.models.database import get_mongo_db
from server.models.user import UserCreate, UserLogin, UserResponse, UserModel
from server.middleware.auth import AuthMiddleware, get_current_user
from server.utils.response import ApiResponse, ResponseModel, ErrorCode, ErrorDetail
from server.utils.request_id import get_request_id

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(tags=["认证"], prefix="/auth")

@router.post(
    "/register", 
    response_model=ResponseModel,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="创建新用户账户并返回用户信息和认证令牌",
    responses={
        201: {"description": "用户注册成功"},
        409: {"description": "邮箱已被注册"},
        400: {"description": "请求参数无效"}
    }
)
async def register(
    user_data: Annotated[UserCreate, Body(...)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)],
    request_id: str = Depends(get_request_id)
):
    """
    用户注册接口
    
    Args:
        user_data: 用户注册信息，包含邮箱、密码等
        db: MongoDB数据库连接
        request_id: 请求ID
    
    Returns:
        CustomJSONResponse: 包含用户信息和JWT令牌的响应
    """
    logger.info(f"处理用户注册请求: {user_data.email} - 请求ID: {request_id}")
    
    try:
        # 检查邮箱是否已存在
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            logger.warning(f"注册失败: 邮箱已存在 {user_data.email} - 请求ID: {request_id}")
            return ApiResponse.error(
                message="此邮箱已被注册",
                error_code=ErrorCode.CONFLICT,
                status_code=status.HTTP_409_CONFLICT,
                request_id=request_id
            )
        
        # 创建新用户
        new_user = UserModel(
            email=user_data.email,
            phone_number=user_data.phone_number,
            password_hash=UserModel.hash_password(user_data.password),
            full_name=user_data.full_name
        )
        
        # 插入到数据库
        result = await db.users.insert_one(new_user.model_dump(by_alias=True))
        
        # 查询新创建的用户
        created_user = await db.users.find_one({"_id": result.inserted_id})
        if not created_user:
            logger.error(f"用户创建后无法检索: {result.inserted_id} - 请求ID: {request_id}")
            return ApiResponse.server_error(
                message="用户创建失败", 
                request_id=request_id
            )
        
        # 创建令牌
        token = AuthMiddleware.generate_token(created_user)
        
        # 删除敏感信息
        if "password_hash" in created_user:
            del created_user["password_hash"]
        
        logger.info(f"用户注册成功: {user_data.email} - 请求ID: {request_id}")
        
        # 返回用户信息和令牌
        return ApiResponse.success(
            message="注册成功",
            data={
                "user": created_user,
                "token": token
            },
            status_code=status.HTTP_201_CREATED,
            request_id=request_id
        )
    except Exception as e:
        logger.exception(f"用户注册过程中发生错误: {str(e)} - 请求ID: {request_id}")
        return ApiResponse.server_error(
            message="注册过程中发生错误",
            exc=e,
            request_id=request_id
        )

@router.post(
    "/login", 
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="用户登录",
    description="验证用户凭据并返回认证令牌",
    responses={
        200: {"description": "登录成功"},
        401: {"description": "邮箱或密码不正确"},
        400: {"description": "请求参数无效"}
    }
)
async def login(
    login_data: Annotated[UserLogin, Body(...)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)],
    request_id: str = Depends(get_request_id)
):
    """
    用户登录接口
    
    Args:
        login_data: 用户登录信息，包含邮箱和密码
        db: MongoDB数据库连接
        request_id: 请求ID
    
    Returns:
        CustomJSONResponse: 包含用户信息和JWT令牌的响应
    """
    logger.info(f"处理用户登录请求: {login_data.email} - 请求ID: {request_id}")
    
    try:
        # 查找用户
        user = await db.users.find_one({"email": login_data.email})
        if not user:
            logger.warning(f"登录失败: 用户不存在 {login_data.email} - 请求ID: {request_id}")
            return ApiResponse.error(
                message="邮箱或密码不正确",
                error_code=ErrorCode.UNAUTHORIZED,
                status_code=status.HTTP_401_UNAUTHORIZED,
                request_id=request_id
            )
        
        # 调试日志：检查用户数据
        logger.debug(f"从数据库获取的用户数据: {user} - 请求ID: {request_id}")
        
        # 检查必要字段是否存在
        if "password_hash" not in user or not user["password_hash"]:
            logger.error(f"用户数据缺少password_hash字段: {login_data.email} - 请求ID: {request_id}")
            return ApiResponse.error(
                message="登录过程中发生错误",
                error_code=ErrorCode.SERVER_ERROR,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                request_id=request_id
            )
        
        # 验证密码
        user_model = UserModel(**user)
        is_valid = await user_model.compare_password(login_data.password)
        if not is_valid:
            logger.warning(f"登录失败: 密码错误 {login_data.email} - 请求ID: {request_id}")
            return ApiResponse.error(
                message="邮箱或密码不正确",
                error_code=ErrorCode.UNAUTHORIZED,
                status_code=status.HTTP_401_UNAUTHORIZED,
                request_id=request_id
            )
        
        # 更新最后登录时间
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # 创建令牌
        token = AuthMiddleware.generate_token(user)
        
        # 删除敏感信息
        if "password_hash" in user:
            del user["password_hash"]
        
        logger.info(f"用户登录成功: {login_data.email} - 请求ID: {request_id}")
        
        # 返回用户信息和令牌
        return ApiResponse.success(
            message="登录成功",
            data={
                "user": user,
                "token": token
            },
            request_id=request_id
        )
    except Exception as e:
        logger.exception(f"用户登录过程中发生错误: {str(e)} - 请求ID: {request_id}")
        return ApiResponse.server_error(
            message="登录过程中发生错误",
            exc=e,
            request_id=request_id
        )

@router.get(
    "/me", 
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="获取当前用户信息",
    description="返回当前登录用户的详细信息",
    responses={
        200: {"description": "获取用户信息成功"},
        401: {"description": "未认证或令牌无效"},
    }
)
async def get_current_user_info(
    current_user: Annotated[Dict[str, Any], Depends(get_current_user)],
    request_id: str = Depends(get_request_id)
):
    """
    获取当前用户信息接口
    
    Args:
        current_user: 当前用户信息，通过认证中间件获取
        request_id: 请求ID
    
    Returns:
        CustomJSONResponse: 包含用户详细信息的响应
    """
    logger.info(f"获取当前用户信息: {current_user.get('email')} - 请求ID: {request_id}")
    
    try:
        # 删除敏感信息
        if "password_hash" in current_user:
            del current_user["password_hash"]
        
        return ApiResponse.success(
            message="获取用户信息成功",
            data=current_user,
            request_id=request_id
        )
    except Exception as e:
        logger.exception(f"获取用户信息过程中发生错误: {str(e)} - 请求ID: {request_id}")
        return ApiResponse.server_error(
            message="获取用户信息失败",
            exc=e,
            request_id=request_id
        )
