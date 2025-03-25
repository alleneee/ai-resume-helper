"""
简历优化和分析相关的智能代理实现
"""
from typing import Dict, Any, List, Optional
import asyncio
import logging
from pydantic import BaseModel, Field

from agents import Agent, Runner, function_tool, RunStatus
from agents.run import Run
from agents.model_settings import ModelSettings

from models.agent import ResumeOptimizationResult, ResumeOptimizationRequest
from utils.response import ErrorCode

# 配置日志
logger = logging.getLogger(__name__)

# 定义工具输入/输出模型
class ResumeAnalysisInput(BaseModel):
    resume_content: str = Field(..., description="简历内容")

class ResumeAnalysisOutput(BaseModel):
    strengths: List[str] = Field(..., description="简历优势列表")
    weaknesses: List[str] = Field(..., description="简历劣势列表")
    keywords: List[str] = Field(..., description="提取的关键词")
    skill_gaps: List[str] = Field(..., description="技能缺口")

class ResumeOptimizationInput(BaseModel):
    resume_content: str = Field(..., description="原始简历内容")
    job_description: str = Field(..., description="目标职位描述")
    focus_areas: Optional[List[str]] = Field(None, description="需要重点关注的领域或技能")

class ResumeOptimizationOutput(BaseModel):
    optimized_content: str = Field(..., description="优化后的简历内容")
    suggestions: List[str] = Field(..., description="改进建议")

# 简历分析工具
@function_tool
def analyze_resume(resume_content: str) -> ResumeAnalysisOutput:
    """
    分析简历内容，提取优势、劣势、关键词和技能缺口
    
    Args:
        resume_content: 简历内容
        
    Returns:
        ResumeAnalysisOutput: 分析结果，包含优势、劣势、关键词和技能缺口
    """
    logger.debug("调用简历分析工具")
    # 注意：这里只是一个示例，真实场景中这部分逻辑可能需要更复杂的实现
    return ResumeAnalysisOutput(
        strengths=[
            "清晰展示了技术技能",
            "包含了量化的成就",
            "包含相关项目经验"
        ],
        weaknesses=[
            "缺少关键技能关键词",
            "职责描述过于笼统",
            "成就没有足够量化"
        ],
        keywords=["Python", "FastAPI", "React", "项目管理"],
        skill_gaps=["Docker", "Kubernetes", "AWS"]
    )

# 简历优化工具
@function_tool
def optimize_resume(
    resume_content: str, 
    job_description: str, 
    focus_areas: Optional[List[str]] = None
) -> ResumeOptimizationOutput:
    """
    根据职位描述和关注点优化简历内容
    
    Args:
        resume_content: 原始简历内容
        job_description: 目标职位描述
        focus_areas: 需要重点关注的领域或技能
        
    Returns:
        ResumeOptimizationOutput: 优化结果，包含优化后的内容和改进建议
    """
    logger.debug("调用简历优化工具")
    focus_str = "、".join(focus_areas) if focus_areas else "无特定关注点"
    # 注意：这里只是一个示例，真实场景中这部分逻辑可能需要更复杂的实现
    return ResumeOptimizationOutput(
        optimized_content=f"优化后的简历内容...\n根据职位描述突出了相关技能和经验",
        suggestions=[
            f"添加更多与{job_description}相关的关键词",
            "更具体地描述项目成果",
            f"突出与{focus_str}相关的技能"
        ]
    )

# 创建简历分析代理
resume_analysis_agent = Agent(
    name="简历分析专家",
    instructions="""
    你是一位简历分析专家，精通提取简历中的优势、劣势、关键技能和技能缺口。
    
    分析过程要考虑：
    1. 技术技能与行业关键词的匹配度
    2. 成就描述的具体性和量化程度
    3. 项目经验与求职方向的相关性
    4. 表达方式的专业性和简洁性
    
    提供简明扼要但有价值的分析结果，帮助求职者理解自己简历的优劣势。
    """,
    tools=[analyze_resume],
    model_settings=ModelSettings(temperature=0.2)
)

# 创建简历优化代理
resume_optimization_agent = Agent(
    name="简历优化专家",
    instructions="""
    你是一位简历优化专家，擅长根据特定职位要求优化简历内容，提高求职成功率。
    
    优化时需要：
    1. 根据目标职位描述，突出相关技能和经验
    2. 量化成就，使用具体数字和百分比
    3. 使用行业关键词，提高ATS筛选通过率
    4. 保持简洁专业的表达方式
    5. 调整内容顺序，将最相关的经验放在前面
    
    提供优化后的简历内容和具体改进建议，帮助求职者针对特定职位优化简历。
    """,
    tools=[analyze_resume, optimize_resume],
    model_settings=ModelSettings(temperature=0.3)
)

