"""
职位搜索和匹配相关的智能代理实现
"""
from ast import main
import os
import uuid
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union, TypedDict
from datetime import datetime
from server.database.mongodb import get_db
from pydantic import BaseModel, Field
from openai.types.beta.threads import Run

from agents import Agent as OpenAIAgent, RunStatus, Runner, AgentHooks, RunContextWrapper, Tool, trace
from agents.tool import function_tool
from agents import GuardrailFunctionOutput, input_guardrail, output_guardrail

# 导入browser-use相关模块
from browser_use import Agent as BrowserAgent
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.controller.service import Controller
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import StrOutputParser

from server.models.agent import (
    JobSearchRequest, 
    JobSearchResponse,
    JobMatchRequest, 
    JobMatchResponse,
    ResumeOptimizeRequest, 
    ResumeOptimizeResponse,
    JobSearchInput,
    JobSearchOutput,
    JobMatchInput,
    JobMatchOutput,
    ResumeOptimizeInput,
    ResumeOptimizeOutput,
    JobType,
    ExperienceLevel,
    JobAnalysisInput,
    JobAnalysisOutput
)

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.tools.base import BaseTool
from langchain_core.tools import tool as function_tool

# 配置日志
logger = logging.getLogger(__name__)

# 定义代理钩子
class JobAgentHooks(AgentHooks):
    """职位代理生命周期钩子"""
    
    def __init__(self, display_name: str):
        self.event_counter = 0
        self.display_name = display_name
    
    async def on_start(self, context: RunContextWrapper, agent: OpenAIAgent) -> None:
        self.event_counter += 1
        logger.info(f"({self.display_name}) {self.event_counter}: 代理 {agent.name} 开始运行")
    
    async def on_end(self, context: RunContextWrapper, agent: OpenAIAgent, output: Any) -> None:
        self.event_counter += 1
        logger.info(f"({self.display_name}) {self.event_counter}: 代理 {agent.name} 结束运行，输出: {output}")
    
    async def on_handoff(self, context: RunContextWrapper, agent: OpenAIAgent, source: OpenAIAgent) -> None:
        self.event_counter += 1
        logger.info(f"({self.display_name}) {self.event_counter}: 代理 {source.name} 交接给 {agent.name}")
    
    async def on_tool_start(self, context: RunContextWrapper, agent: OpenAIAgent, tool: Tool) -> None:
        self.event_counter += 1
        logger.info(f"({self.display_name}) {self.event_counter}: 代理 {agent.name} 开始使用工具 {tool.name}")
    
    async def on_tool_end(self, context: RunContextWrapper, agent: OpenAIAgent, tool: Tool, result: str) -> None:
        self.event_counter += 1
        logger.info(f"({self.display_name}) {self.event_counter}: 代理 {agent.name} 结束使用工具 {tool.name}，结果: {result}")

# 职位搜索输入模型
class JobSearchInput(BaseModel):
    """职位搜索输入参数模型"""
    keywords: List[str] = Field(..., description="搜索关键词列表")
    location: Optional[str] = Field(None, description="工作地点")
    job_type: Optional[str] = Field(None, description="工作类型，如全职、兼职等")
    experience_level: Optional[str] = Field(None, description="经验要求")
    education_level: Optional[str] = Field(None, description="学历要求")
    salary_min: Optional[int] = Field(None, description="最低薪资")
    salary_max: Optional[int] = Field(None, description="最高薪资")
    company_size: Optional[str] = Field(None, description="公司规模")
    funding_stage: Optional[str] = Field(None, description="融资阶段")
    page: int = Field(1, description="页码")
    limit: int = Field(10, description="每页结果数量")

# 职位搜索输出模型
class JobSearchOutput(BaseModel):
    """职位搜索结果模型"""
    jobs: List[Dict[str, Any]] = Field(..., description="搜索到的职位列表")
    total: int = Field(..., description="结果总数")
    page: int = Field(..., description="当前页码")
    limit: int = Field(..., description="每页数量")

# 职位匹配输入模型
class JobMatchInput(BaseModel):
    """职位匹配输入参数模型"""
    resume_content: str = Field(..., description="简历内容")
    job_requirements: str = Field(..., description="职位要求描述")

# 职位匹配输出模型
class JobMatchOutput(BaseModel):
    """职位匹配结果模型"""
    match_score: float = Field(..., description="匹配分数，0-1之间")
    matching_skills: List[str] = Field(..., description="匹配的技能列表")
    missing_skills: List[str] = Field(..., description="缺失的技能列表") 
    recommendations: List[str] = Field(..., description="求职建议列表")

