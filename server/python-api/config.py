"""
AI简历优化与一键投递系统主配置文件
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# 基本配置
DEBUG = os.environ.get('DEBUG_MODE', 'False').lower() in ('true', '1', 't')
API_PREFIX = os.environ.get('API_PREFIX', '/api')
PROJECT_NAME = "AI Resume Helper"
VERSION = "0.1.0"

# CORS配置
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')

# 日志配置
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# 文件上传配置
UPLOAD_DIR = os.environ.get('UPLOAD_FOLDER', 'uploads')
ALLOWED_EXTENSIONS = os.environ.get('ALLOWED_FILE_EXTENSIONS', 'pdf,docx,doc,txt').split(',')
MAX_FILE_SIZE = int(os.environ.get('MAX_UPLOAD_SIZE_MB', '10')) * 1024 * 1024  # MB转字节

# Node.js API服务
NODE_API_URL = os.environ.get('NODE_API_URL', 'http://localhost:5000')

# AI模型配置
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o')
MAX_TOKENS = int(os.environ.get('MAX_AGENT_TOKENS', '4000'))
FIRECRAWL_API_KEY = os.environ.get('FIRECRAWL_API_KEY', '')

# 数据库配置
DB_CONNECTION_STRING = os.environ.get("DB_CONNECTION_STRING", "mongodb://localhost:27017/resume_helper")
DB_NAME = os.environ.get("DB_NAME", "resume_helper")

# 服务器配置
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))