async def optimize_resume(
    request: ResumeOptimizationRequest,
    resume_content: str,
) -> Dict[str, Any]:
    """
    优化简历内容
    
    Args:
        request: 简历优化请求
        resume_content: 原始简历内容
        
    Returns:
        Dict: 优化结果包含原始内容、优化后内容、改进建议和关键词
    """
    try:
        logger.info(f"开始进行简历优化, 简历ID: {request.resume_id}")
        
        # 创建代理运行
        run = resume_optimization_agent.create_run()
        
        # 启动代理运行
        focus_areas_text = f"\n优化重点关注领域: {', '.join(request.focus_areas)}" if request.focus_areas else ""
        
        await run.send_message(
            f"""
            请分析并优化以下简历内容，针对这个职位描述：
            
            职位描述：
            {request.job_description}
            
            简历内容：
            {resume_content}
            {focus_areas_text}
            """
        )
        
        # 处理代理响应
        optimization_result = None
        
        # 等待代理完成并处理响应
        while True:
            try:
                response = await run.get_next_response()
                logger.debug(f"代理响应类型: {type(response)}")
                
                # 处理工具调用
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    for tool_call in response.tool_calls:
                        if tool_call.function.name == "optimize_resume":
                            output = tool_call.function.output
                            if isinstance(output, dict):
                                optimization_result = output
                
                # 检查运行状态
                if run.status in [RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.EXPIRED]:
                    break
                    
            except Exception as e:
                logger.error(f"获取代理响应时出错: {str(e)}")
                break
            
            # 短暂等待避免过快轮询
            await asyncio.sleep(0.5)
        
        if run.status != RunStatus.COMPLETED:
            logger.error(f"简历优化失败, 状态: {run.status}")
            return {
                "success": False,
                "message": "简历优化处理失败",
                "data": {
                    "error": f"代理运行失败: {run.status}"
                },
                "error_code": ErrorCode.INTERNAL_ERROR
            }
        
        # 如果没有从工具调用中获取结果，尝试从最终输出中解析
        if not optimization_result:
            # 获取代理产生的最终文本输出
            final_message = run.final_output
            logger.debug(f"最终输出: {final_message}")
            
            # 构建基本结果
            optimization_result = {
                "optimized_content": "无法从代理响应中提取优化内容",
                "suggestions": ["未能生成有效的优化建议"]
            }
        
        # 整合分析结果和优化内容
        result = ResumeOptimizationResult(
            original_content=resume_content,
            optimized_content=optimization_result.get("optimized_content", "无法生成优化内容"),
            suggestions=optimization_result.get("suggestions", ["无优化建议"]),
            keywords=request.keywords or ["无关键词提取"]
        )
        
        logger.info(f"简历优化完成, 简历ID: {request.resume_id}")
        
        return {
            "success": True,
            "message": "简历优化成功",
            "data": result
        }
        
    except Exception as e:
        logger.exception(f"简历优化过程中发生错误: {str(e)}")
        return {
            "success": False,
            "message": f"简历优化失败: {str(e)}",
            "data": None,
            "error_code": ErrorCode.INTERNAL_ERROR
        }

async def analyze_resume(
    resume_content: str,
) -> Dict[str, Any]:
    """
    分析简历内容
    
    Args:
        resume_content: 简历内容
        
    Returns:
        Dict: 分析结果包含优势、劣势、关键词和技能缺口
    """
    try:
        logger.info("开始进行简历分析")
        
        # 创建代理运行
        run = resume_analysis_agent.create_run()
        
        # 启动代理运行
        await run.send_message(
            f"""
            请分析以下简历内容，提取优势、劣势、关键词和技能缺口：
            
            {resume_content}
            """
        )
        
        # 处理代理响应
        analysis_result = None
        
        # 等待代理完成并处理响应
        while True:
            try:
                response = await run.get_next_response()
                logger.debug(f"代理响应类型: {type(response)}")
                
                # 处理工具调用
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    for tool_call in response.tool_calls:
                        if tool_call.function.name == "analyze_resume":
                            output = tool_call.function.output
                            if isinstance(output, dict):
                                analysis_result = output
                
                # 检查运行状态
                if run.status in [RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.EXPIRED]:
                    break
                    
            except Exception as e:
                logger.error(f"获取代理响应时出错: {str(e)}")
                break
            
            # 短暂等待避免过快轮询
            await asyncio.sleep(0.5)
        
        if run.status != RunStatus.COMPLETED:
            logger.error(f"简历分析失败, 状态: {run.status}")
            return {
                "success": False,
                "message": "简历分析处理失败",
                "data": {
                    "error": f"代理运行失败: {run.status}"
                },
                "error_code": ErrorCode.INTERNAL_ERROR
            }
        
        # 如果没有从工具调用中获取结果，尝试从最终输出中解析
        if not analysis_result:
            # 获取代理产生的最终文本输出
            final_message = run.final_output
            logger.debug(f"最终输出: {final_message}")
            
            # 构建基本结果
            analysis_result = {
                "strengths": ["未能从代理中提取优势"],
                "weaknesses": ["未能从代理中提取劣势"],
                "keywords": ["未能从代理中提取关键词"],
                "skill_gaps": ["未能从代理中提取技能缺口"]
            }
        
        logger.info("简历分析完成")
        
        return {
            "success": True,
            "message": "简历分析成功",
            "data": analysis_result
        }
        
    except Exception as e:
        logger.exception(f"简历分析过程中发生错误: {str(e)}")
        return {
            "success": False,
            "message": f"简历分析失败: {str(e)}",
            "data": None,
            "error_code": ErrorCode.INTERNAL_ERROR
        }