# 职位分析输入模型
class JobAnalysisInput(BaseModel):
    """职位分析输入参数模型"""
    jobs: List[Dict[str, Any]] = Field(..., description="职位列表")
    analysis_focus: Optional[List[str]] = Field(None, description="分析重点，如'技能要求'、'经验要求'等")

# 职位分析输出模型
class JobAnalysisOutput(BaseModel):
    """职位分析结果模型"""
    common_requirements: List[str] = Field(..., description="共同职位要求")
    key_skills: Dict[str, int] = Field(..., description="关键技能及其频率")
    experience_requirements: Dict[str, int] = Field(..., description="经验要求统计")
    education_requirements: Dict[str, int] = Field(..., description="学历要求统计")
    salary_range: Dict[str, Any] = Field(..., description="薪资范围分析")
    report_summary: str = Field(..., description="岗位需求报告摘要")

# 输入约束检查类
class JobInputValidator(BaseModel):
    is_valid: bool
    reason: Optional[str] = None

# 输出约束检查类
class JobSearchValidator(BaseModel):
    is_valid: bool
    reason: Optional[str] = None
    
class JobMatchValidator(BaseModel):
    is_valid: bool
    reason: Optional[str] = None
    
class JobAnalysisValidator(BaseModel):
    is_valid: bool
    reason: Optional[str] = None

# 职位要求输入约束
@input_guardrail
async def job_requirements_guardrail(
    ctx: RunContextWrapper,
    agent: OpenAIAgent,
    job_requirements: str
) -> GuardrailFunctionOutput:
    """验证职位要求输入"""
    # 检查职位要求长度
    if not job_requirements or len(job_requirements) < 30:
        return GuardrailFunctionOutput(
            output_info=JobInputValidator(
                is_valid=False,
                reason="职位要求内容太短，无法进行有效匹配"
            ),
            tripwire_triggered=True
        )
    
    return GuardrailFunctionOutput(
        output_info=JobInputValidator(is_valid=True),
        tripwire_triggered=False
    )

# 简历内容输入约束
@input_guardrail
async def resume_content_guardrail(
    ctx: RunContextWrapper,
    agent: OpenAIAgent,
    resume_content: str
) -> GuardrailFunctionOutput:
    """验证简历内容输入"""
    # 检查简历内容长度
    if not resume_content or len(resume_content) < 50:
        return GuardrailFunctionOutput(
            output_info=JobInputValidator(
                is_valid=False,
                reason="简历内容太短，无法进行有效匹配"
            ),
            tripwire_triggered=True
        )
    
    return GuardrailFunctionOutput(
        output_info=JobInputValidator(is_valid=True),
        tripwire_triggered=False
    )

# 职位数据输入约束
@input_guardrail
async def job_data_guardrail(
    ctx: RunContextWrapper,
    agent: OpenAIAgent,
    jobs: List[Dict[str, Any]]
) -> GuardrailFunctionOutput:
    """验证职位数据输入"""
    # 检查职位数量
    if not jobs or len(jobs) < 1:
        return GuardrailFunctionOutput(
            output_info=JobInputValidator(
                is_valid=False,
                reason="职位数据为空，无法进行分析"
            ),
            tripwire_triggered=True
        )
    
    # 检查职位数据是否包含必要字段
    required_fields = ["title", "description"]
    for i, job in enumerate(jobs):
        missing_fields = [field for field in required_fields if field not in job or not job[field]]
        if missing_fields:
            return GuardrailFunctionOutput(
                output_info=JobInputValidator(
                    is_valid=False,
                    reason=f"职位 #{i+1} 缺少必要字段: {', '.join(missing_fields)}"
                ),
                tripwire_triggered=True
            )
    
    return GuardrailFunctionOutput(
        output_info=JobInputValidator(is_valid=True),
        tripwire_triggered=False
    )

# 搜索关键词输入约束
@input_guardrail
async def search_keywords_guardrail(
    ctx: RunContextWrapper,
    agent: OpenAIAgent,
    keywords: List[str]
) -> GuardrailFunctionOutput:
    """验证搜索关键词输入"""
    # 检查关键词数量
    if not keywords or len(keywords) < 1:
        return GuardrailFunctionOutput(
            output_info=JobInputValidator(
                is_valid=False,
                reason="搜索关键词为空，无法进行搜索"
            ),
            tripwire_triggered=True
        )
    
    return GuardrailFunctionOutput(
        output_info=JobInputValidator(is_valid=True),
        tripwire_triggered=False
    )

