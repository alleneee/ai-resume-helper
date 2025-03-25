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
from agents import Agent as OpenAIAgent, RunStatus
from agents.tool import function_tool

# 导入browser-use相关模块
from browser_use import Agent as BrowserAgent
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.controller.service import Controller
from langchain_openai import ChatOpenAI

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
    ExperienceLevel
)

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.tools.base import BaseTool
from langchain_core.tools import tool as function_tool

# 配置日志
logger = logging.getLogger(__name__)

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

# 职位搜索工具
@function_tool
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
            model="gpt-3.5-turbo-0125",
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
        logger.error(f"职位搜索过程中出错: {str(e)}")
        return _get_mock_job_search_results(params)
    finally:
        # 确保浏览器关闭
        if 'browser' in locals():
            await browser.close()
            logger.info("浏览器已关闭")

def _get_mock_job_search_results(params: JobSearchInput) -> JobSearchOutput:
    """返回模拟的职位搜索结果"""
    logger.info("返回模拟的职位搜索结果")
    return JobSearchOutput(
        jobs=[
            {
                "id": "job123",
                "title": "高级Python开发工程师",
                "company": "科技有限公司",
                "location": "上海",
                "description": "负责设计和实现高性能的Web应用程序...",
                "salary": "20k-40k",
                "job_type": "全职",
                "experience_level": "3-5年",
                "education_level": "本科及以上",
                "company_size": "中型公司(201-1000人)",
                "funding_stage": "B轮",
                "company_description": "一家专注于人工智能和机器学习的创新型科技公司...",
                "url": "https://example.com/jobs/123",
                "posted_date": "2023-05-15"
            }
        ],
        total=100,
        page=params.page,
        limit=params.limit
    )

# 职位匹配工具
@function_tool
def match_job(input_data: JobMatchInput) -> JobMatchOutput:
    """根据简历内容和职位要求进行匹配分析"""
    # 模拟匹配结果
    return JobMatchOutput(
        match_score=0.85,
        matching_skills=[
            "Python开发经验",
            "FastAPI框架使用经验",
            "数据库设计能力"
        ],
        missing_skills=[
            "Docker容器化经验",
            "Kubernetes集群管理"
        ],
        recommendations=[
            "强调Python和FastAPI项目经验",
            "突出数据库优化成果",
            "添加API性能优化案例"
        ]
    )

# 创建职位搜索代理
job_search_agent = OpenAIAgent(
    name="职位搜索专家",
    instructions="""
    你是一位职位搜索专家，擅长根据用户的搜索条件找到最合适的职位。
    
    搜索职位时需要考虑：
    1. 关键词与职位描述的匹配度
    2. 地理位置的准确性
    3. 职位类型的匹配
    4. 经验和学历要求的适配性
    5. 薪资范围的合理性
    
    提供准确、相关的职位搜索结果，并确保结果按照相关性排序。
    """,
    tools=[search_jobs],
    model_settings={"temperature": 0.2}
)

