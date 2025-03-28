"""
API响应格式化工具

提供统一的API响应格式和错误处理机制
"""
from typing import Any, Dict, Optional, Generic, TypeVar, List, Union, Annotated, Literal, ClassVar, Type, cast
from fastapi.responses import JSONResponse
from fastapi import status, HTTPException, Response, Request
from pydantic import BaseModel, Field, ConfigDict, create_model, field_validator, model_validator
from enum import Enum, auto
import json
import logging
from datetime import datetime
import os

# 配置日志
logger = logging.getLogger(__name__)

# 定义泛型类型变量
T = TypeVar('T')
DataT = TypeVar('DataT')

class ErrorCode(str, Enum):
    """错误代码枚举"""
    # 客户端错误 (4xx)
    VALIDATION_ERROR = "validation_error"       # 数据验证错误
    NOT_FOUND = "not_found"                     # 资源不存在
    UNAUTHORIZED = "unauthorized"               # 未授权访问
    FORBIDDEN = "forbidden"                     # 禁止访问
    BAD_REQUEST = "bad_request"                 # 请求参数错误
    CONFLICT = "conflict"                       # 资源冲突
    RATE_LIMIT = "rate_limit"                   # 请求频率限制
    RESOURCE_EXHAUSTED = "resource_exhausted"   # 资源耗尽
    METHOD_NOT_ALLOWED = "method_not_allowed"   # 方法不允许
    PRECONDITION_FAILED = "precondition_failed" # 前提条件失败
    REQUEST_TIMEOUT = "request_timeout"         # 请求超时
    
    # 服务器错误 (5xx)
    SERVER_ERROR = "server_error"               # 服务器内部错误
    NOT_IMPLEMENTED = "not_implemented"         # 未实现功能
    SERVICE_UNAVAILABLE = "service_unavailable" # 服务不可用
    GATEWAY_TIMEOUT = "gateway_timeout"         # 网关超时
    
    # 业务错误
    BUSINESS_ERROR = "business_error"           # 业务逻辑错误
    DATA_ERROR = "data_error"                   # 数据错误
    AI_SERVICE_ERROR = "ai_service_error"       # AI服务错误

class ErrorSeverity(str, Enum):
    """错误严重性级别"""
    DEBUG = "debug"         # 调试级别，不影响用户体验
    INFO = "info"           # 信息级别，只是通知用户
    WARNING = "warning"     # 警告级别，可能影响用户体验
    ERROR = "error"         # 错误级别，影响功能使用
    CRITICAL = "critical"   # 严重级别，系统级错误

class BaseAPIModel(BaseModel, Generic[T]):
    """
    基础API模型
    
    提供通用配置和方法的基类
    """
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        validate_default=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )

class ResponseModel(BaseAPIModel, Generic[T, DataT]):
    """标准API响应模型"""
    success: bool = Field(
        ..., 
        description="操作是否成功",
        examples=[True]
    )
    message: str = Field(
        ..., 
        description="响应消息",
        examples=["操作成功"]
    )
    data: Optional[DataT] = Field(
        None, 
        description="响应数据"
    )
    request_id: Optional[str] = Field(
        None, 
        description="请求ID，用于追踪和调试",
        examples=["req-123456789"]
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="响应时间戳"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "操作成功",
                "data": {
                    "id": "1",
                    "name": "示例数据"
                },
                "request_id": "req-123456789",
                "timestamp": "2023-01-01T12:00:00"
            }
        }
    )
    
    @classmethod
    def create_response_model(cls, data_model: Type[Any]) -> Type[BaseAPIModel]:
        """
        创建具有特定数据模型的响应模型
        
        Args:
            data_model: 响应数据模型类
            
        Returns:
            Type[BaseAPIModel]: 创建的响应模型类
        """
        return create_model(
            f"{data_model.__name__}Response",
            __base__=ResponseModel,
            data=(Optional[data_model], Field(None, description=f"{data_model.__name__}数据")),
        )
    
    @classmethod
    def success_response(
        cls, 
        data: Optional[DataT] = None, 
        message: str = "操作成功",
        request_id: Optional[str] = None
    ) -> 'ResponseModel[T, DataT]':
        """
        创建成功响应实例
        
        Args:
            data: 响应数据
            message: 响应消息
            request_id: 请求ID
            
        Returns:
            ResponseModel: 成功响应实例
        """
        return cls(
            success=True,
            message=message,
            data=data,
            request_id=request_id
        )