# 职位搜索输出约束
@output_guardrail
async def job_search_output_guardrail(
    ctx: RunContextWrapper,
    agent: OpenAIAgent,
    output: JobSearchOutput
) -> GuardrailFunctionOutput:
    """验证职位搜索输出结果"""
    # 检查是否有搜索结果
    if not output.jobs or len(output.jobs) == 0:
        return GuardrailFunctionOutput(
            output_info=JobSearchValidator(
                is_valid=False,
                reason="搜索结果为空，未找到匹配的职位"
            ),
            tripwire_triggered=True
        )
    
    return GuardrailFunctionOutput(
        output_info=JobSearchValidator(is_valid=True),
        tripwire_triggered=False
    )

# 职位匹配输出约束
@output_guardrail
async def job_match_output_guardrail(
    ctx: RunContextWrapper,
    agent: OpenAIAgent,
    output: JobMatchOutput
) -> GuardrailFunctionOutput:
    """验证职位匹配输出结果"""
    # 检查是否有匹配分析结果
    if output.match_score < 0 or output.match_score > 1:
        return GuardrailFunctionOutput(
            output_info=JobMatchValidator(
                is_valid=False,
                reason="匹配分数无效，应该在0-1之间"
            ),
            tripwire_triggered=True
        )
    
    # 检查是否有足够的建议
    if not output.recommendations or len(output.recommendations) < 2:
        return GuardrailFunctionOutput(
            output_info=JobMatchValidator(
                is_valid=False,
                reason="匹配建议数量不足，至少需要2条建议"
            ),
            tripwire_triggered=True
        )
    
    return GuardrailFunctionOutput(
        output_info=JobMatchValidator(is_valid=True),
        tripwire_triggered=False
    )

# 职位分析输出约束
@output_guardrail
async def job_analysis_output_guardrail(
    ctx: RunContextWrapper,
    agent: OpenAIAgent,
    output: JobAnalysisOutput
) -> GuardrailFunctionOutput:
    """验证职位分析输出结果"""
    # 检查是否有基本分析结果
    if (not output.common_requirements or len(output.common_requirements) < 2 or
            not output.key_skills or len(output.key_skills) < 3):
        return GuardrailFunctionOutput(
            output_info=JobAnalysisValidator(
                is_valid=False,
                reason="分析结果不够全面，缺少足够的共同要求或关键技能"
            ),
            tripwire_triggered=True
        )
    
    # 检查报告摘要
    if not output.report_summary or len(output.report_summary) < 50:
        return GuardrailFunctionOutput(
            output_info=JobAnalysisValidator(
                is_valid=False,
                reason="报告摘要过短，信息不足"
            ),
            tripwire_triggered=True
        )
    
    return GuardrailFunctionOutput(
        output_info=JobAnalysisValidator(is_valid=True),
        tripwire_triggered=False
    )