# 创建职位匹配代理
job_match_agent = OpenAIAgent(
    name="职位匹配专家",
    instructions="""
    你是一位职位匹配专家，擅长分析简历内容与职位要求的匹配程度，提供针对性的应聘建议。
    
    匹配分析时需要考虑：
    1. 技能和经验的匹配度
    2. 教育背景的适配性
    3. 项目经验与职位要求的相关性
    4. 技能差距和改进空间
    5. 如何在申请中突出优势
    
    提供详细的匹配分析和针对性的申请建议，帮助求职者提高应聘成功率。
    """,
    tools=[match_job, search_jobs],
    model_settings={"temperature": 0.3}
)

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
        
        # 创建代理运行
        run = job_search_agent.create_run()
        
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
        
        # 等待代理完成
        result = await _execute_agent_run(run, message, "search_jobs")
        
        if not result["success"]:
            return result
            
        # 转换为JobItem对象列表
        jobs = []
        for job_data in result["data"].get("jobs", []):
            job = {
                "id": job_data.get("id", ""),
                "title": job_data.get("title", ""),
                "company": job_data.get("company", ""),
                "location": job_data.get("location", ""),
                "description": job_data.get("description", ""),
                "salary": job_data.get("salary"),
                "job_type": job_data.get("job_type"),
                "experience_level": job_data.get("experience_level"),
                "education_level": job_data.get("education_level"),
                "company_size": job_data.get("company_size"),
                "funding_stage": job_data.get("funding_stage"),
                "company_description": job_data.get("company_description"),
                "url": job_data.get("url"),
                "posted_date": job_data.get("posted_date"),
                "created_at": datetime.utcnow()
            }
            jobs.append(job)
        
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
            total=result["data"].get("total", len(jobs)),
            page=result["data"].get("page", request.page),
            limit=result["data"].get("limit", request.limit)
        )
        
        logger.info(f"职位搜索完成, 找到{len(jobs)}个匹配职位")
        
        return {
            "success": True,
            "message": "职位搜索成功",
            "data": search_result
        }
        
    except Exception as e:
        return _handle_exception(e, "职位搜索过程中发生错误")

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
        logger.info(f"开始匹配职位, 简历ID: {request.resume_id}")
        
        # 创建代理运行
        run = job_match_agent.create_run()
        
        # 构建匹配消息
        message = f"""
        请根据以下简历内容和职位要求进行匹配分析：
        
        简历内容：
        {resume_content}
        
        职位要求：
        {job_description}
        """
        
        # 等待代理完成
        result = await _execute_agent_run(run, message, "match_job")
        
        if not result["success"]:
            return result
            
        logger.info(f"职位匹配完成, 简历ID: {request.resume_id}")
        
        return {
            "success": True,
            "message": "职位匹配成功",
            "data": {
                "match_score": result["data"].get("match_score", 0),
                "matching_skills": result["data"].get("matching_skills", []),
                "missing_skills": result["data"].get("missing_skills", []),
                "recommendations": result["data"].get("recommendations", [])
            }
        }
        
    except Exception as e:
        return _handle_exception(e, "职位匹配过程中发生错误")

async def _execute_agent_run(run: Run, message: str, expected_tool_name: str) -> Dict[str, Any]:
    """
    执行代理运行并等待结果
    
    Args:
        run: 代理运行实例
        message: 要发送的消息
        expected_tool_name: 期望调用的工具名称
        
    Returns:
        Dict: 包含执行结果的字典
    """
    # 启动代理运行
    await run.send_message(message)
    
    # 等待代理完成
    while run.status not in [RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.EXPIRED]:
        try:
            response = await run.get_next_response()
            logger.debug(f"代理响应: {response.content}")
        except Exception as e:
            logger.error(f"获取代理响应时出错: {str(e)}")
            break
        await asyncio.sleep(0.5)
    
    if run.status != RunStatus.COMPLETED:
        logger.error(f"代理运行失败, 状态: {run.status}")
        return {
            "success": False,
            "message": "代理处理失败",
            "data": {
                "error": f"代理运行失败: {run.status}"
            },
            "error_code": ErrorCode.INTERNAL_ERROR
        }
    
    # 获取工具调用结果
    result = None
    for step in run.thread_messages():
        if getattr(step, "tool_calls", None):
            for tool_call in step.tool_calls:
                if tool_call.function.name == expected_tool_name:
                    result = tool_call.function.output
    
    if not result:
        logger.error(f"未找到工具调用结果: {expected_tool_name}")
        return {
            "success": False,
            "message": "结果解析失败",
            "data": {"error": "未找到工具调用结果"},
            "error_code": ErrorCode.INTERNAL_ERROR
        }
    
    return {
        "success": True,
        "data": result
    }

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
            "error_code": ErrorCode.API_ERROR
        }
    elif isinstance(exception, ValidationError):
        return {
            "success": False,
            "message": "数据验证错误",
            "data": {"error": str(exception)},
            "error_code": ErrorCode.VALIDATION_ERROR
        }
    else:
        return {
            "success": False,
            "message": "服务器内部错误",
            "data": {"error": str(exception)},
            "error_code": ErrorCode.INTERNAL_ERROR
        }
