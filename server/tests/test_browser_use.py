"""
测试browser-use的简单脚本 - 模拟查询Boss直聘
"""
import asyncio
import logging
import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from browser_use import Agent as BrowserAgent, Controller
from browser_use.browser.browser import Browser, BrowserConfig

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    # 获取OpenAI API密钥
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
        headless=False,  # 设置为False以显示浏览器窗口
        # 可以尝试连接到已经运行的Chrome浏览器
        # cdp_url='http://localhost:9222',  # 如果有已经运行的Chrome浏览器，可以取消注释这行
    )
    
    # 创建浏览器实例
    browser = Browser(config=browser_config)
    
    # 定义任务 - 查询Boss直聘上海地区的Java岗位
    task = """
    访问Boss直聘网站(https://www.zhipin.com)，并执行以下操作：
    1. 在首页找到城市选择选项，选择"上海"
    2. 在搜索框中输入"Java"并搜索
    3. 等待搜索结果加载完成
    4. 提取前5个职位的以下信息：
       - 职位名称
       - 公司名称
       - 薪资范围
       - 工作地点
       - 经验要求
       - 学历要求
    5. 将提取的信息整理成结构化的JSON格式返回
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
        logger.info("开始执行任务...")
        result = await browser_agent.run()
        
        # 输出结果
        logger.info("任务执行完成")
        print("\n" + "="*50)
        print("任务结果:")
        print(result)
        print("="*50 + "\n")
        
        # 尝试解析JSON结果并格式化输出
        try:
            import json
            json_result = json.loads(result)
            print("\n格式化的职位信息:")
            for i, job in enumerate(json_result, 1):
                print(f"\n--- 职位 {i} ---")
                for key, value in job.items():
                    print(f"{key}: {value}")
        except:
            # 如果结果不是有效的JSON，则跳过格式化
            pass
        
    except Exception as e:
        logger.error(f"执行任务时出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭浏览器
        await browser.close()
        logger.info("浏览器已关闭")

if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())
