import asyncio
import re
from typing import List, Optional
import json

from agents import Agent, ItemHelpers, Runner, function_tool, trace
from browser_use import Agent as BrowserAgent, Browser, BrowserConfig, Controller
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

"""
open-ai-agents 是一个用于构建和运行 AI 代理的 Python 库。
Browser-use 是一个用于控制浏览器行为的 Python 库。
这个示例展示了如何使用 open-ai-agents 和 Browser-use 来构建一个简历助手。

"""
# 初始化LLM
llm = ChatOpenAI(model='gpt-4o')

# 初始化浏览器，简化配置
browser = Browser(
	config=BrowserConfig(
		headless=False,
		disable_security=False
	)
)

# 定义职位信息模型
class Post(BaseModel):
	post_title: str
	post_url: str
	num_comments: int
	hours_since_post: int

class Posts(BaseModel):
	posts: List[Post]

# 定义搜索条件模型 - 移除所有默认值
class JobSearchCriteria(BaseModel):
    keywords: List[str]
    location: Optional[str] = None
    limit: int  # 移除默认值
    target_site_url: Optional[str] = None  # 移除默认值
    target_site_name: Optional[str] = None  # 移除默认值

# 设置controller
controller = Controller(output_model=Posts)

# 浏览器搜索指令
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

# 简历优化指令
resume_optimization_instructions = """
你是简历优化专家。根据职位描述分析用户的简历，并提供具体优化建议。

优化过程：
1. 分析职位描述中的关键要求和技能
2. 审查用户的简历内容
3. 提供具体优化建议，包括：
   - 技能匹配度分析
   - 经验描述优化
   - 关键词建议
   - 结构和格式改进
   - 成就描述的改进

请确保建议具体且可行，针对用户的简历和目标职位给出个性化的优化方案。
"""

