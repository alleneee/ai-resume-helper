"""
应用配置模块
使用Pydantic的BaseSettings管理环境变量
"""
from typing import Optional, Dict, Any, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置设置类"""
    
    # 服务器配置
    SERVER_ENV: str = Field("development", description="服务器环境")
    SERVER_HOST: str = Field("0.0.0.0", description="服务器主机")
    SERVER_PORT: int = Field(8000, description="服务器端口")
    DEBUG: bool = Field(False, description="调试模式")
    
    # 数据库配置
    MONGODB_URL: str = Field(..., description="MongoDB连接URL")
    MONGODB_DB: str = Field("resume_helper", description="MongoDB数据库名")
    
    # 安全配置
    SECRET_KEY: str = Field(..., description="JWT密钥")
    JWT_EXPIRES_IN: int = Field(3600, description="JWT过期时间（秒）")
    BCRYPT_SALT_ROUNDS: int = Field(12, description="Bcrypt盐轮数")
    
    # 文件存储配置
    UPLOAD_DIR: str = Field("uploads", description="上传目录")
    MAX_UPLOAD_SIZE: int = Field(10485760, description="最大上传大小（字节）")
    
    # OpenAI配置
    OPENAI_API_KEY: str = Field("", description="OpenAI API密钥")
    OPENAI_ORGANIZATION: str = Field("", description="OpenAI 组织ID")
    OPENAI_MODEL: str = Field("gpt-4o", description="OpenAI基础模型")
    OPENAI_API_BASE_URL: str = Field("https://api.openai.com/v1", description="OpenAI API基础URL")
    OPENAI_TIMEOUT: int = Field(60, description="OpenAI API超时时间（秒）")
    OPENAI_MAX_RETRIES: int = Field(3, description="OpenAI API最大重试次数")
    
    # OpenAI Agents配置
    OPENAI_ASSISTANT_MODEL: str = Field("gpt-4o", description="OpenAI助手模型")
    OPENAI_AGENT_TIMEOUT: int = Field(180, description="OpenAI Agent超时时间（秒）")
    OPENAI_AGENT_MAX_RETRIES: int = Field(2, description="OpenAI Agent最大重试次数")
    RESUME_OPTIMIZER_ASSISTANT_ID: str = Field("", description="简历优化助手ID")
    JOB_SEARCH_ASSISTANT_ID: str = Field("", description="职位搜索助手ID")
    COVER_LETTER_ASSISTANT_ID: str = Field("", description="求职信生成助手ID")
    
    # 职位搜索API配置
    JOB_SEARCH_API_KEY: str = Field("", description="职位搜索API密钥")
    JOB_SEARCH_API_URL: str = Field("https://api.jobsearch.com/v1", description="职位搜索API URL")
    
    # Firecrawl API配置
    FIRECRAWL_API_KEY: str = Field("", description="Firecrawl API密钥")
    
    # CORS配置
    CORS_ORIGINS: List[str] = Field(["*"], description="CORS允许的源")
    
    # 速率限制配置
    RATE_LIMIT_ENABLED: bool = Field(True, description="是否启用速率限制")
    RATE_LIMIT_WINDOW: int = Field(60, description="速率限制窗口（秒）")
    RATE_LIMIT_MAX_REQUESTS: int = Field(100, description="速率限制最大请求数")
    
    # 日志配置
    LOG_LEVEL: str = Field("INFO", description="日志级别")
    
    # 浏览器配置
    BROWSER_HEADLESS: bool = Field(True, description="浏览器无头模式")
    BROWSER_WIDTH: int = Field(1920, description="浏览器窗口宽度")
    BROWSER_HEIGHT: int = Field(1080, description="浏览器窗口高度")
    BROWSER_TIMEOUT: int = Field(30, description="浏览器操作超时时间（秒）")
    
    # Pydantic v2 配置
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @field_validator("SERVER_ENV")
    def validate_server_env(cls, v: str) -> str:
        """验证服务器环境"""
        allowed_values = ["development", "testing", "production"]
        if v.lower() not in allowed_values:
            raise ValueError(f"SERVER_ENV必须是以下值之一: {', '.join(allowed_values)}")
        return v.lower()
    
    @field_validator("LOG_LEVEL")
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别"""
        allowed_values = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_values:
            raise ValueError(f"LOG_LEVEL必须是以下值之一: {', '.join(allowed_values)}")
        return v.upper()
    
    @field_validator("MAX_UPLOAD_SIZE", mode="before")
    def validate_max_upload_size(cls, v: Any) -> int:
        """验证最大上传大小"""
        if isinstance(v, str):
            # 移除注释
            v = v.split('#')[0].strip()
            return int(v)
        return v
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.SERVER_ENV == "development"
    
    @property
    def is_testing(self) -> bool:
        """是否为测试环境"""
        return self.SERVER_ENV == "testing"
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.SERVER_ENV == "production"
    
    @property
    def cors_settings(self) -> Dict[str, Any]:
        """CORS设置"""
        return {
            "allow_origins": self.CORS_ORIGINS,
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }
    
    @property
    def rate_limit_settings(self) -> Dict[str, Any]:
        """速率限制设置"""
        return {
            "enabled": self.RATE_LIMIT_ENABLED,
            "window": self.RATE_LIMIT_WINDOW,
            "max": self.RATE_LIMIT_MAX_REQUESTS
        }
    
    @property
    def openai_settings(self) -> Dict[str, Any]:
        """OpenAI设置"""
        return {
            "api_key": self.OPENAI_API_KEY,
            "organization": self.OPENAI_ORGANIZATION,
            "base_url": self.OPENAI_API_BASE_URL,
            "timeout": self.OPENAI_TIMEOUT,
            "max_retries": self.OPENAI_MAX_RETRIES,
            "model": self.OPENAI_MODEL
        }
    
    @property
    def openai_agents_settings(self) -> Dict[str, Any]:
        """OpenAI Agents设置"""
        return {
            "timeout": self.OPENAI_AGENT_TIMEOUT,
            "max_retries": self.OPENAI_AGENT_MAX_RETRIES,
            "model": self.OPENAI_ASSISTANT_MODEL,
            "resume_optimizer_id": self.RESUME_OPTIMIZER_ASSISTANT_ID,
            "job_search_id": self.JOB_SEARCH_ASSISTANT_ID,
            "cover_letter_id": self.COVER_LETTER_ASSISTANT_ID
        }
        
    @property
    def browser_settings(self) -> Dict[str, Any]:
        """浏览器设置"""
        return {
            "headless": self.BROWSER_HEADLESS,
            "width": self.BROWSER_WIDTH,
            "height": self.BROWSER_HEIGHT,
            "timeout": self.BROWSER_TIMEOUT
        }


@lru_cache()
def get_settings() -> Settings:
    """
    获取应用配置单例
    使用lru_cache装饰器确保只创建一个实例
    """
    return Settings()
