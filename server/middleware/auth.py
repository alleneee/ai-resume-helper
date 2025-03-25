"""
认证中间件
"""
import jwt
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from config.app import config
from models.database import get_mongo_db

security = HTTPBearer()

class AuthMiddleware:
    """
    认证中间件类
    处理JWT令牌验证和用户身份认证
    """
    
    @staticmethod
    def generate_token(user_data: Dict[str, Any]) -> str:
        """
        生成JWT令牌
        
        Args:
            user_data: 用户数据
            
        Returns:
            JWT令牌字符串
        """
        jwt_secret = config['security']['jwtSecret']
        # 解析JWT过期时间字符串（例如："7d"）
        expires_in = config['security']['jwtExpiresIn']
        
        # 处理过期时间格式
        if expires_in.endswith('d'):
            expires_delta = timedelta(days=int(expires_in[:-1]))
        elif expires_in.endswith('h'):
            expires_delta = timedelta(hours=int(expires_in[:-1]))
        elif expires_in.endswith('m'):
            expires_delta = timedelta(minutes=int(expires_in[:-1]))
        else:
            # 默认为7天
            expires_delta = timedelta(days=7)
        
        payload = {
            'sub': str(user_data['_id']),
            'email': user_data['email'],
            'name': user_data['full_name'],
            'role': user_data.get('role', 'USER'),
            'exp': datetime.utcnow() + expires_delta
        }
        
        return jwt.encode(payload, jwt_secret, algorithm='HS256')
    
    @staticmethod
    async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """
        验证JWT令牌
        
        Args:
            credentials: HTTP授权凭证
            
        Returns:
            解码后的JWT负载
            
        Raises:
            HTTPException: 如果令牌无效或已过期
        """
        token = credentials.credentials
        jwt_secret = config['security']['jwtSecret']
        
        try:
            payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail='令牌已过期')
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail='无效的令牌')
    
    @staticmethod
    async def get_current_user(
        payload: Dict[str, Any] = Depends(verify_token),
        db: AsyncIOMotorDatabase = Depends(get_mongo_db)
    ) -> Dict[str, Any]:
        """
        获取当前用户
        
        Args:
            payload: JWT负载
            db: MongoDB数据库连接
            
        Returns:
            用户对象
            
        Raises:
            HTTPException: 如果用户不存在
        """
        user_id = payload['sub']
        user = await db.users.find_one({'_id': user_id})
        
        if user is None:
            raise HTTPException(status_code=404, detail='用户不存在')
        
        return user

auth_middleware = AuthMiddleware()
