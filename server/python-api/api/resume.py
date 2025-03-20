import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from fastapi.responses import JSONResponse
from typing import List, Optional

from services.resume_parser import ResumeParserService
from services.resume_analyzer import ResumeAnalyzerService
from services.resume_optimizer import ResumeOptimizerService

# 创建路由器
router = APIRouter(tags=["Resume"])
logger = logging.getLogger(__name__)

# 依赖项
def get_resume_parser():
    return ResumeParserService()

def get_resume_analyzer():
    return ResumeAnalyzerService()

def get_resume_optimizer():
    return ResumeOptimizerService()

@router.post("/parse")
async def parse_resume(
    file: UploadFile = File(...),
    parser: ResumeParserService = Depends(get_resume_parser)
):
    """
    解析上传的简历文件，提取简历内容和结构化数据
    """
    logger.info(f"解析简历: {file.filename}")
    
    try:
        # 检查文件类型
        content_type = file.content_type
        if not content_type or content_type not in [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "image/jpeg",
            "image/png",
            "text/plain"
        ]:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {content_type}. 请上传PDF, DOCX, JPG, PNG 或文本文件."
            )
        
        # 读取文件内容
        file_content = await file.read()
        
        # 解析简历
        result = await parser.parse_resume(file_content, content_type)
        
        return {
            "status": "success",
            "message": "简历解析成功",
            "data": result
        }
    except Exception as e:
        logger.error(f"简历解析失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"简历解析失败: {str(e)}"
        )
    finally:
        await file.close()

@router.post("/analyze")
async def analyze_resume(
    resume_data: dict,
    analyzer: ResumeAnalyzerService = Depends(get_resume_analyzer)
):
    """
    分析简历内容，提供质量评分和改进建议
    """
    logger.info("分析简历")
    
    try:
        # 分析简历
        analysis_result = await analyzer.analyze_resume(resume_data)
        
        return {
            "status": "success",
            "message": "简历分析成功",
            "data": analysis_result
        }
    except Exception as e:
        logger.error(f"简历分析失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"简历分析失败: {str(e)}"
        )

@router.post("/optimize")
async def optimize_resume(
    resume_data: dict,
    job_description: Optional[str] = None,
    optimizer: ResumeOptimizerService = Depends(get_resume_optimizer)
):
    """
    根据工作描述优化简历，生成针对性建议
    """
    logger.info("优化简历")
    
    try:
        # 优化简历
        optimization_result = await optimizer.optimize_resume(resume_data, job_description)
        
        return {
            "status": "success",
            "message": "简历优化成功",
            "data": optimization_result
        }
    except Exception as e:
        logger.error(f"简历优化失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"简历优化失败: {str(e)}"
        ) 