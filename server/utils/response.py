"""
API响应格式化工具
"""
from typing import Any, Dict, Optional, Generic, TypeVar, List, Union
from fastapi.responses import JSONResponse
from fastapi import status
from pydantic import BaseModel, Field, ConfigDict

# 定义泛型类型变量
T = TypeVar('T')

class ResponseModel(BaseModel):
    """标准API响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "success": True,
            "message": "操作成功",
            "data": {
                "id": "1",
                "name": "示例数据"
            }
        }
    })

class PaginatedResponseModel(ResponseModel):
    """分页响应模型"""
    data: Optional[List[Any]] = Field(None, description="分页数据列表")
    pagination: Dict[str, int] = Field(
        ...,
        description="分页信息",
        example={
            "page": 1,
            "limit": 10,
            "total": 100,
            "totalPages": 10
        }
    )

class ErrorDetail(BaseModel):
    """错误详情模型"""
    field: Optional[str] = Field(None, description="错误字段")
    message: str = Field(..., description="错误消息")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "field": "email",
            "message": "无效的邮箱格式"
        }
    })

class ErrorResponseModel(BaseModel):
    """错误响应模型"""
    success: bool = Field(False, description="操作是否成功")
    message: str = Field(..., description="错误消息")
    errors: Optional[List[ErrorDetail]] = Field(None, description="详细错误列表")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "success": False,
            "message": "请求处理失败",
            "errors": [
                {
                    "field": "email",
                    "message": "无效的邮箱格式"
                },
                {
                    "field": "password",
                    "message": "密码长度不足"
                }
            ]
        }
    })

class ApiResponse:
    """
    API响应格式化类
    统一API响应格式
    """
    
    @staticmethod
    def success(
        message: str = "操作成功", 
        data: Any = None, 
        status_code: int = status.HTTP_200_OK
    ) -> ResponseModel:
        """
        成功响应
        
        Args:
            message: 成功消息
            data: 响应数据
            status_code: HTTP状态码
            
        Returns:
            ResponseModel
        """
        return ResponseModel(
            success=True,
            message=message,
            data=data
        )
    
    @staticmethod
    def paginated(
        items: List[Any],
        total: int,
        page: int,
        limit: int,
        message: str = "获取数据成功"
    ) -> PaginatedResponseModel:
        """
        分页响应
        
        Args:
            items: 分页数据列表
            total: 总记录数
            page: 当前页码
            limit: 每页记录数
            message: 响应消息
            
        Returns:
            PaginatedResponseModel
        """
        total_pages = (total + limit - 1) // limit if limit > 0 else 0
        
        return PaginatedResponseModel(
            success=True,
            message=message,
            data=items,
            pagination={
                "page": page,
                "limit": limit,
                "total": total,
                "totalPages": total_pages
            }
        )
    
    @staticmethod
    def error(
        message: str = "操作失败", 
        errors: Optional[List[Union[ErrorDetail, Dict[str, str]]]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ) -> ErrorResponseModel:
        """
        错误响应
        
        Args:
            message: 错误消息
            errors: 详细错误列表
            status_code: HTTP状态码
            
        Returns:
            ErrorResponseModel
        """
        # 转换错误列表
        error_details = None
        if errors:
            error_details = []
            for error in errors:
                if isinstance(error, dict):
                    error_details.append(ErrorDetail(**error))
                else:
                    error_details.append(error)
        
        return ErrorResponseModel(
            success=False,
            message=message,
            errors=error_details
        )
    
    @staticmethod
    def validation_error(
        message: str = "数据验证失败",
        errors: Optional[List[Dict[str, str]]] = None
    ) -> ErrorResponseModel:
        """
        验证错误响应
        
        Args:
            message: 错误消息
            errors: 验证错误列表
            
        Returns:
            ErrorResponseModel
        """
        return ApiResponse.error(
            message=message,
            errors=errors,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    
    @staticmethod
    def not_found(
        message: str = "资源不存在",
        resource: Optional[str] = None
    ) -> ErrorResponseModel:
        """
        资源不存在响应
        
        Args:
            message: 错误消息
            resource: 资源名称
            
        Returns:
            ErrorResponseModel
        """
        if resource and "不存在" not in message:
            message = f"{resource}不存在"
            
        return ApiResponse.error(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    @staticmethod
    def unauthorized(
        message: str = "未授权访问"
    ) -> ErrorResponseModel:
        """
        未授权响应
        
        Args:
            message: 错误消息
            
        Returns:
            ErrorResponseModel
        """
        return ApiResponse.error(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    @staticmethod
    def forbidden(
        message: str = "禁止访问"
    ) -> ErrorResponseModel:
        """
        禁止访问响应
        
        Args:
            message: 错误消息
            
        Returns:
            ErrorResponseModel
        """
        return ApiResponse.error(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    @staticmethod
    def server_error(
        message: str = "服务器内部错误"
    ) -> ErrorResponseModel:
        """
        服务器错误响应
        
        Args:
            message: 错误消息
            
        Returns:
            ErrorResponseModel
        """
        return ApiResponse.error(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