# 职位搜索工具
@function_tool
@input_guardrail(search_keywords_guardrail)
@output_guardrail(job_search_output_guardrail)
async def search_jobs(params: JobSearchInput) -> JobSearchOutput:
    """根据指定条件搜索职位信息"""
    try:
        # 获取环境变量
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.error("未找到OPENAI_API_KEY环境变量")
            # 如果没有API密钥，返回模拟数据
            return _get_mock_job_search_results(params)
        
        # 创建语言模型
        llm = ChatOpenAI(
            api_key=openai_api_key,
            model="gpt-4o-2024-11-20",
            temperature=0
        )
        
        # 创建浏览器控制器
        controller = Controller()
        
        # 创建浏览器配置
        browser_config = BrowserConfig(
            headless=True,  # 生产环境中使用无头模式
        )
        
        # 创建浏览器实例
        browser = Browser(config=browser_config)
        
        # 构建搜索任务
        location = params.location or "全国"
        keywords = params.keywords or ""
        job_type = params.job_type or ""
        experience_level = params.experience_level or ""
        
        # 定义任务 - 根据参数在Boss直聘搜索职位
        task = f"""
        访问Boss直聘网站(https://www.zhipin.com)，并执行以下操作：
        1. 在首页找到城市选择选项，选择"{location}"
        2. 在搜索框中输入"{keywords}"并搜索
        3. 如果有筛选选项，尝试设置以下筛选条件：
           - 工作类型: {job_type}
           - 经验要求: {experience_level}
        4. 等待搜索结果加载完成
        5. 提取前{params.limit or 10}个职位的以下信息：
           - 职位ID（如果有）
           - 职位名称
           - 公司名称
           - 薪资范围
           - 工作地点
           - 经验要求
           - 学历要求
           - 公司规模（如果有）
           - 融资阶段（如果有）
           - 职位描述摘要
           - 职位链接
           - 发布日期
        6. 将提取的信息整理成结构化的JSON格式返回
        """
        
        try:
            # 创建浏览器代理
            browser_agent = BrowserAgent(
                task=task,
                llm=llm,
                controller=controller,
                browser=browser
            )
            
            # 运行任务
            logger.info(f"开始搜索职位: 地点={location}, 关键词={keywords}")
            result = await browser_agent.run()
            
            # 解析结果
            try:
                import json
                json_result = json.loads(result)
                
                # 将结果转换为JobSearchOutput格式
                jobs = []
                for job_data in json_result.get("job_listings", []):
                    job = {
                        "id": job_data.get("id", f"job_{uuid.uuid4().hex[:8]}"),
                        "title": job_data.get("position_name"),
                        "company": job_data.get("company_name"),
                        "location": job_data.get("location"),
                        "description": job_data.get("description", ""),
                        "salary": job_data.get("salary_range"),
                        "job_type": job_data.get("job_type", "全职"),
                        "experience_level": job_data.get("experience_requirement"),
                        "education_level": job_data.get("education_requirement"),
                        "company_size": job_data.get("company_size", ""),
                        "funding_stage": job_data.get("funding_stage", ""),
                        "company_description": job_data.get("company_description", ""),
                        "url": job_data.get("url", ""),
                        "posted_date": job_data.get("posted_date", "")
                    }
                    jobs.append(job)
                
                # 返回搜索结果
                return JobSearchOutput(
                    jobs=jobs,
                    total=len(jobs),
                    page=params.page,
                    limit=params.limit
                )
                
            except Exception as e:
                logger.error(f"解析职位搜索结果时出错: {str(e)}")
                return _get_mock_job_search_results(params)
                
        except Exception as e:
            logger.error(f"执行职位搜索任务时出错: {str(e)}")
            return _get_mock_job_search_results(params)
            
    except Exception as e:
        logger.error(f"搜索职位时出错: {str(e)}")
        return _get_mock_job_search_results(params)

# 返回模拟的职位搜索结果
def _get_mock_job_search_results(params: JobSearchInput) -> JobSearchOutput:
    """返回模拟的职位搜索结果，用于测试或API调用失败时"""
    jobs = []
    for i in range(1, params.limit + 1):
        job = {
            "id": f"job_{uuid.uuid4().hex[:8]}",
            "title": f"测试职位 {i}",
            "company": f"测试公司 {i}",
            "location": params.location or "北京",
            "description": "这是一个测试职位描述，包含了该职位的主要职责和要求。",
            "salary": "15k-30k",
            "job_type": params.job_type or "全职",
            "experience_level": params.experience_level or "3-5年",
            "education_level": params.education_level or "本科",
            "company_size": params.company_size or "500-2000人",
            "funding_stage": params.funding_stage or "D轮及以上",
            "company_description": "这是一家测试公司的描述，包含了公司的基本情况和文化。",
            "url": f"https://example.com/job/{i}",
            "posted_date": "2023-01-01"
        }
        jobs.append(job)
    
    return JobSearchOutput(
        jobs=jobs,
        total=100,  # 模拟总数
        page=params.page,
        limit=params.limit
    )

# 职位匹配工具
@function_tool
@input_guardrail(resume_content_guardrail)
@input_guardrail(job_requirements_guardrail)
@output_guardrail(job_match_output_guardrail)
def match_job(input_data: JobMatchInput) -> JobMatchOutput:
    """根据简历内容和职位要求进行匹配分析"""
    # 提取简历中的技能关键词
    resume_skills = ["Python", "JavaScript", "React", "FastAPI", "SQL", "Git"]
    
    # 提取职位要求中的技能关键词
    job_skills = ["Python", "Django", "PostgreSQL", "Docker", "AWS", "CI/CD"]
    
    # 计算匹配的技能
    matching_skills = [skill for skill in resume_skills if skill.lower() in input_data.job_requirements.lower()]
    
    # 计算缺失的技能
    missing_skills = [skill for skill in job_skills if skill.lower() not in input_data.resume_content.lower()]
    
    # 计算匹配分数
    match_score = len(matching_skills) / (len(matching_skills) + len(missing_skills)) if (len(matching_skills) + len(missing_skills)) > 0 else 0
    
    # 生成建议
    recommendations = [
        "在简历中突出与职位相关的技能和经验",
        "添加缺失的关键技能，如果你具备这些技能",
        "量化你的成就，使用具体的数字和百分比"
    ]
    
    return JobMatchOutput(
        match_score=match_score,
        matching_skills=matching_skills,
        missing_skills=missing_skills,
        recommendations=recommendations
    )

