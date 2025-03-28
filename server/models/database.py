"""
数据库连接和会话管理
"""
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient
from config.settings import get_settings

# 配置日志
logger = logging.getLogger(__name__)

# MongoDB连接
mongo_client = None
mongo_db = None

# 创建SQLAlchemy引擎和会话
SQLALCHEMY_DATABASE_URL = "sqlite:///./resume_helper.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# connect_to_mongo 作为 connect_to_mongodb 的别名使用
async def connect_to_mongo():
    """
    连接到MongoDB数据库 (为兼容性保留的别名函数)
    """
    global mongo_client, mongo_db
    try:
        settings = get_settings()
        mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
        mongo_db = mongo_client[settings.MONGODB_DB]
        logger.info("已成功连接到MongoDB")
        return mongo_db
    except Exception as e:
        logger.error(f"连接MongoDB失败: {str(e)}")
        raise

async def connect_to_mongodb():
    """
    连接到MongoDB数据库
    """
    global mongo_client, mongo_db
    try:
        settings = get_settings()
        mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
        mongo_db = mongo_client[settings.MONGODB_DB]
        logger.info("已成功连接到MongoDB")
        return mongo_db
    except Exception as e:
        logger.error(f"连接MongoDB失败: {str(e)}")
        raise

def get_db():
    """
    获取SQLAlchemy数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_mongo_db():
    """
    获取MongoDB数据库连接
    """
    return mongo_db

async def close_mongo_connection():
    """
    关闭MongoDB连接
    """
    global mongo_client
    if mongo_client:
        mongo_client.close()
        logger.info("已关闭MongoDB连接")