class PaginationInfo(BaseAPIModel):
    """分页信息模型"""
    page: int = Field(..., description="当前页码", ge=1, examples=[1])
    limit: int = Field(..., description="每页记录数", ge=1, le=100, examples=[10])
    total: int = Field(..., description="总记录数", ge=0, examples=[100])
    total_pages: int = Field(..., description="总页数", ge=0, examples=[10])
    has_previous: bool = Field(..., description="是否有上一页", examples=[False])
    has_next: bool = Field(..., description="是否有下一页", examples=[True])
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page": 1,
                "limit": 10,
                "total": 100,
                "total_pages": 10,
                "has_previous": False,
                "has_next": True
            }
        }
    )
    
    @classmethod
    def create(cls, page: int, limit: int, total: int) -> 'PaginationInfo':
        """
        创建分页信息实例
        
        Args:
            page: 当前页码
            limit: 每页记录数
            total: 总记录数
            
        Returns:
            PaginationInfo: 分页信息实例
        """
        total_pages = (total + limit - 1) // limit if limit > 0 else 0
        has_previous = page > 1
        has_next = page < total_pages
        
        return cls(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
            has_previous=has_previous,
            has_next=has_next
        )

class PaginatedResponseModel(ResponseModel[T, List[DataT]], Generic[T, DataT]):
    """分页响应模型"""
    data: Optional[List[DataT]] = Field(None, description="分页数据列表")
    pagination: PaginationInfo = Field(..., description="分页信息")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "获取数据成功",
                "data": [
                    {"id": "1", "name": "项目1"},
                    {"id": "2", "name": "项目2"}
                ],
                "pagination": {
                    "page": 1,
                    "limit": 10,
                    "total": 100,
                    "total_pages": 10,
                    "has_previous": False,
                    "has_next": True
                },
                "request_id": "req-123456789",
                "timestamp": "2023-01-01T12:00:00"
            }
        }
    )
    
    @classmethod
    def create(
        cls,
        items: List[DataT],
        page: int,
        limit: int,
        total: int,
        message: str = "获取数据成功",
        request_id: Optional[str] = None
    ) -> 'PaginatedResponseModel[T, DataT]':
        """
        创建分页响应实例
        
        Args:
            items: 分页数据列表
            page: 当前页码
            limit: 每页记录数
            total: 总记录数
            message: 响应消息
            request_id: 请求ID
            
        Returns:
            PaginatedResponseModel: 分页响应实例
        """
        pagination = PaginationInfo.create(page, limit, total)
        
        return cls(
            success=True,
            message=message,
            data=items,
            pagination=pagination,
            request_id=request_id
        )

class ErrorDetail(BaseAPIModel):
    """错误详情模型"""
    field: Optional[str] = Field(
        None, 
        description="错误字段",
        examples=["email"]
    )
    message: str = Field(
        ..., 
        description="错误消息",
        examples=["无效的邮箱格式"]
    )
    code: Optional[str] = Field(
        None, 
        description="错误代码",
        examples=["invalid_email"]
    )
    severity: ErrorSeverity = Field(
        ErrorSeverity.ERROR,
        description="错误严重性",
        examples=["error"]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "field": "email",
                "message": "无效的邮箱格式",
                "code": "invalid_email",
                "severity": "error"
            }
        }
    )