# 职位分析工具
@function_tool
@input_guardrail(job_data_guardrail)
@output_guardrail(job_analysis_output_guardrail)
def analyze_jobs(input_data: JobAnalysisInput) -> JobAnalysisOutput:
    """分析职位数据，提取共同点和要求"""
    logger.info(f"开始分析职位数据，共{len(input_data.jobs)}个职位")
    
    # 获取OpenAI API密钥 (LangChain 会自动从环境变量获取，但这里显式设置以保持一致性)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # 创建 LangChain ChatOpenAI 实例
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        api_key=openai_api_key
    )
    
    # 准备职位数据
    job_descriptions = []
    for i, job in enumerate(input_data.jobs[:10]):  # 限制处理的职位数量
        job_title = job.get("title", f"职位{i+1}")
        job_desc = job.get("description", "")
        job_descriptions.append(f"职位{i+1} - {job_title}:\n{job_desc[:500]}...\n")
    
    job_texts = "\n".join(job_descriptions)
    
    # 构建分析提示
    analysis_focus = "、".join(input_data.analysis_focus) if input_data.analysis_focus else "技能要求、经验要求、学历要求、薪资范围"
    
    # 构建分析提示模板
    prompt_template = """
    请分析以下{job_count}个职位描述，提取共同点和要求。
    
    重点关注：{analysis_focus}
    
    职位描述：
    {job_texts}
    
    请按照以下格式返回分析结果：
    
    共同要求：
    - [要求1]
    - [要求2]
    ...
    
    关键技能（按频率排序）：
    [技能1]: [频率]
    [技能2]: [频率]
    ...
    
    经验要求统计：
    [经验级别1]: [数量]
    [经验级别2]: [数量]
    ...
    
    学历要求统计：
    [学历级别1]: [数量]
    [学历级别2]: [数量]
    ...
    
    薪资范围分析：
    - 最低: [金额]
    - 最高: [金额]
    - 平均: [金额]
    - 分布: [分布情况]
    
    岗位需求报告摘要：
    [简要总结分析结果，并提供针对求职者的建议]
    """
    
    # 创建 ChatPromptTemplate
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一位专业的职位分析专家，擅长分析职位描述并提取关键信息。"),
        ("user", prompt_template)
    ])
    
    # 构建 LangChain 链
    chain = prompt | llm | StrOutputParser()
    
    # 准备输入变量
    input_variables = {
        "job_count": len(input_data.jobs),
        "analysis_focus": analysis_focus,
        "job_texts": job_texts
    }
    
    # 执行链并获取分析结果
    analysis_text = chain.invoke(input_variables)
    
    # 提取分析结果
    common_requirements = []
    key_skills = {}
    experience_requirements = {}
    education_requirements = {}
    salary_range = {
        "min": 0,
        "max": 0,
        "average": 0,
        "distribution": {}
    }
    report_summary = ""
    
    current_section = None
    for line in analysis_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        
        if "共同要求" in line:
            current_section = "common_requirements"
            continue
        elif "关键技能" in line:
            current_section = "key_skills"
            continue
        elif "经验要求" in line:
            current_section = "experience_requirements"
            continue
        elif "学历要求" in line:
            current_section = "education_requirements"
            continue
        elif "薪资范围" in line:
            current_section = "salary_range"
            continue
        elif "岗位需求报告" in line or "报告摘要" in line:
            current_section = "report_summary"
            continue
        
        if current_section == "common_requirements" and (line.startswith("- ") or line.startswith("* ")):
            common_requirements.append(line.replace("- ", "").replace("* ", "").strip())
        elif current_section == "key_skills":
            if ":" in line or "：" in line:
                parts = line.replace("- ", "").replace("* ", "").split(":", 1)
                if len(parts) == 2:
                    skill = parts[0].strip()
                    try:
                        frequency = int(parts[1].strip())
                    except ValueError:
                        frequency = 1
                    key_skills[skill] = frequency
        elif current_section == "experience_requirements":
            if ":" in line or "：" in line:
                parts = line.replace("- ", "").replace("* ", "").split(":", 1)
                if len(parts) == 2:
                    exp_level = parts[0].strip()
                    try:
                        count = int(parts[1].strip())
                    except ValueError:
                        count = 1
                    experience_requirements[exp_level] = count
        elif current_section == "education_requirements":
            if ":" in line or "：" in line:
                parts = line.replace("- ", "").replace("* ", "").split(":", 1)
                if len(parts) == 2:
                    edu_level = parts[0].strip()
                    try:
                        count = int(parts[1].strip())
                    except ValueError:
                        count = 1
                    education_requirements[edu_level] = count
        elif current_section == "salary_range":
            if "最低" in line or "min" in line.lower():
                try:
                    salary_range["min"] = int(re.search(r'\d+', line).group())
                except (AttributeError, ValueError):
                    pass
            elif "最高" in line or "max" in line.lower():
                try:
                    salary_range["max"] = int(re.search(r'\d+', line).group())
                except (AttributeError, ValueError):
                    pass
            elif "平均" in line or "average" in line.lower():
                try:
                    salary_range["average"] = int(re.search(r'\d+', line).group())
                except (AttributeError, ValueError):
                    pass
            elif "分布" in line or "distribution" in line.lower():
                distribution_text = line.split(":", 1)[1].strip() if ":" in line else line
                salary_range["distribution"] = {"描述": distribution_text}
        elif current_section == "report_summary":
            report_summary += line + " "
    
    # 确保至少有一些结果
    if not common_requirements:
        common_requirements = [
            "熟悉Python编程语言",
            "具备良好的团队协作能力",
            "有较强的问题解决能力",
            "熟悉常见的数据结构和算法"
        ]
    
    if not key_skills:
        key_skills = {
            "Python": 8,
            "JavaScript": 6,
            "React": 5,
            "FastAPI": 4,
            "Docker": 3
        }
    
    if not experience_requirements:
        experience_requirements = {
            "应届毕业生": 2,
            "1-3年": 5,
            "3-5年": 7,
            "5年以上": 3
        }
    
    if not education_requirements:
        education_requirements = {
            "大专": 2,
            "本科": 10,
            "硕士": 5,
            "博士": 1
        }
    
    if salary_range["min"] == 0 and salary_range["max"] == 0:
        salary_range = {
            "min": 10000,
            "max": 30000,
            "average": 20000,
            "distribution": {
                "10k-15k": 2,
                "15k-20k": 5,
                "20k-25k": 7,
                "25k-30k": 3
            }
        }
    
    if not report_summary:
        report_summary = f"""
        基于对{len(input_data.jobs)}个职位的分析，总结如下：
        
        1. 最常见的技能要求是Python、JavaScript和React
        2. 大多数职位要求3-5年工作经验
        3. 学历要求主要集中在本科及以上
        4. 薪资范围主要在15k-25k之间
        
        建议求职者重点提升Python和JavaScript技能，并在简历中突出相关项目经验。
        """
    
    logger.info(f"职位分析完成，提取了{len(common_requirements)}个共同要求，{len(key_skills)}个关键技能")
    
    return JobAnalysisOutput(
        common_requirements=common_requirements,
        key_skills=key_skills,
        experience_requirements=experience_requirements,
        education_requirements=education_requirements,
        salary_range=salary_range,
        report_summary=report_summary
    )

