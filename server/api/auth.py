"""
认证相关的API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any, Annotated
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
import logging

from models.database import get_mongo_db
from models.user import UserCreate, UserLogin, UserResponse, UserModel
from middleware.auth import AuthMiddleware
from utils.response import ApiResponse, ResponseModel

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(tags=["认证"], prefix="/auth")

@router.post(
    "/register", 
    response_model=ResponseModel,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="创建新用户账户并返回用户信息和认证令牌"
)
async def register(
    user_data: Annotated[UserCreate, Body(...)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)]
):
    """
    用户注册
    
    - **user_data**: 用户注册信息，包含邮箱、密码等
    - 返回：用户信息和JWT令牌
    
    可能的错误：
    - 409: 邮箱已被注册
    """
    try:
        logger.info(f"处理用户注册请求: {user_data.email}")
        
        # 检查邮箱是否已存在
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            logger.warning(f"注册失败: 邮箱已存在 {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="此邮箱已被注册"
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
            logger.error(f"用户创建后无法检索: {result.inserted_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="用户创建失败"
            )
        
        # 创建令牌
        token = AuthMiddleware.generate_token(created_user)
        
        # 删除敏感信息
        if "password_hash" in created_user:
            del created_user["password_hash"]
        
        logger.info(f"用户注册成功: {user_data.email}")
        
        # 返回用户信息和令牌
        return ApiResponse.success(
            message="注册成功",
            data={
                "user": created_user,
                "token": token
            }
        )
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"用户注册过程中发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册过程中发生错误: {str(e)}"
        )

@router.post(
    "/login", 
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="用户登录",
    description="验证用户凭据并返回认证令牌"
)
async def login(
    login_data: Annotated[UserLogin, Body(...)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)]
):
    """
    用户登录
    
    - **login_data**: 用户登录信息，包含邮箱和密码
    - 返回：用户信息和JWT令牌
    
    可能的错误：
    - 401: 邮箱或密码不正确
    """
    try:
        logger.info(f"处理用户登录请求: {login_data.email}")
        
        # 查找用户
        user = await db.users.find_one({"email": login_data.email})
        if not user:
            logger.warning(f"登录失败: 用户不存在 {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码不正确"
            )
        
        # 验证密码
        user_model = UserModel(**user)
        is_valid = await user_model.compare_password(login_data.password)
        if not is_valid:
            logger.warning(f"登录失败: 密码错误 {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码不正确"
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
        
        logger.info(f"用户登录成功: {login_data.email}")
        
        # 返回用户信息和令牌
        return ApiResponse.success(
            message="登录成功",
            data={
                "user": user,
                "token": token
            }
        )
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"用户登录过程中发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录过程中发生错误: {str(e)}"
        )

@router.get(
    "/me", 
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="获取当前用户信息",
    description="返回当前登录用户的详细信息"
)
async def get_current_user_info(
    current_user: Annotated[Dict[str, Any], Depends(AuthMiddleware.get_current_user)]
):
    """
    获取当前用户信息
    
    - 需要认证令牌
    - 返回：当前登录用户的详细信息
    
    可能的错误：
    - 401: 未认证或令牌无效
    """
    try:
        logger.info(f"获取当前用户信息: {current_user.get('email')}")
        
        # 删除敏感信息
        if "password_hash" in current_user:
            del current_user["password_hash"]
        
        return ApiResponse.success(
            message="获取用户信息成功",
            data=current_user
        )
    except Exception as e:
        logger.error(f"获取用户信息过程中发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户信息失败: {str(e)}"
        )