class ErrorResponseModel(BaseAPIModel):
    """错误响应模型"""
    success: Literal[False] = Field(
        False, 
        description="操作是否成功"
    )
    message: str = Field(
        ..., 
        description="错误消息",
        examples=["请求处理失败"]
    )
    errors: Optional[List[ErrorDetail]] = Field(
        None, 
        description="详细错误列表"
    )
    error_code: Optional[str] = Field(
        None, 
        description="错误代码",
        examples=["validation_error"]
    )
    request_id: Optional[str] = Field(
        None, 
        description="请求ID",
        examples=["req-123456789"]
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="响应时间戳"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "message": "请求处理失败",
                "errors": [
                    {
                        "field": "email",
                        "message": "无效的邮箱格式",
                        "code": "invalid_email",
                        "severity": "error"
                    },
                    {
                        "field": "password",
                        "message": "密码长度不足",
                        "code": "invalid_length",
                        "severity": "error"
                    }
                ],
                "error_code": "validation_error",
                "request_id": "req-123456789",
                "timestamp": "2023-01-01T12:00:00"
            }
        }
    )
    
    @classmethod
    def create(
        cls,
        message: str,
        error_code: str = ErrorCode.BAD_REQUEST,
        errors: Optional[List[Union[ErrorDetail, Dict[str, Any]]]] = None,
        request_id: Optional[str] = None
    ) -> 'ErrorResponseModel':
        """
        创建错误响应实例
        
        Args:
            message: 错误消息
            error_code: 错误代码
            errors: 详细错误列表
            request_id: 请求ID
            
        Returns:
            ErrorResponseModel: 错误响应实例
        """
        error_details = []
        
        if errors:
            for error in errors:
                if isinstance(error, ErrorDetail):
                    error_details.append(error)
                elif isinstance(error, dict):
                    field = error.get("field")
                    msg = error.get("message") or error.get("msg", "未知错误")
                    code = error.get("code")
                    severity = error.get("severity", ErrorSeverity.ERROR)
                    error_details.append(
                        ErrorDetail(
                            field=field,
                            message=msg,
                            code=code,
                            severity=severity
                        )
                    )
        
        return cls(
            success=False,
            message=message,
            errors=error_details if error_details else None,
            error_code=error_code,
            request_id=request_id
        )