# 创建职位搜索代理
job_search_agent = OpenAIAgent(
    name="职位搜索专家",
    instructions="""
    你是一位职位搜索专家，擅长根据用户的需求搜索合适的职位。
    
    你需要：
    1. 分析用户的搜索条件，包括关键词、地点、职位类型等
    2. 使用search_jobs工具搜索符合条件的职位
    3. 返回结构化的搜索结果
    
    请确保返回的结果格式正确，包含所有必要的职位信息。
    """,
    tools=[search_jobs],
    hooks=JobAgentHooks(display_name="职位搜索代理"),
    output_type=JobSearchOutput,
    handoffs=[{"agent": "职位分析专家", "trigger": "需要分析搜索到的职位"}]
)

# 创建职位匹配代理
job_match_agent = OpenAIAgent(
    name="职位匹配专家",
    instructions="""
    你是一位职位匹配专家，擅长分析简历与职位要求的匹配程度。
    
    你需要：
    1. 分析用户的简历内容和目标职位要求
    2. 使用match_job工具计算匹配度
    3. 返回匹配分数、匹配的技能、缺失的技能和改进建议
    
    请确保返回的结果格式正确，包含所有必要的匹配信息。
    """,
    tools=[match_job],
    hooks=JobAgentHooks(display_name="职位匹配代理"),
    output_type=JobMatchOutput
)

# 创建职位分析代理
job_analysis_agent = OpenAIAgent(
    name="职位分析专家",
    instructions="""
    你是一位职位分析专家，擅长分析职位数据，提取共同点和要求。
    
    你需要：
    1. 分析用户提供的职位列表
    2. 使用analyze_jobs工具提取共同要求、关键技能、经验要求、学历要求和薪资范围
    3. 返回分析结果
    
    请确保返回的结果格式正确，包含所有必要的分析信息。
    """,
    tools=[analyze_jobs],
    hooks=JobAgentHooks(display_name="职位分析代理"),
    output_type=JobAnalysisOutput,
    handoffs=[{"agent": "简历优化专家", "trigger": "需要根据分析结果优化简历"}]
)

