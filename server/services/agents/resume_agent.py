"""
简历优化和分析相关的智能代理实现
"""
from typing import Dict, Any, List, Optional
import asyncio
import logging
from pydantic import BaseModel, Field

from agents import Agent, Runner, function_tool, RunStatus, AgentHooks, RunContextWrapper, Tool, trace, handoff
from agents.run import Run
from agents.model_settings import ModelSettings

from models.agent import ResumeOptimizationResult, ResumeOptimizationRequest, ResumeOptimizeRequest, ResumeOptimizeResponse
from utils.response import ErrorCode

# 配置日志
logger = logging.getLogger(__name__)

# 定义代理钩子
class ResumeAgentHooks(AgentHooks):
    """简历代理生命周期钩子"""
    
    def __init__(self, display_name: str):
        self.event_counter = 0
        self.display_name = display_name
    
    async def on_start(self, context: RunContextWrapper, agent: Agent) -> None:
        self.event_counter += 1
        logger.info(f"({self.display_name}) {self.event_counter}: 代理 {agent.name} 开始运行")
    
    async def on_end(self, context: RunContextWrapper, agent: Agent, output: Any) -> None:
        self.event_counter += 1
        logger.info(f"({self.display_name}) {self.event_counter}: 代理 {agent.name} 结束运行，输出: {output}")
    
    async def on_handoff(self, context: RunContextWrapper, agent: Agent, source: Agent) -> None:
        self.event_counter += 1
        logger.info(f"({self.display_name}) {self.event_counter}: 代理 {source.name} 交接给 {agent.name}")
    
    async def on_tool_start(self, context: RunContextWrapper, agent: Agent, tool: Tool) -> None:
        self.event_counter += 1
        logger.info(f"({self.display_name}) {self.event_counter}: 代理 {agent.name} 开始使用工具 {tool.name}")
    
    async def on_tool_end(self, context: RunContextWrapper, agent: Agent, tool: Tool, result: str) -> None:
        self.event_counter += 1
        logger.info(f"({self.display_name}) {self.event_counter}: 代理 {agent.name} 结束使用工具 {tool.name}，结果: {result}")

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
    job_analysis: Optional[Dict[str, Any]] = Field(None, description="职位分析结果，包含共同要求、关键技能等")