class ApiResponse:
    """
    API响应格式化类
    
    提供统一的API响应格式和辅助方法，用于创建各种类型的API响应
    """
    
    @staticmethod
    def success(
        message: str = "操作成功", 
        data: Any = None, 
        status_code: int = status.HTTP_200_OK,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """
        成功响应
        
        Args:
            message: 成功消息
            data: 响应数据
            status_code: HTTP状态码
            request_id: 请求ID，用于追踪
            
        Returns:
            JSONResponse: 包含ResponseModel的JSON响应
        """
        return JSONResponse(
            status_code=status_code,
            content=ResponseModel.success_response(
                data=data, 
                message=message,
                request_id=request_id
            ).dict()
        )

    @staticmethod
    def paginated(
        items: List[Any],
        total: int,
        page: int,
        limit: int,
        message: str = "获取数据成功",
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """
        分页响应
        
        Args:
            items: 分页数据列表
            total: 总记录数
            page: 当前页码
            limit: 每页记录数
            message: 响应消息
            request_id: 请求ID，用于追踪
            
        Returns:
            JSONResponse: 包含PaginatedResponseModel的JSON响应
        """
        return JSONResponse(
            content=PaginatedResponseModel.create(
                items=items, 
                page=page, 
                limit=limit, 
                total=total, 
                message=message,
                request_id=request_id
            ).dict()
        )

    @staticmethod
    def error(
        message: str = "操作失败", 
        errors: Optional[List[Union[ErrorDetail, Dict[str, Any]]]] = None,
        error_code: str = ErrorCode.BAD_REQUEST,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        request_id: Optional[str] = None,
        log_error: bool = True
    ) -> JSONResponse:
        """
        错误响应
        
        Args:
            message: 错误消息
            errors: 详细错误列表
            error_code: 错误代码
            status_code: HTTP状态码
            request_id: 请求ID，用于追踪
            log_error: 是否记录错误日志
            
        Returns:
            JSONResponse: 包含ErrorResponseModel的JSON响应
        """
        # 创建错误响应
        error_response = ErrorResponseModel.create(
            message=message,
            error_code=error_code,
            errors=errors,
            request_id=request_id
        )
        
        # 记录错误日志
        if log_error:
            log_message = f"错误 [{error_code}] {message}"
            if request_id:
                log_message += f" (请求ID: {request_id})"
            if errors:
                error_details = []
                for error in errors:
                    if isinstance(error, ErrorDetail):
                        error_details.append(error.dict())
                    elif isinstance(error, dict):
                        error_details.append(error)
                log_message += f" - 详情: {error_details}"
            
            logger.error(log_message)
        
        return JSONResponse(
            status_code=status_code,
            content=error_response.dict()
        )

    @staticmethod
    def validation_error(
        message: str = "数据验证失败",
        errors: Optional[List[Dict[str, Any]]] = None,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """
        验证错误响应
        
        Args:
            message: 错误消息
            errors: 验证错误列表
            request_id: 请求ID，用于追踪
            
        Returns:
            JSONResponse: 包含验证错误的JSON响应
        """
        return ApiResponse.error(
            message=message,
            errors=errors,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            request_id=request_id
        )

    @staticmethod
    def not_found(
        message: str = "资源不存在",
        resource: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """
        资源不存在响应
        
        Args:
            message: 错误消息
            resource: 资源名称
            request_id: 请求ID，用于追踪
            
        Returns:
            JSONResponse: 包含404错误的JSON响应
        """
        if resource and "不存在" not in message:
            message = f"{resource}不存在"
            
        return ApiResponse.error(
            message=message,
            error_code=ErrorCode.NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            request_id=request_id
        )

    @staticmethod
    def unauthorized(
        message: str = "未授权访问",
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """
        未授权响应
        
        Args:
            message: 错误消息
            request_id: 请求ID，用于追踪
            
        Returns:
            JSONResponse: 包含401错误的JSON响应
        """
        return ApiResponse.error(
            message=message,
            error_code=ErrorCode.UNAUTHORIZED,
            status_code=status.HTTP_401_UNAUTHORIZED,
            request_id=request_id
        )

    @staticmethod
    def forbidden(
        message: str = "禁止访问",
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """
        禁止访问响应
        
        Args:
            message: 错误消息
            request_id: 请求ID，用于追踪
            
        Returns:
            JSONResponse: 包含403错误的JSON响应
        """
        return ApiResponse.error(
            message=message,
            error_code=ErrorCode.FORBIDDEN,
            status_code=status.HTTP_403_FORBIDDEN,
            request_id=request_id
        )

    @staticmethod
    def server_error(
        message: str = "服务器内部错误",
        exc: Optional[Exception] = None,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """
        服务器错误响应
        
        Args:
            message: 错误消息
            exc: 异常对象
            request_id: 请求ID，用于追踪
            
        Returns:
            JSONResponse: 包含500错误的JSON响应
        """
        if exc:
            logger.exception(f"服务器错误: {message}", exc_info=exc)
        
        return ApiResponse.error(
            message=message,
            error_code=ErrorCode.SERVER_ERROR,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            request_id=request_id
        )
    
    @staticmethod
    def conflict(
        message: str = "资源冲突",
        errors: Optional[List[Dict[str, Any]]] = None,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """
        资源冲突响应
        
        Args:
            message: 错误消息
            errors: 详细错误列表
            request_id: 请求ID，用于追踪
            
        Returns:
            JSONResponse: 包含409错误的JSON响应
        """
        return ApiResponse.error(
            message=message,
            errors=errors,
            error_code=ErrorCode.CONFLICT,
            status_code=status.HTTP_409_CONFLICT,
            request_id=request_id
        )
    
    @staticmethod
    def rate_limit(
        message: str = "请求过于频繁",
        retry_after: Optional[int] = None,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """
        请求频率限制响应
        
        Args:
            message: 错误消息
            retry_after: 多少秒后可以重试
            request_id: 请求ID，用于追踪
            
        Returns:
            JSONResponse: 包含429错误的JSON响应
        """
        response = ApiResponse.error(
            message=message,
            error_code=ErrorCode.RATE_LIMIT,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            request_id=request_id
        )
        
        if retry_after:
            response.headers["Retry-After"] = str(retry_after)
            
        return response
    
    @staticmethod
    def business_error(
        message: str,
        errors: Optional[List[Dict[str, Any]]] = None,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """
        业务逻辑错误响应
        
        Args:
            message: 错误消息
            errors: 详细错误列表
            request_id: 请求ID，用于追踪
            
        Returns:
            JSONResponse: 包含业务错误的JSON响应
        """
        return ApiResponse.error(
            message=message,
            errors=errors,
            error_code=ErrorCode.BUSINESS_ERROR,
            status_code=status.HTTP_400_BAD_REQUEST,
            request_id=request_id
        )
    
    @staticmethod
    def ai_service_error(
        message: str = "AI服务调用失败",
        errors: Optional[List[Dict[str, Any]]] = None,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """
        AI服务错误响应
        
        Args:
            message: 错误消息
            errors: 详细错误列表
            request_id: 请求ID，用于追踪
            
        Returns:
            JSONResponse: 包含AI服务错误的JSON响应
        """
        return ApiResponse.error(
            message=message,
            errors=errors,
            error_code=ErrorCode.AI_SERVICE_ERROR,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            request_id=request_id
        )


# 异常处理工具类
class HttpExceptionHandler:
    """HTTP异常处理工具类"""
    
    @staticmethod
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """
        处理HTTP异常
        
        Args:
            request: FastAPI请求对象
            exc: HTTP异常
            
        Returns:
            JSONResponse: 格式化的错误响应
        """
        # 获取请求ID
        request_id = request.headers.get("X-Request-ID")
        
        # 记录日志
        logger.error(
            f"HTTP异常 [{exc.status_code}]: {exc.detail} (请求ID: {request_id or 'unknown'})"
        )
        
        # 根据状态码获取错误代码
        error_code = HttpExceptionHandler._get_error_code_from_status(exc.status_code)
        
        # 获取headers中的详细错误信息
        errors = None
        if exc.headers and "errors" in exc.headers:
            try:
                errors = json.loads(exc.headers["errors"])
            except json.JSONDecodeError:
                logger.error(f"解析错误详情失败: {exc.headers['errors']}")
        
        return ApiResponse.error(
            message=exc.detail,
            errors=errors,
            error_code=error_code,
            status_code=exc.status_code,
            request_id=request_id
        )
    
    @staticmethod
    async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        处理Pydantic验证异常
        
        Args:
            request: FastAPI请求对象
            exc: 验证异常
            
        Returns:
            JSONResponse: 格式化的错误响应
        """
        # 获取请求ID
        request_id = request.headers.get("X-Request-ID")
        
        # 从异常中获取错误详情
        error_details = []
        
        # 尝试从不同类型的验证异常中提取错误详情
        try:
            if hasattr(exc, "errors"):
                for error in exc.errors():
                    field = ".".join(str(loc) for loc in error.get("loc", []))
                    error_details.append({
                        "field": field,
                        "message": error.get("msg"),
                        "code": error.get("type")
                    })
        except Exception as e:
            logger.error(f"提取验证错误详情失败: {str(e)}")
        
        # 记录日志
        logger.error(
            f"验证异常: {str(exc)} (请求ID: {request_id or 'unknown'}), 错误详情: {error_details}"
        )
        
        return ApiResponse.validation_error(
            message="数据验证失败",
            errors=error_details,
            request_id=request_id
        )
    
    @staticmethod
    async def internal_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        处理未捕获的异常
        
        Args:
            request: FastAPI请求对象
            exc: 异常
            
        Returns:
            JSONResponse: 格式化的错误响应
        """
        # 获取请求ID
        request_id = request.headers.get("X-Request-ID")
        
        # 记录详细错误信息
        logger.exception(
            f"未捕获的异常 [{type(exc).__name__}]: {str(exc)} (请求ID: {request_id or 'unknown'})",
            exc_info=exc
        )
        
        # 根据异常类型使用不同的错误代码
        if "权限" in str(exc) or "认证" in str(exc):
            error_code = ErrorCode.FORBIDDEN
            status_code = status.HTTP_403_FORBIDDEN
            message = "权限不足"
        elif "未找到" in str(exc) or "不存在" in str(exc):
            error_code = ErrorCode.NOT_FOUND
            status_code = status.HTTP_404_NOT_FOUND
            message = "资源不存在"
        elif "超时" in str(exc) or "timeout" in str(exc).lower():
            error_code = ErrorCode.REQUEST_TIMEOUT
            status_code = status.HTTP_504_GATEWAY_TIMEOUT
            message = "请求处理超时"
        else:
            error_code = ErrorCode.SERVER_ERROR
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            message = "服务器内部错误"
        
        # 生产环境不暴露详细错误
        is_production = os.environ.get("ENVIRONMENT") == "production"
        
        return ApiResponse.error(
            message=message if is_production else str(exc),
            error_code=error_code,
            status_code=status_code,
            request_id=request_id
        )
    
    @staticmethod
    def _get_error_code_from_status(status_code: int) -> str:
        """
        根据HTTP状态码获取对应的错误代码
        
        Args:
            status_code: HTTP状态码
            
        Returns:
            str: 错误代码
        """
        if status_code == status.HTTP_400_BAD_REQUEST:
            return ErrorCode.BAD_REQUEST
        elif status_code == status.HTTP_401_UNAUTHORIZED:
            return ErrorCode.UNAUTHORIZED
        elif status_code == status.HTTP_403_FORBIDDEN:
            return ErrorCode.FORBIDDEN
        elif status_code == status.HTTP_404_NOT_FOUND:
            return ErrorCode.NOT_FOUND
        elif status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
            return ErrorCode.VALIDATION_ERROR
        elif status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            return ErrorCode.RATE_LIMIT
        elif status_code == status.HTTP_409_CONFLICT:
            return ErrorCode.CONFLICT
        elif status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            return ErrorCode.METHOD_NOT_ALLOWED
        elif status_code == status.HTTP_412_PRECONDITION_FAILED:
            return ErrorCode.PRECONDITION_FAILED
        elif status_code == status.HTTP_408_REQUEST_TIMEOUT:
            return ErrorCode.REQUEST_TIMEOUT
        elif status_code == status.HTTP_501_NOT_IMPLEMENTED:
            return ErrorCode.NOT_IMPLEMENTED
        elif status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            return ErrorCode.SERVICE_UNAVAILABLE
        elif status_code == status.HTTP_504_GATEWAY_TIMEOUT:
            return ErrorCode.GATEWAY_TIMEOUT
        else:
            return ErrorCode.SERVER_ERROR
            
def create_http_exception(
    status_code: int,
    detail: str,
    errors: Optional[List[Dict[str, Any]]] = None
) -> HTTPException:
    """
    创建HTTP异常
    
    Args:
        status_code: HTTP状态码
        detail: 错误详情
        errors: 详细错误列表
        
    Returns:
        HTTPException: HTTP异常
    """
    headers = {}
    if errors:
        try:
            headers["errors"] = json.dumps(errors)
        except Exception as e:
            logger.error(f"序列化错误详情失败: {str(e)}")
    
    return HTTPException(
        status_code=status_code,
        detail=detail,
        headers=headers
    )

def register_exception_handlers(app):
    """
    注册全局异常处理器
    
    Args:
        app: FastAPI应用实例
    """
    from fastapi.exceptions import RequestValidationError
    from pydantic import ValidationError
    
    # 处理FastAPI的HTTP异常
    app.add_exception_handler(
        HTTPException, 
        HttpExceptionHandler.http_exception_handler
    )
    
    # 处理请求验证错误
    app.add_exception_handler(
        RequestValidationError,
        HttpExceptionHandler.validation_exception_handler
    )
    
    # 处理Pydantic验证错误
    app.add_exception_handler(
        ValidationError,
        HttpExceptionHandler.validation_exception_handler
    )
    
    # 处理所有未捕获的异常
    app.add_exception_handler(
        Exception,
        HttpExceptionHandler.internal_exception_handler
    )
    
    logger.info("已注册全局异常处理器")