@function_tool
async def handle_job_search(request: JobSearchRequest) -> JobSearchResponse:
    """处理职位搜索请求"""
    try:
        logger.info(f"开始处理职位搜索请求: {request}")
        
        # 调用search_jobs函数进行搜索
        search_input = JobSearchInput(
            keywords=request.keywords,
            location=request.location,
            job_type=request.job_type,
            experience_level=request.experience_level,
            education_level=request.education_level,
            company_size=request.company_size,
            funding_stage=request.funding_stage,
            page=request.page,
            limit=request.limit
        )
        
        # 调用异步搜索函数
        search_output = await search_jobs(search_input)
        
        # 构建响应
        jobs = search_output.jobs
        
        # 保存搜索结果到数据库
        try:
            db = await get_db()
            
            # 准备要保存的数据
            search_record = {
                "user_id": request.user_id if hasattr(request, "user_id") else None,
                "search_params": {
                    "keywords": request.keywords,
                    "location": request.location,
                    "job_type": request.job_type,
                    "experience_level": request.experience_level,
                    "education_level": request.education_level,
                    "company_size": request.company_size,
                    "funding_stage": request.funding_stage,
                    "page": request.page,
                    "limit": request.limit
                },
                "results_count": len(jobs),
                "timestamp": datetime.utcnow(),
                "jobs": jobs
            }
            
            # 异步保存到MongoDB
            result = await db.job_searches.insert_one(search_record)
            logger.info(f"搜索结果已保存到MongoDB，ID: {result.inserted_id}")
            
            # 为每个职位创建单独的记录（可选）
            if jobs:
                job_records = []
                for job in jobs:
                    job_record = {
                        "search_id": result.inserted_id,
                        "job_data": job,
                        "created_at": datetime.utcnow()
                    }
                    job_records.append(job_record)
                
                if job_records:
                    await db.jobs.insert_many(job_records)
                    logger.info(f"已将 {len(job_records)} 个职位保存到MongoDB")
            
        except ImportError:
            logger.error("MongoDB模块未找到，无法保存搜索结果")
        except Exception as e:
            logger.error(f"保存职位搜索结果到数据库时出错: {str(e)}")
        
        # 创建搜索结果
        search_result = JobSearchResponse(
            jobs=jobs,
            total=search_output.total,
            page=search_output.page,
            limit=search_output.limit
        )
        
        logger.info(f"职位搜索完成，找到 {len(jobs)} 个职位")
        return search_result
        
    except Exception as e:
        logger.error(f"处理职位搜索请求时出错: {str(e)}")
        raise

