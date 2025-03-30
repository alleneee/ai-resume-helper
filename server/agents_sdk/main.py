import asyncio
import logging
import json
import os
from typing import Optional, List, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import pymongo
from pymongo.errors import ConnectionFailure as MongoConnectionError

# MongoDB配置
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "resume_helper")
MONGO_COLLECTION_NAME = "job_postings_cache"
CACHE_EXPIRATION_HOURS = 24  # 缓存24小时后过期

# 导入 Agent Runner 和定义的 Agents (使用用户提供的导入)
try:
    from agents import Agent, ItemHelpers, MessageOutputItem, Runner, trace # Updated import
    from agents import RunContextWrapper  # 导入 RunContextWrapper
    from .agents.scraper_agent import ScraperAgent
    from .agents.analyzer_agent import AnalyzerAgent
    from .agents.optimizer_agent import ResumeOptimizerAgent
    # Check if base Agent class was imported correctly for other agents
    agents_available = ScraperAgent and AnalyzerAgent and ResumeOptimizerAgent is not None and Runner is not None
except ImportError as e:
    logging.error(f"无法导入 Agents 或 Runner: {e}. 管道将无法运行。")
    agents_available = False
    # Placeholders
    Agent = object
    ItemHelpers = object
    MessageOutputItem = object
    Runner = None
    trace = None
    ScraperAgent = None
    AnalyzerAgent = None
    ResumeOptimizerAgent = None
    RunContextWrapper = None

# 尝试导入 browser-use 相关模块
try:
    from browser_use import Browser, Controller, BrowserConfig
    browser_use_available = True
except ImportError:
    logging.error("无法导入 browser-use 模块。爬虫功能将无法工作。")
    browser_use_available = False
    # 定义占位符
    Browser = object
    Controller = object
    BrowserConfig = object

# 导入 Pydantic 模型
from .models import (
    JobSearchCriteria,
    JobPosting,
    ResumeData,
    AnalysisResult,
    OptimizedResume,
    JobPostingList
)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 自定义上下文类
@dataclass
class AppContext:
    """应用上下文，包含依赖注入的共享实例"""
    llm: Any = None  # LLM 实例
    browser: Any = None  # Browser 实例
    controller: Any = None  # Controller 实例

# 初始化上下文的函数
async def initialize_resources(headless_mode: bool = True) -> AppContext:
    """
    初始化应用程序资源
    
    Args:
        headless_mode: 是否以无头模式运行浏览器
        
    Returns:
        AppContext: 包含初始化好的资源
    """
    context = AppContext()
    
    if browser_use_available:
        try:
            # 初始化 Controller 和输出模型
            context.controller = Controller(output_model=JobPostingList)
            
            # 初始化 Browser，使用 BrowserConfig
            browser_config = BrowserConfig(
                headless=headless_mode,
                disable_security=False
            )
            context.browser = Browser(config=browser_config)
            # await context.browser.start() # Browser 对象不需要显式启动
            logger.info("浏览器已成功初始化")
            
            # LLM 由 agent-sdk 内部创建和管理
        except Exception as e:
            logger.error(f"初始化浏览器资源时出错: {e}", exc_info=True)
    else:
        logger.warning("browser-use 不可用，无法初始化浏览器资源")
    
    return context

# 关闭资源的函数
async def cleanup_resources(context: AppContext) -> None:
    """
    清理和关闭应用程序资源
    
    Args:
        context: 应用上下文实例
    """
    if context.browser:
        try:
            await context.browser.close()
            logger.info("浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器时出错: {e}")

# --- 编排逻辑 ---

