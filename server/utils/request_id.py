"""
请求ID工具模块
用于生成和获取请求ID，便于请求跟踪和日志记录
"""
import uuid
from fastapi import Request
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_CTX_KEY = "request_id"


def generate_request_id() -> str:
    """
    生成唯一的请求ID
    
    Returns:
        str: UUID格式的请求ID
    """
    return str(uuid.uuid4())


def get_request_id(request: Request) -> str:
    """
    从请求上下文中获取请求ID
    
    Args:
        request: FastAPI请求对象
    
    Returns:
        str: 请求ID，如果不存在则生成新的
    """
    if REQUEST_ID_CTX_KEY not in request.state.__dict__:
        request.state.__dict__[REQUEST_ID_CTX_KEY] = generate_request_id()
    
    return request.state.__dict__[REQUEST_ID_CTX_KEY]


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    请求ID中间件
    为每个请求添加唯一ID，并在响应头中包含该ID
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求，添加请求ID
        
        Args:
            request: 请求对象
            call_next: 下一个中间件或应用处理器
            
        Returns:
            响应对象
        """
        # 尝试从请求头中获取请求ID
        request_id = request.headers.get(REQUEST_ID_HEADER)
        
        # 如果请求头中没有，则生成新的请求ID
        if not request_id:
            request_id = generate_request_id()
            
        # 将请求ID存储在请求状态中
        request.state.__dict__[REQUEST_ID_CTX_KEY] = request_id
        
        # 处理请求并获取响应
        response = await call_next(request)
        
        # 在响应头中添加请求ID
        response.headers[REQUEST_ID_HEADER] = request_id
        
        return response