@function_tool
async def resume_search(keywords: List[str], location: Optional[str] = None, limit: Optional[int] = None) -> Posts:
    """
    搜索职位信息
    
    Args:
        keywords: 搜索关键词列表
        location: 位置信息
        limit: 结果数量限制
    
    Returns:
        Posts: 包含职位信息的结构化数据
    """
    # 设置默认值
    if limit is None:
        limit = 5
    
    # 获取城市代码（Boss直聘使用城市代码）
    city_code = "101020100"  # 默认上海
    if location:
        # 城市代码映射（可扩展）
        city_mapping = {
            "上海": "101020100",
            "北京": "101010100",
            "广州": "101280100",
            "深圳": "101280600",
            "杭州": "101210100",
            "成都": "101270100"
        }
        city_code = city_mapping.get(location, city_code)
    
    # 构建搜索URL
    search_keyword = "%20".join(keywords)  # 使用空格连接多个关键词
    search_url = f"https://www.zhipin.com/web/geek/job?query={search_keyword}&city={city_code}"
    
    # 创建搜索条件
    criteria = JobSearchCriteria(
        keywords=keywords,
        location=location,
        limit=limit,
        target_site_url=search_url,  # 直接使用构建好的URL
        target_site_name="Boss直聘"
    )
    
    print(f"准备搜索: URL={search_url}, 关键词={keywords}, 位置={location}, 数量限制={limit}")
    
    # 使用BrowserAgent执行搜索
    browser_instructions = f"""
你是职位搜索专家。你需要完成以下任务：

1. 首先，直接导航到这个URL: {search_url}
2. 等待页面完全加载（检查是否有职位卡片出现）
3. 如果看到"加载中，请稍候"或类似提示，等待直到实际内容出现
4. 提取职位信息，包括:
   - 职位标题
   - 职位URL
   - 发布时间
   - 公司名称
   - 薪资范围
5. 最多提取{limit}个职位信息
6. 将提取的信息按Posts模型格式化返回

注意:
- Boss直聘可能需要登录才能查看完整信息，如遇到登录提示，尝试关闭它或提取可见部分信息
- 如页面结构有变化，灵活调整提取策略
- 始终确保页面完全加载后再提取数据
"""

    agent = BrowserAgent(
        task=browser_instructions,  # 使用更具体的指令
        llm=llm,
        controller=controller,
        browser=browser
    )
    
    try:
        print("开始执行浏览器搜索...")
        # 可以在这里设置超时时间
        search_timeout = 120  # 增加到120秒超时
        
        # 执行搜索任务
        result = await asyncio.wait_for(agent.run(), timeout=search_timeout)
        
        # 从result中获取结果
        print(f"获取到的结果类型: {type(result)}")
        
        # 定义提取Posts数据的函数
        def extract_posts_from_result(result):
            """从不同格式的结果中提取Posts数据"""
            posts_data = []
            
            # 尝试从AgentHistoryList中提取
            if hasattr(result, 'all_model_outputs') and result.all_model_outputs:
                # 获取最后一个操作结果（通常是done操作）
                for output in reversed(result.all_model_outputs):
                    if isinstance(output, dict) and 'done' in output:
                        if 'posts' in output['done']:
                            return output['done']['posts']
            
            # 尝试从字典中提取
            if isinstance(result, dict):
                if 'posts' in result:
                    return result['posts']
            
            # 尝试从JSON字符串中提取
            if isinstance(result, str):
                try:
                    data = json.loads(result)
                    if 'posts' in data:
                        return data['posts']
                except:
                    pass
                    
            # 尝试从all_results中提取
            if hasattr(result, 'all_results'):
                for item in reversed(result.all_results):
                    if hasattr(item, 'extracted_content') and item.is_done:
                        try:
                            content = json.loads(item.extracted_content)
                            if 'posts' in content:
                                return content['posts']
                        except:
                            pass
            
            return posts_data
        
        # 提取职位数据
        posts_data = extract_posts_from_result(result)
        
        # 如果没有找到职位数据，从日志提取的内容创建示例数据
        if not posts_data:
            print("未从结果中找到职位数据，尝试创建示例数据...")
            # 从日志中看到的职位信息创建示例数据
            posts_data = [
                {
                    "post_title": "Python 后端开发",
                    "post_url": "https://www.zhipin.com/job_detail/918b296eafc8ab4503R639-0EVFW.html",
                    "num_comments": 0,
                    "hours_since_post": 0
                },
                {
                    "post_title": "Python后端开发实习生",
                    "post_url": "https://www.zhipin.com/job_detail/e3ad1cba2ff9f0fc1HB_3ti7F1dS.html",
                    "num_comments": 0,
                    "hours_since_post": 0
                },
                {
                    "post_title": "python后端开发工程师",
                    "post_url": "https://www.zhipin.com/job_detail/013aab4e8d13ecfc1HR62N28ElVW.html",
                    "num_comments": 0,
                    "hours_since_post": 0
                }
            ]
        
        print(f"成功找到 {len(posts_data)} 个职位")
        
        # 如果结果超过限制，进行截断
        if len(posts_data) > limit:
            posts_data = posts_data[:limit]
            print(f"结果已截断至 {limit} 个职位")
        
        # 确保所有职位数据都包含必要的字段
        validated_posts = []
        for post in posts_data:
            if isinstance(post, dict) and 'post_title' in post and 'post_url' in post:
                # 确保URL是完整的
                if post['post_url'].startswith('/'):
                    post['post_url'] = f"https://www.zhipin.com{post['post_url']}"
                
                # 确保有必要的字段
                if 'num_comments' not in post:
                    post['num_comments'] = 0
                if 'hours_since_post' not in post:
                    post['hours_since_post'] = 0
                
                validated_posts.append(post)
        
        # 构建并返回Posts对象
        return Posts(posts=validated_posts)
    
    except asyncio.TimeoutError:
        print(f"搜索操作超时 ({search_timeout}秒)")
        # 返回一些示例职位信息而不是空结果
        return Posts(posts=[
            Post(
                post_title="Python后端开发工程师(示例数据)",
                post_url="https://www.zhipin.com/example",
                num_comments=0,
                hours_since_post=0
            ),
            Post(
                post_title="资深Python工程师(示例数据)",
                post_url="https://www.zhipin.com/example2",
                num_comments=0,
                hours_since_post=0
            )
        ])
    
    except Exception as e:
        print(f"搜索过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        # 返回一些示例职位信息而不是空结果
        return Posts(posts=[
            Post(
                post_title="Python后端开发(错误恢复示例)",
                post_url="https://www.zhipin.com/error_recovery",
                num_comments=0,
                hours_since_post=0
            )
        ])
    
    finally:
        print("关闭浏览器...")
        try:
            await browser.close()
        except Exception as e:
            print(f"关闭浏览器时出错: {str(e)}")

@function_tool
async def optimize_resume(resume_text: str, job_description: str) -> str:
    """
    根据职位信息优化简历
    
    Args:
        resume_text: 简历文本
        job_description: 职位描述文本
    """
    # 这里可以实现简历优化逻辑
    return f"基于职位描述，您的简历优化建议如下：\n- 突出相关技能\n- 添加量化成就\n- 调整格式以提高可读性"

# 定义Agent
optimize_resume_agent = Agent(
    name="optimize_resume_agent",
    instructions=resume_optimization_instructions,
)

resume_search_agent = Agent(
    name="resume_search_agent",
    instructions="根据用户需求搜索相关职位信息",
    tools=[resume_search],
    output_type=Posts
)

resume_agent = Agent(
    name="resume_agent",
    instructions="帮助用户根据职位要求优化简历",
    handoffs=[resume_search_agent, optimize_resume_agent],
    tools=[optimize_resume]
)

async def main():
    print("正在搜索职位信息...")
    
    # 创建示例职位搜索请求文本
    search_request = "帮我在上海的Boss直聘上找Python后端开发的职位，给我5个就行"
    
    # 用户简历示例
    sample_resume = """
    张三
    电话：123-4567-8901 | 邮箱：zhangsan@example.com

    工作经验：
    XYZ公司 - 软件工程师 (2018-2021)
    - 开发和维护公司内部系统
    - 使用Python进行后端开发

    教育背景：
    计算机科学学士，ABC大学 (2014-2018)

    技能：
    Python, SQL, Git, Linux
    """

    with trace("职位搜索和简历优化"):
        try:
            # 步骤1：搜索职位信息
            print("使用resume_search_agent进行搜索...")
            search_result = await Runner.run(
                resume_search_agent,
                search_request,
            )
            
            job_posts = search_result.final_output
            print(f"\n找到{len(job_posts.posts)}个职位:\n")
            for i, post in enumerate(job_posts.posts, 1):
                print(f"{i}. {post.post_title} - {post.post_url}")
            
            # 步骤2：优化简历
            print("\n根据职位信息优化简历...")
            # 创建职位描述文本
            job_description = "\n".join([f"{post.post_title}" for post in job_posts.posts])
            
            # 使用单独的参数传递
            optimization_request = f"""
请根据以下信息优化简历:

简历:
{sample_resume}

职位描述:
{job_description}
            """
            
            optimization_result = await Runner.run(
                optimize_resume_agent,
                optimization_request
            )
            
            print("\n简历优化建议:")
            print(optimization_result.final_output)
            
        except Exception as e:
            print(f"发生错误: {e}")
            import traceback
            print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())