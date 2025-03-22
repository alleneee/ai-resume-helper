"""
AI简历助手 Python API
负责处理简历解析、分析和职位匹配相关功能
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# 导入Agent组件
from agents import (
    CoordinatorAgent, JobSearchParams, ResumeAnalysisResult,
    JobCrawlResult, JobMatchResult, ResumeOptimizationResult
)
from agents.config import UPLOAD_DIR

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="AI简历助手API",
    description="提供简历分析、职位搜索和匹配评估服务",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建全局协调Agent
coordinator = CoordinatorAgent()

# 请求模型
class ResumeUploadRequest(BaseModel):
    """简历上传请求"""
    job_description: Optional[str] = None
    
class JobSearchRequest(BaseModel):
    """职位搜索请求"""
    keywords: List[str]
    locations: Optional[List[str]] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    salary_range: Optional[str] = None
    job_type: Optional[str] = None
    
class JobMatchRequest(BaseModel):
    """职位匹配请求"""
    resume_id: str
    job_description: str
    
class MarketTrendRequest(BaseModel):
    """市场趋势分析请求"""
    job_title: str
    location: Optional[str] = None

# 工具函数
async def extract_text_from_resume(file_path: str) -> str:
    """从不同格式的简历文件中提取文本"""
    # 这里应该根据文件类型调用不同的解析器
    # 为简化演示，这里直接返回文本文件内容
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            # 使用PyPDF2或pdfplumber等库解析PDF
            # 示例代码，实际实现需要安装相应库
            import pdfplumber
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return text
        
        elif file_ext in ['.docx', '.doc']:
            # 使用python-docx等库解析Word文档
            # 示例代码，实际实现需要安装相应库
            import docx
            doc = docx.Document(file_path)
            return " ".join([para.text for para in doc.paragraphs])
        
        elif file_ext == '.txt':
            # 直接读取文本文件
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        else:
            raise ValueError(f"不支持的文件类型: {file_ext}")
            
    except Exception as e:
        logger.error(f"简历文本提取失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"简历文本提取失败: {str(e)}")

# API路由
@app.get("/")
async def root():
    """API健康检查"""
    return {"message": "AI简历助手API服务正常运行"}

@app.post("/resume/upload", response_model=Dict[str, Any])
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    job_description: Optional[str] = Form(None)
):
    """
    上传并分析简历
    
    - **file**: 简历文件(PDF, DOCX, DOC, TXT格式)
    - **job_description**: 可选的目标职位描述
    """
    try:
        # 保存上传的文件
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 提取简历文本
        resume_text = await extract_text_from_resume(file_path)
        
        # 在后台分析简历
        resume_id = os.path.splitext(file.filename)[0]
        
        # 返回即时响应
        response = {
            "message": "简历上传成功，正在分析",
            "resume_id": resume_id,
            "file_name": file.filename,
            "status": "processing"
        }
        
        # 在后台执行分析任务
        background_tasks.add_task(
            analyze_resume_background,
            resume_id,
            resume_text,
            job_description
        )
        
        return response
        
    except Exception as e:
        logger.error(f"简历上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"简历上传失败: {str(e)}")

async def analyze_resume_background(resume_id: str, resume_text: str, job_description: Optional[str] = None):
    """后台执行简历分析任务"""
    try:
        # 分析简历
        analysis_result = await coordinator.process_resume(resume_text)
        
        # 保存分析结果到文件
        result_file = os.path.join(UPLOAD_DIR, f"{resume_id}_analysis.json")
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_result.dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"简历 {resume_id} 分析完成")
        
    except Exception as e:
        logger.error(f"后台简历分析失败: {str(e)}")

@app.get("/resume/{resume_id}/analysis", response_model=Dict[str, Any])
async def get_resume_analysis(resume_id: str):
    """
    获取简历分析结果
    
    - **resume_id**: 简历ID
    """
    try:
        # 检查分析结果是否存在
        result_file = os.path.join(UPLOAD_DIR, f"{resume_id}_analysis.json")
        
        if not os.path.exists(result_file):
            return {
                "message": "分析结果尚未准备好或不存在",
                "resume_id": resume_id,
                "status": "processing"
            }
        
        # 读取分析结果
        with open(result_file, 'r', encoding='utf-8') as f:
            analysis_result = json.load(f)
        
        return {
            "resume_id": resume_id,
            "status": "completed",
            "result": analysis_result
        }
        
    except Exception as e:
        logger.error(f"获取简历分析结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取简历分析结果失败: {str(e)}")

@app.post("/jobs/search", response_model=Dict[str, Any])
async def search_jobs(request: JobSearchRequest):
    """
    搜索职位信息
    
    - **keywords**: 关键词列表
    - **locations**: 可选的地点列表
    - **experience**: 可选的经验要求
    - **education**: 可选的学历要求
    - **salary_range**: 可选的薪资范围
    - **job_type**: 可选的工作类型
    """
    try:
        # 转换请求为搜索参数
        search_params = JobSearchParams(**request.dict())
        
        # 调用协调Agent搜索职位
        result = await coordinator.search_jobs(search_params)
        
        return {
            "status": "success",
            "result": result.dict()
        }
        
    except Exception as e:
        logger.error(f"职位搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"职位搜索失败: {str(e)}")

@app.post("/resume/match", response_model=Dict[str, Any])
async def match_resume_with_job(request: JobMatchRequest):
    """
    评估简历与特定职位的匹配度
    
    - **resume_id**: 简历ID
    - **job_description**: 职位描述
    """
    try:
        # 检查简历文本
        resume_file_pattern = os.path.join(UPLOAD_DIR, f"{request.resume_id}.*")
        import glob
        resume_files = glob.glob(resume_file_pattern)
        
        if not resume_files:
            raise HTTPException(status_code=404, detail=f"找不到ID为 {request.resume_id} 的简历")
        
        # 获取第一个匹配的文件
        resume_file = resume_files[0]
        
        # 提取简历文本
        resume_text = await extract_text_from_resume(resume_file)
        
        # 评估匹配度
        match_result = await coordinator.match_resume_with_job(
            resume_text, 
            request.job_description
        )
        
        return {
            "status": "success",
            "resume_id": request.resume_id,
            "result": match_result.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"简历匹配评估失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"简历匹配评估失败: {str(e)}")

@app.post("/resume/optimize", response_model=Dict[str, Any])
async def optimize_resume(
    resume_id: str = Body(...),
    job_description: Optional[str] = Body(None)
):
    """
    优化简历
    
    - **resume_id**: 简历ID
    - **job_description**: 可选的目标职位描述
    """
    try:
        # 检查简历文本
        resume_file_pattern = os.path.join(UPLOAD_DIR, f"{resume_id}.*")
        import glob
        resume_files = glob.glob(resume_file_pattern)
        
        if not resume_files:
            raise HTTPException(status_code=404, detail=f"找不到ID为 {resume_id} 的简历")
        
        # 获取第一个匹配的文件
        resume_file = resume_files[0]
        
        # 提取简历文本
        resume_text = await extract_text_from_resume(resume_file)
        
        # 优化简历
        optimization_result = await coordinator.optimize_resume(
            resume_text, 
            job_description
        )
        
        return {
            "status": "success",
            "resume_id": resume_id,
            "result": optimization_result.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"简历优化失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"简历优化失败: {str(e)}")

@app.post("/market/trend", response_model=Dict[str, Any])
async def analyze_market_trend(request: MarketTrendRequest):
    """
    分析职位市场趋势
    
    - **job_title**: 职位名称
    - **location**: 可选的地点
    """
    try:
        # 调用协调Agent分析市场趋势
        result = await coordinator.analyze_market_trend(
            request.job_title,
            request.location
        )
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"市场趋势分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"市场趋势分析失败: {str(e)}")

# 启动应用
if __name__ == "__main__":
    import uvicorn
    # 确保上传目录存在
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    # 启动服务
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
