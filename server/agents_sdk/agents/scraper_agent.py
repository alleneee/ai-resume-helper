import logging
from typing import List
import json # Import json for potential input parsing if needed

# 导入 Agent 基类
try:
    from agents import Agent
except ImportError:
    Agent = object
    logging.warning("Could not import 'Agent' from 'agents'. Using placeholder.")

# 导入所需的 Pydantic 模型 (用于理解输入和输出)
from server.agents_sdk.models import JobSearchCriteria, JobPosting

# 导入新的浏览器搜索工具
try:
    from server.agents_sdk.tools.scraper_tool import run_browser_job_search
    scraper_tool_available = True
except ImportError as e:
    logging.error(f"Failed to import run_browser_job_search tool: {e}. ScraperAgent will have no tools.")
    run_browser_job_search = None # Placeholder
    scraper_tool_available = False

logger = logging.getLogger(__name__)

# --- 定义 Scraper Agent (修订版) ---

# 新的工具列表，只包含高级工具
scraper_tools = []
if scraper_tool_available:
    scraper_tools.append(run_browser_job_search)

# 新的简化指令
# 指导 Agent 如何理解请求并调用工具
scraper_instructions = """
你是职位信息聚合代理。你的任务是理解用户的职位搜索请求，提取关键信息（关键词、地点、数量限制等），然后调用 `run_browser_job_search` 工具来执行实际的搜索和爬取。

可用工具：
- `run_browser_job_search(criteria: JobSearchCriteria, target_site_url: str, target_site_name: str)`: (注意：此工具现在没有默认参数了)
    - 这个工具会使用浏览器代理在指定的招聘网站上搜索职位。
    - 你需要将用户请求中的关键词、地点、数量限制等信息构造成一个 `JobSearchCriteria` 对象传递给 `criteria` 参数。
    - `criteria` 参数需要包含 `keywords` (list[str]), `location` (Optional[str]), `limit` (int), `other_filters` (Optional[dict]) 字段。
    - 你必须根据用户请求或常识明确提供 `target_site_url` 和 `target_site_name`。例如，如果用户提到"Boss直聘"，则使用 `target_site_url='https://www.zhipin.com/'` 和 `target_site_name='Boss直聘'`。
    - **重要：这个工具现在直接返回一个 `JobPosting` 对象的列表 (`List[JobPosting]`)，而不是 JSON 字符串。**

工作流程：
1.  分析用户的自然语言请求，识别出搜索的**关键词** (可能是一个或多个)、**地点** (如果提供)、**数量限制** (如果没有明确说明，可以使用默认值，例如 5 或 10) 以及 **目标网站** (如果提供)。
2.  **构造 `JobSearchCriteria` 对象:** 将提取的信息填充到 `JobSearchCriteria` 模型的字段中。
3.  **确定目标网站:** 从用户请求或常识中确定 `target_site_url` 和 `target_site_name`。如果没有明确指定，可以使用 Boss 直聘作为默认。
4.  **调用工具:** 调用 `run_browser_job_search` 工具，传递构造好的 `JobSearchCriteria` 对象、`target_site_url` 和 `target_site_name`。
5.  **输出结果:** **将 `run_browser_job_search` 工具返回的 `List[JobPosting]` 对象直接作为你的最终输出 (`final_output`)。不要进行任何转换或添加解释。**

示例用户请求: "帮我在上海的 Boss 直聘上找找 Python 后端开发的职位，要最近发布的，给我 5 个就行。"
你需要提取: keywords=["Python", "后端开发"], location="上海", limit=5, target_site_url='https://www.zhipin.com/', target_site_name='Boss直聘'
然后调用 `run_browser_job_search(criteria=JobSearchCriteria(keywords=['Python', '后端开发'], location='上海', limit=5), target_site_url='https://www.zhipin.com/', target_site_name='Boss直聘')`

请确保准确提取参数并正确调用工具，并将工具返回的列表直接作为最终输出。
"""

# 创建 ScraperAgent 实例 (修订版)
try:
    # 确保 Agent SDK 能够处理只有一个工具的情况
    ScraperAgent = Agent(
        name="JobScraperAgent",
        instructions=scraper_instructions,
        tools=scraper_tools,
        # 指定期望的最终输出类型为列表
        output_type=List[JobPosting] 
    )
    logger.info("ScraperAgent 定义完成 (使用 run_browser_job_search 工具，期望 List[JobPosting] 输出)")
except Exception as e:
     logger.error(f"创建 ScraperAgent 失败: {e}")
     ScraperAgent = None



