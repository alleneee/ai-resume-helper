import asyncio
import logging
import os
import json
from typing import List, Optional, Dict, Any

# 导入 Agent SDK 的 function_tool 装饰器
try:
    # 尝试从 agents.tool 或 agents 导入
    try:
        from agents.tool import function_tool
    except ImportError:
        from agents import function_tool
except ImportError:
    # 如果都失败，提供占位符
    def function_tool(func):
        return func
    logging.warning("Could not import 'function_tool'. Using placeholder.")

# 导入 RunContextWrapper 用于在工具函数中访问上下文
try:
    from agents import RunContextWrapper
    run_context_available = True
except ImportError:
    logging.error("Failed to import 'RunContextWrapper'. Tool will not be able to access context.")
    run_context_available = False
    # Define placeholder if import fails
    class RunContextWrapper:
        def __init__(self, context=None):
            self.context = context

# 导入 browser-use 相关模块
try:
    from browser_use import Agent as BrowserAgent
    browser_use_available = True
except ImportError:
    logging.error("Failed to import 'browser-use'. Tool will not function.")
    browser_use_available = False
    # Define placeholders if import fails
    BrowserAgent = object

# 导入 Pydantic 模型 (使用相对导入)
from ..models import JobSearchCriteria, JobPosting, JobPostingList # Changed to relative import (up one level)

# 配置日志
logger = logging.getLogger(__name__)

# --- 浏览器搜索工具实现 ---

# --- _extract_json_string_from_result 函数已被删除 ---


