#!/usr/bin/env python3
"""
AI简历优化与一键投递系统启动脚本
"""
import os
import uvicorn
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

if __name__ == "__main__":
    # 获取配置参数
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info")
    reload = os.getenv("DEBUG", "False").lower() == "true"
    
    # 启动服务
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=reload
    ) 