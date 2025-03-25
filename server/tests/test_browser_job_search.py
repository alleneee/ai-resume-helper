"""
测试使用browser-use进行职位搜索
"""
import os
import asyncio
import logging
import json
from dotenv import load_dotenv
from datetime import datetime

# 导入browser-use相关模块
from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.controller.service import Controller
from langchain_openai import ChatOpenAI

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_job_search():
    """测试使用browser-use进行职位搜索"""
    try:
        logger.info("开始测试职位搜索功能...")
        
        # 获取环境变量
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.error("未找到OPENAI_API_KEY环境变量")
            return
        
        # 创建语言模型
        llm = ChatOpenAI(
            api_key=openai_api_key,
            model="gpt-4o",
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
        
        # 定义搜索参数
        keywords = "Java"
        location = "上海"
        limit = 5
        
        # 定义任务 - 在Boss直聘搜索职位
        task = f"""
        访问Boss直聘网站(https://www.zhipin.com)，并执行以下操作：
        1. 在首页找到城市选择选项，选择"{location}"
        2. 在搜索框中输入"{keywords}"并搜索
        3. 等待搜索结果加载完成
        4. 提取前{limit}个职位的以下信息：
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
        5. 将提取的信息整理成结构化的JSON格式返回
        """
        
        try:
            # 创建浏览器代理
            browser_agent = Agent(
                task=task,
                llm=llm,
                controller=controller,
                browser=browser
            )
            
            # 运行任务
            logger.info(f"开始搜索职位: 地点={location}, 关键词={keywords}")
            result = await browser_agent.run()
            
            # 调试输出，查看结果对象的结构
            logger.info(f"结果类型: {type(result)}")
            logger.info(f"结果属性: {dir(result)}")
            
            # 解析结果
            try:
                # 从browser-use的结果中提取JSON
                if hasattr(result, "result"):
                    # 如果结果对象有result属性
                    result_text = result.result
                    logger.info(f"从result属性提取: {type(result_text)}")
                elif hasattr(result, "output"):
                    # 如果结果对象有output属性
                    result_text = result.output
                    logger.info(f"从output属性提取: {type(result_text)}")
                elif hasattr(result, "history"):
                    # 如果结果对象有history属性
                    history = result.history
                    if history and len(history) > 0:
                        last_item = history[-1]
                        if hasattr(last_item, "output"):
                            result_text = last_item.output
                            logger.info(f"从history[-1].output提取: {type(result_text)}")
                        else:
                            logger.error("history中最后一项没有output属性")
                            return None
                    else:
                        logger.error("history为空")
                        return None
                else:
                    # 直接使用字符串表示
                    result_text = str(result)
                    logger.info(f"使用字符串表示: {type(result_text)}")
                
                # 尝试从文本中提取JSON
                import re
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', result_text)
                if json_match:
                    json_str = json_match.group(1)
                    logger.info("成功从文本中提取JSON")
                    json_result = json.loads(json_str)
                else:
                    # 如果没有找到JSON格式，尝试直接解析整个文本
                    try:
                        json_result = json.loads(result_text)
                        logger.info("直接解析文本为JSON成功")
                    except json.JSONDecodeError:
                        # 如果不是JSON格式，尝试从文本中提取职位信息
                        logger.info("尝试从文本中提取职位信息")
                        job_listings = []
                        
                        # 简单的正则表达式来提取职位信息
                        job_pattern = r'\*\*Job ID\*\*: ([^\n]*)\s*\n\s*- \*\*Job Title\*\*: ([^\n]*)\s*\n\s*- \*\*Company Name\*\*: ([^\n]*)\s*\n\s*- \*\*Salary Range\*\*: ([^\n]*)\s*\n\s*- \*\*Location\*\*: ([^\n]*)\s*\n\s*- \*\*Experience Requirement\*\*: ([^\n]*)\s*\n\s*- \*\*Education Requirement\*\*: ([^\n]*)\s*\n\s*- \*\*Company Size\*\*: ([^\n]*)\s*\n\s*- \*\*Financing Stage\*\*: ([^\n]*)\s*\n\s*- \*\*Job Description Summary\*\*: ([^\n]*)\s*\n\s*- \*\*Job Link\*\*: \[Link\]\(([^\)]*)\)\s*\n\s*- \*\*Posting Date\*\*: ([^\n]*)'
                        
                        for match in re.finditer(job_pattern, result_text):
                            job = {
                                "job_id": match.group(1),
                                "job_title": match.group(2),
                                "company_name": match.group(3),
                                "salary_range": match.group(4),
                                "location": match.group(5),
                                "experience_requirement": match.group(6),
                                "education_requirement": match.group(7),
                                "company_size": match.group(8),
                                "financing_stage": match.group(9),
                                "job_description_summary": match.group(10),
                                "job_link": match.group(11),
                                "posting_date": match.group(12)
                            }
                            job_listings.append(job)
                        
                        if job_listings:
                            json_result = {"job_listings": job_listings}
                            logger.info(f"从文本中提取到 {len(job_listings)} 个职位")
                        else:
                            logger.error("无法从文本中提取职位信息")
                            # 保存原始文本以便调试
                            with open("result_text.txt", "w") as f:
                                f.write(result_text)
                            logger.info("已将原始文本保存到result_text.txt")
                            return None
                
                # 打印结果
                logger.info(f"搜索完成，找到 {len(json_result.get('job_listings', []))} 个职位")
                for i, job in enumerate(json_result.get("job_listings", []), 1):
                    logger.info(f"\n--- 职位 {i} ---")
                    logger.info(f"职位名称: {job.get('job_title')}")
                    logger.info(f"公司名称: {job.get('company_name')}")
                    logger.info(f"薪资范围: {job.get('salary_range')}")
                    logger.info(f"工作地点: {job.get('location')}")
                    logger.info(f"经验要求: {job.get('experience_requirement')}")
                    logger.info(f"学历要求: {job.get('education_requirement')}")
                
                # 尝试连接MongoDB并保存数据
                try:
                    from server.database.mongodb import get_db
                    
                    # 获取MongoDB连接
                    db = await get_db()
                    
                    # 准备要保存的数据
                    search_record = {
                        "search_params": {
                            "keywords": keywords,
                            "location": location,
                            "limit": limit
                        },
                        "results_count": len(json_result.get("job_listings", [])),
                        "timestamp": datetime.utcnow(),
                        "jobs": json_result.get("job_listings", [])
                    }
                    
                    # 保存到MongoDB
                    result = await db.job_searches.insert_one(search_record)
                    logger.info(f"搜索结果已保存到MongoDB，ID: {result.inserted_id}")
                    
                    # 为每个职位创建单独的记录
                    job_records = []
                    for job in json_result.get("job_listings", []):
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
                    logger.warning("MongoDB模块未找到，跳过数据保存")
                except Exception as e:
                    logger.error(f"保存到MongoDB时出错: {str(e)}")
                
                return json_result
                
            except Exception as e:
                logger.error(f"解析结果时出错: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"执行职位搜索任务时出错: {str(e)}")
            return None
            
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # 确保浏览器关闭
        if 'browser' in locals():
            await browser.close()
            logger.info("浏览器已关闭")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_job_search())