async def run_resume_optimization_pipeline(
    resume_data: ResumeData,
    search_criteria: JobSearchCriteria,
    app_context: AppContext,
    target_site_url: str = "https://www.zhipin.com/",
    target_site_name: str = "Boss直聘"
) -> Optional[OptimizedResume]:
    """
    运行完整的简历优化流程：爬取 -> 分析 -> 优化。

    Args:
        resume_data: 用户简历信息。
        search_criteria: 职位搜索条件。
        app_context: 应用上下文，包含共享资源。
        target_site_url: 目标网站 URL。
        target_site_name: 目标网站名称。

    Returns:
        优化后的简历对象或 None。
    """
    if not agents_available:
        logger.error("必要的 Agent 未被正确导入/创建，无法运行优化流程。")
        return None

    job_postings: List[JobPosting] = []
    analysis_result: Optional[AnalysisResult] = None
    optimized_resume: Optional[OptimizedResume] = None
    run_scraper = True

    # 创建上下文包装器
    context_wrapper = RunContextWrapper(context=app_context)

    # 步骤 0: 检查缓存
    logger.info("步骤 0: 检查职位信息缓存...")
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000) # 添加超时
        client.server_info() # 强制连接测试
        db = client[MONGO_DB_NAME]
        cache_collection = db[MONGO_COLLECTION_NAME]
        sorted_keywords = sorted(search_criteria.keywords)
        cache_query = {
            "keywords": sorted_keywords,
            "location": search_criteria.location,
            "timestamp": {"$gt": datetime.utcnow() - timedelta(hours=CACHE_EXPIRATION_HOURS)}
        }
        cached_results = cache_collection.find_one(cache_query, sort=[("timestamp", pymongo.DESCENDING)])
        if cached_results:
            cached_jobs = cached_results.get("job_postings", [])
            if cached_jobs:
                validated_cached_jobs = []
                for job_data in cached_jobs:
                    try:
                        validated_cached_jobs.append(JobPosting.model_validate(job_data))
                    except Exception as e:
                        logger.warning(f"缓存中的职位数据验证失败: {e}")
                if validated_cached_jobs:
                    job_postings = validated_cached_jobs
                    logger.info(f"从缓存中成功获取到 {len(job_postings)} 个有效职位信息")
                    run_scraper = False
    except MongoConnectionError as e:
        logger.warning(f"连接MongoDB失败 (缓存不可用): {e}")
    except Exception as e:
        logger.warning(f"检查缓存时发生错误: {e}")
    finally:
        if 'client' in locals():
            client.close()

    # 步骤 1: 爬取职位 (如果缓存无效)
    if run_scraper:
        logger.info(f"步骤 1: 开始使用 {target_site_name} 爬取职位...")
        scraper_input_prompt = (
            f"请帮我搜索职位信息。关键词是: {'、'.join(search_criteria.keywords)}。"
            f"地点: {search_criteria.location or '不限'}。"
            f"最多返回 {search_criteria.limit} 条结果。"
        )
        # 向 ScraperAgent 传递上下文包装器
        try:
            scraper_run_result = await Runner.run(ScraperAgent, scraper_input_prompt, context=app_context)
            if scraper_run_result.final_output and isinstance(scraper_run_result.final_output, list):
                validated_jobs = []
                for item in scraper_run_result.final_output:
                    try:
                        validated_jobs.append(JobPosting.model_validate(item))
                    except Exception as validation_error:
                        logger.warning(f"ScraperAgent 返回列表中的项无法验证为 JobPosting: {validation_error}. Item: {item}")
                job_postings = validated_jobs # 覆盖为空或旧的列表
                logger.info(f"ScraperAgent 成功返回并验证了 {len(job_postings)} 个职位信息。")
                
                # 更新缓存
                if job_postings:
                    try:
                        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
                        client.server_info()
                        db = client[MONGO_DB_NAME]
                        cache_collection = db[MONGO_COLLECTION_NAME]
                        job_postings_dicts = [job.model_dump() for job in job_postings]
                        cache_data = {
                            "keywords": sorted_keywords,
                            "location": search_criteria.location,
                            "target_site_url": target_site_url, # 使用传入的 URL
                            "timestamp": datetime.utcnow(),
                            "job_postings": job_postings_dicts 
                        }
                        cache_collection.update_one(
                            {"keywords": sorted_keywords, "location": search_criteria.location},
                            {"$set": cache_data}, upsert=True
                        )
                        logger.info("成功更新职位信息缓存")
                    except MongoConnectionError as e:
                         logger.warning(f"连接MongoDB失败 (无法更新缓存): {e}")
                    except Exception as e:
                        logger.warning(f"更新缓存时发生错误: {e}")
                    finally:
                        if 'client' in locals():
                            client.close()
            else:
                logger.warning("ScraperAgent 运行完成，但没有返回有效的职位列表。")
        except Exception as e:
            logger.error(f"运行 ScraperAgent 时发生严重错误: {e}", exc_info=True)

    # 检查是否有职位信息用于分析
    if not job_postings:
        logger.warning("未能获取到任何有效的职位信息，无法进行基于职位的分析和优化。流程可能无法继续或效果不佳。")
        # 可以选择返回 None 或进行无职位信息的优化
        # return None # 如果职位是必须的，取消注释此行

    # 步骤 2: 分析简历与职位 (恢复调用)
    logger.info(f"步骤 2: 开始分析简历与 {len(job_postings)} 个职位...")
    # 构建 Analyzer 的输入 Prompt
    analyzer_input_prompt = f"""请根据你的角色和任务要求，分析以下简历和职位描述。

    简历信息:
    ```json
    {resume_data.model_dump_json(indent=2, exclude_none=True)}
    ```

    目标职位信息:
    ```json
    {json.dumps([job.model_dump(exclude={'id'}) for job in job_postings], indent=2, ensure_ascii=False)}
    ```

    请严格按照 AnalysisResult 的 JSON 格式输出你的分析结果。
    """
    try:
        analyzer_run_result = await Runner.run(AnalyzerAgent, analyzer_input_prompt, context=app_context)
        if analyzer_run_result.final_output:
             # Agent 设置了 output_type=AnalysisResult，SDK 应该会自动解析
             try:
                 # 尝试使用 final_output_as 获取解析后的对象
                 analysis_result = analyzer_run_result.final_output_as(AnalysisResult)
                 logger.info("AnalyzerAgent 成功返回并解析了分析结果。")
             except Exception as parse_e:
                 logger.error(f"无法将 AnalyzerAgent 结果自动解析为 AnalysisResult: {parse_e}")
                 logger.warning("将尝试手动解析 JSON...")
                 try:
                     # 手动解析 final_output (它应该是 JSON 字符串)
                     analysis_result = AnalysisResult.model_validate_json(analyzer_run_result.final_output)
                     logger.info("手动解析 AnalyzerAgent 结果为 AnalysisResult 成功。")
                 except Exception as manual_parse_e:
                      logger.error(f"手动解析 AnalyzerAgent JSON 结果也失败了: {manual_parse_e}")
        else:
            logger.error("AnalyzerAgent 运行完成，但没有返回任何输出。")

    except Exception as e:
        logger.error(f"运行 AnalyzerAgent 时发生严重错误: {e}", exc_info=True)

    # 检查是否有分析结果用于优化
    if not analysis_result:
        logger.error("未能获取到有效的分析结果，无法进行优化。流程中止。")
        return None

    # 步骤 3: 优化简历
    logger.info("步骤 3: 基于分析结果优化简历...")
    # 构建 Optimizer 的输入 Prompt (使用原始简历和分析结果)
    optimizer_input_prompt = f"""请根据你的角色和任务要求，基于以下原始简历和分析结果，优化简历。

    原始简历:
    ```json
    {resume_data.model_dump_json(indent=2, exclude_none=True)}
    ```

    分析结果与建议:
    ```json
    {analysis_result.model_dump_json(indent=2, exclude_none=True)}
    ```

    请严格按照 OptimizedResume 的 JSON 格式输出你的优化结果，重点是 'optimized_text' 字段。请将原始简历和分析摘要也包含在输出的相应字段中。
    """
    try:
        optimizer_run_result = await Runner.run(ResumeOptimizerAgent, optimizer_input_prompt, context=app_context)
        if optimizer_run_result.final_output:
            # Agent 设置了 output_type=OptimizedResume，SDK 应该会自动解析
            try:
                # 尝试使用 final_output_as 获取解析后的对象
                optimized_resume = optimizer_run_result.final_output_as(OptimizedResume)
                logger.info("ResumeOptimizerAgent 成功返回并解析了优化结果。")
            except Exception as parse_e:
                logger.error(f"无法将 ResumeOptimizerAgent 结果自动解析为 OptimizedResume: {parse_e}")
                logger.warning("将尝试手动解析 JSON...")
                try:
                    # 手动解析 final_output (它应该是 JSON 字符串)
                    optimized_resume = OptimizedResume.model_validate_json(optimizer_run_result.final_output)
                    logger.info("手动解析 ResumeOptimizerAgent 结果为 OptimizedResume 成功。")
                except Exception as manual_parse_e:
                    logger.error(f"手动解析 ResumeOptimizerAgent JSON 结果也失败了: {manual_parse_e}")
        else:
            logger.error("ResumeOptimizerAgent 运行完成，但没有返回任何输出。")
            
    except Exception as e:
        logger.error(f"运行 ResumeOptimizerAgent 时发生严重错误: {e}", exc_info=True)
    
    return optimized_resume