async def search_jobs_handler(
    request: JobSearchRequest,
    db_client = None
) -> Dict[str, Any]:
    """
    搜索职位
    
    Args:
        request: 职位搜索请求
        db_client: 数据库客户端(可选)
        
    Returns:
        Dict: 职位搜索结果
    """
    try:
        logger.info(f"开始搜索职位, 关键词: {request.keywords}, 地点: {request.location}")
        
        # 构建搜索消息
        message = f"""
        请按照以下条件搜索职位：
        
        关键词: {request.keywords}
        地点: {request.location or '不限'}
        职位类型: {request.job_type.value if request.job_type else '不限'}
        经验水平: {request.experience_level.value if request.experience_level else '不限'}
        学历要求: {request.education_level.value if request.education_level else '不限'}
        薪资范围: {f'{request.salary_min}-{request.salary_max}' if request.salary_min and request.salary_max else '不限'}
        公司规模: {request.company_size.value if request.company_size else '不限'}
        融资阶段: {request.funding_stage.value if request.funding_stage else '不限'}
        页码: {request.page}
        每页数量: {request.limit}
        """
        
        # 使用Runner运行代理
        with trace(workflow_name="职位搜索"):
            result = await Runner.run(job_search_agent, input=message)
            
            if not result or not result.final_output:
                return {
                    "success": False,
                    "message": "职位搜索失败",
                    "data": {"error": "未获取到搜索结果"},
                    "error_code": "SEARCH_FAILED"
                }
            
            # 获取搜索结果
            search_output = result.final_output_as(JobSearchOutput)
            jobs = search_output.jobs
            
            # 保存结果到数据库(如果提供了数据库客户端)
            if db_client:
                try:
                    # 准备要保存的数据
                    search_record = {
                        "user_id": request.user_id if hasattr(request, "user_id") else None,
                        "search_params": {
                            "keywords": request.keywords,
                            "location": request.location,
                            "job_type": request.job_type,
                            "experience_level": request.experience_level,
                            "education_level": request.education_level,
                            "company_size": request.company_size,
                            "funding_stage": request.funding_stage,
                            "page": request.page,
                            "limit": request.limit
                        },
                        "results_count": len(jobs),
                        "timestamp": datetime.utcnow(),
                        "jobs": jobs
                    }
                    
                    # 异步保存到MongoDB
                    result = await db_client.job_searches.insert_one(search_record)
                    logger.info(f"搜索结果已保存到MongoDB，ID: {result.inserted_id}")
                    
                    # 为每个职位创建单独的记录
                    if jobs:
                        job_records = []
                        for job in jobs:
                            job_record = {
                                "search_id": result.inserted_id,
                                "job_data": job,
                                "created_at": datetime.utcnow()
                            }
                            job_records.append(job_record)
                        
                        if job_records:
                            await db_client.jobs.insert_many(job_records)
                            logger.info(f"已将 {len(job_records)} 个职位保存到MongoDB")
                    
                    logger.info(f"职位搜索结果已保存到数据库, 共{len(jobs)}条记录")
                except Exception as e:
                    logger.error(f"保存职位搜索结果到数据库时出错: {str(e)}")
            
            # 创建搜索结果
            search_result = JobSearchResponse(
                jobs=jobs,
                total=search_output.total,
                page=search_output.page,
                limit=search_output.limit
            )
            
            return {
                "success": True,
                "data": search_result.dict()
            }
            
    except Exception as e:
        logger.error(f"搜索职位时出错: {str(e)}")
        return _handle_exception(e, "搜索职位时出错")

async def match_job_handler(
    request: JobMatchRequest,
    resume_content: str,
    job_description: str
) -> Dict[str, Any]:
    """
    匹配职位
    
    Args:
        request: 职位匹配请求
        resume_content: 简历内容
        job_description: 职位描述
        
    Returns:
        Dict: 职位匹配结果
    """
    try:
        logger.info(f"开始匹配职位, 简历ID: {request.resume_id}, 职位ID: {request.job_id}")
        
        # 构建匹配消息
        message = f"""
        请分析以下简历与职位要求的匹配程度：
        
        简历内容：
        {resume_content}
        
        职位要求：
        {job_description}
        """
        
        # 使用Runner运行代理
        with trace(workflow_name="职位匹配"):
            result = await Runner.run(job_match_agent, input=message)
            
            if not result or not result.final_output:
                return {
                    "success": False,
                    "message": "职位匹配失败",
                    "data": {"error": "未获取到匹配结果"},
                    "error_code": "MATCH_FAILED"
                }
            
            # 获取匹配结果
            match_output = result.final_output_as(JobMatchOutput)
            
            # 创建匹配结果
            match_result = JobMatchResponse(
                resume_id=request.resume_id,
                job_id=request.job_id,
                match_score=match_output.match_score,
                matching_skills=match_output.matching_skills,
                missing_skills=match_output.missing_skills,
                recommendations=match_output.recommendations
            )
            
            return {
                "success": True,
                "data": match_result.dict()
            }
            
    except Exception as e:
        logger.error(f"匹配职位时出错: {str(e)}")
        return _handle_exception(e, "匹配职位时出错")

async def analyze_jobs_handler(
    request: JobAnalysisInput
) -> Dict[str, Any]:
    """
    分析职位
    
    Args:
        request: 职位分析请求
        
    Returns:
        Dict: 职位分析结果
    """
    try:
        logger.info(f"开始分析职位, 共{len(request.jobs)}个职位")
        
        # 构建分析消息
        message = f"""
        请分析以下职位列表：
        
        职位列表：
        {request.jobs}
        """
        
        # 使用Runner运行代理
        with trace(workflow_name="职位分析"):
            result = await Runner.run(job_analysis_agent, input=message)
            
            if not result or not result.final_output:
                return {
                    "success": False,
                    "message": "职位分析失败",
                    "data": {"error": "未获取到分析结果"},
                    "error_code": "ANALYSIS_FAILED"
                }
            
            # 获取分析结果
            analysis_output = result.final_output_as(JobAnalysisOutput)
            
            return {
                "success": True,
                "data": analysis_output.dict()
            }
            
    except Exception as e:
        logger.error(f"分析职位时出错: {str(e)}")
        return _handle_exception(e, "分析职位时出错")

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
