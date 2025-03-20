import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# 基本配置
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
API_PREFIX = os.getenv('API_PREFIX', '/api')
PROJECT_NAME = "AI Resume Helper"
VERSION = "0.1.0"

# CORS配置
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

# 日志配置
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# 文件上传配置
UPLOAD_DIR = os.getenv('UPLOAD_DIR', '../uploads')
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 5242880))  # 默认5MB

# Node.js API服务
NODE_API_URL = os.getenv('NODE_API_URL', 'http://localhost:5000')

# AI模型配置
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
MODEL_NAME = os.getenv('MODEL_NAME', 'gpt-4o')
MAX_TOKENS = int(os.getenv('MAX_TOKENS', 8192))