class ResumeOptimizationOutput(BaseModel):
    optimized_content: str = Field(..., description="优化后的简历内容")
    suggestions: List[str] = Field(..., description="改进建议")
    matched_skills: Optional[List[str]] = Field(None, description="与职位匹配的技能")
    missing_skills: Optional[List[str]] = Field(None, description="缺失的技能")

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
    focus_areas: Optional[List[str]] = None,
    job_analysis: Optional[Dict[str, Any]] = None
) -> ResumeOptimizationOutput:
    """
    根据职位描述、关注点和职位分析结果优化简历内容
    
    Args:
        resume_content: 原始简历内容
        job_description: 目标职位描述
        focus_areas: 需要重点关注的领域或技能
        job_analysis: 职位分析结果，包含共同要求、关键技能等
        
    Returns:
        ResumeOptimizationOutput: 优化结果，包含优化后的内容和改进建议
    """
    logger.debug("调用简历优化工具")
    focus_str = "、".join(focus_areas) if focus_areas else "无特定关注点"
    
    # 提取职位分析中的关键技能（如果有）
    key_skills = []
    if job_analysis and "key_skills" in job_analysis:
        key_skills = list(job_analysis["key_skills"].keys())
    
    # 提取职位分析中的共同要求（如果有）
    common_requirements = []
    if job_analysis and "common_requirements" in job_analysis:
        common_requirements = job_analysis["common_requirements"]
    
    # 生成优化建议
    suggestions = []
    
    # 基于职位描述的建议
    suggestions.append(f"添加更多与{job_description[:30]}...相关的关键词")
    suggestions.append("更具体地描述项目成果")
    
    # 基于关注点的建议
    if focus_areas:
        suggestions.append(f"突出与{focus_str}相关的技能")
    
    # 基于职位分析的建议
    if key_skills:
        suggestions.append(f"重点突出以下技能：{', '.join(key_skills[:5])}")
    
    if common_requirements:
        suggestions.append(f"确保简历涵盖这些共同要求：{', '.join(common_requirements[:3])}")
    
    # 模拟匹配的技能和缺失的技能（实际应用中应该基于真实分析）
    matched_skills = ["Python", "JavaScript", "React"]
    missing_skills = ["Docker", "Kubernetes", "AWS"]
    
    if job_analysis and "key_skills" in job_analysis:
        # 假设简历中包含这些技能（实际应用中需要真实分析）
        resume_skills = ["Python", "JavaScript", "React", "FastAPI", "SQL"]
        
        # 找出匹配的技能
        matched_skills = [skill for skill in resume_skills if skill in key_skills]
        
        # 找出缺失的技能
        missing_skills = [skill for skill in key_skills if skill not in resume_skills][:5]
    
    # 注意：这里只是一个示例，真实场景中这部分逻辑可能需要更复杂的实现
    return ResumeOptimizationOutput(
        optimized_content=f"优化后的简历内容...\n根据职位描述和分析结果突出了相关技能和经验",
        suggestions=suggestions,
        matched_skills=matched_skills,
        missing_skills=missing_skills
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
    hooks=ResumeAgentHooks(display_name="简历分析代理"),
    output_type=ResumeAnalysisOutput,
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
    6. 如果有职位分析结果，利用其中的共同要求和关键技能进行优化
    
    提供优化后的简历内容和具体改进建议，帮助求职者针对特定职位优化简历。
    """,
    tools=[analyze_resume, optimize_resume],
    hooks=ResumeAgentHooks(display_name="简历优化代理"),
    output_type=ResumeOptimizationOutput,
    model_settings=ModelSettings(temperature=0.3),
    handoffs=[handoff(resume_analysis_agent, description="需要详细分析简历")]
)

async def optimize_resume_handler(
    request: ResumeOptimizeRequest,
    resume_content: str,
    job_analysis: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    优化简历内容
    
    Args:
        request: 简历优化请求
        resume_content: 原始简历内容
        job_analysis: 职位分析结果（可选）
        
    Returns:
        Dict: 优化结果包含原始内容、优化后内容、改进建议和关键词
    """
    try:
        logger.info(f"开始进行简历优化, 简历ID: {request.resume_id}")
        
        # 构建优化消息
        focus_areas_text = f"\n优化重点关注领域: {', '.join(request.focus_areas)}" if request.focus_areas else ""
        job_analysis_text = ""
        
        if job_analysis:
            job_analysis_text = f"""
            \n职位分析结果:
            - 共同要求: {', '.join(job_analysis.get('common_requirements', [])[:5])}
            - 关键技能: {', '.join(list(job_analysis.get('key_skills', {}).keys())[:5])}
            - 经验要求: {', '.join([f"{k}: {v}" for k, v in job_analysis.get('experience_requirements', {}).items()][:3])}
            - 学历要求: {', '.join([f"{k}: {v}" for k, v in job_analysis.get('education_requirements', {}).items()][:3])}
            """
        
        message = f"""
        请分析并优化以下简历内容，针对这个职位描述：
        
        职位描述：
        {request.job_description}
        
        简历内容：
        {resume_content}
        {focus_areas_text}
        {job_analysis_text}
        """
        
        # 使用Runner运行代理
        with trace(workflow_name="简历优化"):
            result = await Runner.run(
                resume_optimization_agent, 
                input=message
            )
            
            if not result or not result.final_output:
                return {
                    "success": False,
                    "message": "简历优化失败",
                    "data": {"error": "未获取到优化结果"},
                    "error_code": "OPTIMIZATION_FAILED"
                }
            
            # 获取优化结果
            optimization_output = result.final_output_as(ResumeOptimizationOutput)
            
            # 创建优化结果
            optimization_result = ResumeOptimizeResponse(
                resume_id=request.resume_id,
                original_content=resume_content,
                optimized_content=optimization_output.optimized_content,
                suggestions=optimization_output.suggestions,
                matched_skills=optimization_output.matched_skills or [],
                missing_skills=optimization_output.missing_skills or []
            )
            
            return {
                "success": True,
                "data": optimization_result.dict()
            }
    
    except Exception as e:
        logger.error(f"优化简历时出错: {str(e)}")
        return _handle_exception(e, "优化简历时出错")

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
        logger.info("开始分析简历内容")
        
        # 构建分析消息
        message = f"""
        请分析以下简历内容，提取优势、劣势、关键词和技能缺口：
        
        简历内容：
        {resume_content}
        """
        
        # 使用Runner运行代理
        with trace(workflow_name="简历分析"):
            result = await Runner.run(
                resume_analysis_agent, 
                input=message
            )
            
            if not result or not result.final_output:
                return {
                    "success": False,
                    "message": "简历分析失败",
                    "data": {"error": "未获取到分析结果"},
                    "error_code": "ANALYSIS_FAILED"
                }
            
            # 获取分析结果
            analysis_output = result.final_output_as(ResumeAnalysisOutput)
            
            return {
                "success": True,
                "data": {
                    "strengths": analysis_output.strengths,
                    "weaknesses": analysis_output.weaknesses,
                    "keywords": analysis_output.keywords,
                    "skill_gaps": analysis_output.skill_gaps
                }
            }
    
    except Exception as e:
        logger.error(f"分析简历时出错: {str(e)}")
        return _handle_exception(e, "分析简历时出错")

def _handle_exception(exception: Exception, context: str) -> Dict[str, Any]:
    """
    处理异常并返回标准化的错误响应
    
    Args:
        exception: 异常对象
        context: 错误上下文描述
        
    Returns:
        Dict: 标准化的错误响应
    """
    import traceback
    from openai import BadRequestError
    from pydantic import ValidationError
    
    logger.error(f"{context}: {str(exception)}")
    logger.debug(traceback.format_exc())
    
    if isinstance(exception, BadRequestError):
        return {
            "success": False,
            "message": "API调用错误",
            "data": {"error": str(exception)},
            "error_code": "API_ERROR"
        }
    elif isinstance(exception, ValidationError):
        return {
            "success": False,
            "message": "数据验证错误",
            "data": {"error": str(exception)},
            "error_code": "VALIDATION_ERROR"
        }
    else:
        return {
            "success": False,
            "message": "服务器内部错误",
            "data": {"error": str(exception)},
            "error_code": "INTERNAL_ERROR"
        }