@function_tool
async def run_browser_job_search(
    run_context: RunContextWrapper,  # 移到第一个位置
    criteria: JobSearchCriteria,
    target_site_url: str, # URL 由 Agent 确定并传入
    target_site_name: str,
) -> List[JobPosting]: # 返回 JobPosting 列表
    """
    使用 browser-use Agent 在指定的招聘网站上搜索职位。
    Access dependencies through the passed run_context parameter.

    Args:
        run_context: RunContextWrapper containing the app context with browser, controller, and llm.
        criteria: JobSearchCriteria object.
        target_site_url: Target website URL (determined by the calling Agent).
        target_site_name: Target website name.

    Returns:
        List of JobPosting objects, or an empty list on error.
    """
    # 检查依赖和上下文
    if not browser_use_available:
        logger.error("browser-use not available.")
        return []
    
    if not run_context or not run_context.context:
        logger.error("RunContextWrapper or its context is None.")
        return []
    
    # 从 run_context.context 中获取 browser, controller, llm
    app_context = run_context.context
    if not hasattr(app_context, "browser") or not hasattr(app_context, "controller"):
        logger.error("App context missing required attributes (browser, controller).")
        return []
    
    browser = app_context.browser
    controller = app_context.controller
    
    if not browser or not controller:
        logger.error("Browser or controller is None in the provided context.")
        return []

    # --- 构建 browser-use Agent 的任务描述 ---
    location = criteria.location or "全国"
    keywords = "、".join(criteria.keywords)
    limit = criteria.limit

    # 优化后的 Task description
    task = f"""
    你是一个精通 {target_site_name} 网站结构的网络爬虫专家。
    任务：从指定的 URL 提取最多 {limit} 个职位信息。

    步骤：
    1. **导航**: 直接访问这个 URL: {target_site_url}
    2. **等待加载**: 等待页面主要内容加载完成。特别注意等待包含职位列表的容器元素出现，例如 class 为 'job-list-box' 或类似的元素。如果页面显示"加载中"或有骨架屏，请等待实际内容替换它们。
    3. **处理弹窗 (如果需要)**: 如果出现登录提示、APP下载横幅或其他干扰性弹窗，尝试找到并点击关闭按钮（通常是一个 'x' 图标）。
    4. **提取信息**: 遍历页面上的职位列表项（例如 class 可能为 'job-card-wrapper', 'job-primary' 等）。对于每个职位项，提取以下信息：
       - **职位名称 (title)**: 通常在 'job-name' 相关的 class 里。
       - **公司名称 (company_name)**: 通常在 'company-text' 相关的 class 里。
       - **薪资范围 (salary_range)**: 通常在 'salary' 相关的 class 里。
       - **工作地点 (location)**: 通常在职位卡片头部区域或公司信息旁边。
       - **职位详情链接 URL (url)**: 获取整个职位卡片或标题的 'href' 属性，并确保它是完整的 URL (如果需要，拼接上 'https://www.zhipin.com')。
       - **经验要求 (experience_level)**: 查找类似 '经验不限', '1-3年' 等文本。
       - **学历要求 (education_level)**: 查找类似 '本科', '硕士' 等文本。
       - **职位描述 (description)**: 尝试查找是否有简短的职位描述或标签 (tags)。如果没有明显描述，此项可为空。
    5. **格式化**: 将每个提取到的职位信息整理成 JSON 对象，确保 keys 与 JobPosting 模型字段 ('title', 'company_name', 'salary_range', 'location', 'url', 'experience_level', 'education_level', 'description') 一致。
    6. **限制数量**: 最多提取 {limit} 个职位信息。
    7. **返回结果**: 最终根据 controller 配置的 schema (JobPostingList)，将提取到的职位 JSON 对象列表进行结构化返回。如果未找到任何职位，返回一个空列表 (`[]`)。

    请严格按照步骤执行，并注意页面元素 class 名称可能会变化，需要灵活适应。
    """
    logger.info(f"为 browser-use 构建的任务 (目标URL: {target_site_url}): {task[:200]}...") # 增加日志预览长度

    # --- 运行 browser-use Agent ---
    job_postings_list: List[JobPosting] = []
    try:
        # 使用上下文中的实例
        browser_agent = BrowserAgent(
            task=task,
            llm=None,  # llm 由 browser-use 内部处理
            controller=controller,
            browser=browser
        )
        logger.info(f"开始运行 browser-use Agent 搜索 (URL: {target_site_url})，超时设置为 300 秒")
        # 增加超时时间到 300 秒
        run_result = await asyncio.wait_for(browser_agent.run(), timeout=300.0)

        logger.info(f"browser-use Agent 运行完成。尝试处理结果... Type: {type(run_result)}")

        # --- 结果处理 --- 
        if isinstance(run_result, JobPostingList):
            job_postings_list = run_result.jobs
            logger.info(f"成功接收到 JobPostingList，包含 {len(job_postings_list)} 个职位。")
        elif isinstance(run_result, dict) and 'jobs' in run_result:
            try:
                validated_list = [JobPosting(**job_data) for job_data in run_result['jobs']]
                job_postings_list = validated_list
                logger.info(f"成功从字典结果解析了 {len(job_postings_list)} 个职位。")
            except Exception as pydantic_error:
                logger.error(f"无法将字典结果解析为 JobPosting 列表: {pydantic_error}", exc_info=True)
        # 可以保留对 AgentHistoryList 的处理逻辑，以防万一
        # elif isinstance(run_result, AgentHistoryList):
        #    logger.warning("Received AgentHistoryList. Implement specific extraction if needed.")
        #    # ... logic to extract from AgentHistoryList ...
        else:
            logger.warning(f"收到未预期的结果类型: {type(run_result)}. 无法提取职位。 Result: {str(run_result)[:500]}")

        # 应用数量限制
        if len(job_postings_list) > limit:
             job_postings_list = job_postings_list[:limit]
             logger.info(f"结果已截断至 {limit} 个职位")

        return job_postings_list

    except asyncio.TimeoutError:
        logger.error(f"浏览器搜索操作超时 (300s)")
        return []
    except Exception as e:
        logger.error(f"运行浏览器搜索时发生错误: {e}", exc_info=True)
        return []
    finally:
        # 注意：Browser 的关闭由调用方负责
        logger.debug(f"run_browser_job_search for {target_site_url} 完成")
        pass

# --- 测试代码 (可选) ---
# async def test_scraper_tool():
#     criteria = JobSearchCriteria(keywords=["后端开发"], location="深圳", limit=3)
#     print(f"测试搜索条件: {criteria}")
#     result = await run_browser_job_search(criteria)
#     print("\n--- run_browser_job_search 工具结果 ---")
#     print(result)
#     print("--------------------------------------")
#     try:
#         # 验证结果是否是有效的 JSON 列表
#         data = json.loads(result)
#         print(f"结果解析为列表，包含 {len(data)} 个项目。")
#         if data:
#             print("第一个项目:", data[0])
#     except Exception as e:
#         print(f"结果解析失败: {e}")
#
# if __name__ == "__main__":
#      logging.basicConfig(level=logging.INFO)
#      # 需要设置 OPENAI_API_KEY
#      # import os
#      # from dotenv import load_dotenv
#      # load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
#      # if not os.getenv("OPENAI_API_KEY"):
#      #      print("错误：请在 .env 文件中设置 OPENAI_API_KEY")
#      # else:
#      #      asyncio.run(test_scraper_tool())