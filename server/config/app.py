"""
应用配置模块
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 服务器配置
SERVER_ENV = os.getenv("NODE_ENV", "development")
IS_DEVELOPMENT = SERVER_ENV == "development"
SERVER_HOST = os.getenv("HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("PORT", 5000))

# 安全配置
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-here")
JWT_EXPIRES_IN = os.getenv("JWT_EXPIRES_IN", "7d")
BCRYPT_SALT_ROUNDS = 10

# 数据库配置
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/ai-resume-helper")

# CORS配置
CORS = {
    "origin": os.getenv("CORS_ORIGIN", "*"),
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allowedHeaders": ["Content-Type", "Authorization"],
    "credentials": True
}

# 速率限制配置
RATE_LIMIT = {
    "windowMs": 15 * 60 * 1000,  # 15 分钟
    "max": 100                   # 请求次数上限
}

# 日志配置
LOG_LEVEL = "DEBUG" if IS_DEVELOPMENT else "INFO"

# OpenAI配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# 配置对象
config = {
    "server": {
        "env": SERVER_ENV,
        "isDevelopment": IS_DEVELOPMENT,
        "host": SERVER_HOST,
        "port": SERVER_PORT
    },
    "security": {
        "jwtSecret": JWT_SECRET,
        "jwtExpiresIn": JWT_EXPIRES_IN,
        "bcryptSaltRounds": BCRYPT_SALT_ROUNDS
    },
    "database": {
        "uri": MONGODB_URI
    },
    "cors": CORS,
    "rateLimit": RATE_LIMIT,
    "log": {
        "level": LOG_LEVEL
    },
    "openai": {
        "apiKey": OPENAI_API_KEY
    }
}