# --- 主程序入口 (用于测试) ---
async def main():
    # !!! 确保 OPENAI_API_KEY 环境变量已设置 !!!
    if not os.getenv("OPENAI_API_KEY"):
        logger.critical("错误：请设置 OPENAI_API_KEY 环境变量!")
        return
    
    # 初始化共享资源
    app_context = await initialize_resources(headless_mode=True)
    
    try:
        # 准备示例输入数据
        resume = ResumeData(raw_text="""
        张三 - Python 开发工程师

        教育背景:
        某大学 - 计算机科学学士 (2015-2019)

        工作经验:
        B公司 (2021-至今) - Python 后端开发
        - 开发和维护公司核心业务系统的后端 API。
        - 使用 Django 和 Flask 框架。
        - 参与数据库设计 (MySQL)。
        A公司 (2019-2021) - 初级软件工程师
        - 参与开发内部管理工具。

        技能: Python, Django, Flask, MySQL, Git, Linux
        """)
        criteria = JobSearchCriteria(keywords=["Python", "后端开发"], location="上海", limit=5)

        logger.info("开始运行简历优化流程...")
        optimized_result = await run_resume_optimization_pipeline(
            resume_data=resume, 
            search_criteria=criteria,
            app_context=app_context
        )

        if optimized_result:
            logger.info("\n--- 最终优化结果 ---")
            print("优化后的简历文本:")
            print(optimized_result.optimized_text)
            # print(f"\n(基于 {optimized_result.analysis_summary.analyzed_jobs_count} 个职位分析)")
        else:
            logger.error("简历优化流程失败。")
    finally:
        # 清理资源
        await cleanup_resources(app_context)

# 脚本直接运行入口点
if __name__ == "__main__":
    asyncio.run(main())
