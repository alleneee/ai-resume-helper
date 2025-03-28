#!/usr/bin/env python3
"""
AI简历优化与一键投递系统启动脚本
"""
import os
import uvicorn
from dotenv import load_dotenv
from pathlib import Path

# 加载环境变量 (优先从当前目录加载)
load_dotenv()
if Path("server/python-api/.env").exists():
    load_dotenv("server/python-api/.env")

if __name__ == "__main__":
    # 获取配置参数
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    log_level = os.environ.get("LOG_LEVEL", "info").lower()
    reload = os.environ.get("DEBUG_MODE", "False").lower() in ("true", "1", "t")
    
    print(f"启动服务: host={host}, port={port}, log_level={log_level}, reload={reload}")
    
    # 启动服务
    uvicorn.run(
        "server.main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=reload
    ) 