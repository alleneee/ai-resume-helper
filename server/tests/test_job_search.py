"""
测试职位搜索功能
"""
import os
import asyncio
import logging
from dotenv import load_dotenv
from datetime import datetime

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入需要测试的函数和模型
from server.services.agents.job_agent import search_jobs
from server.models.agent import JobSearchInput
from server.database.mongodb import get_db

async def test_search_jobs():
    """测试职位搜索功能"""
    try:
        logger.info("开始测试职位搜索功能...")
        
        # 创建测试输入
        search_input = JobSearchInput(
            keywords="Java",
            location="上海",
            limit=5
        )
        
        # 调用搜索函数
        logger.info(f"搜索条件: 关键词={search_input.keywords}, 地点={search_input.location}")
        result = await search_jobs(search_input)
        
        # 打印结果
        logger.info(f"搜索完成，找到 {len(result.jobs)} 个职位")
        for i, job in enumerate(result.jobs, 1):
            logger.info(f"\n--- 职位 {i} ---")
            logger.info(f"职位名称: {job.get('title')}")
            logger.info(f"公司名称: {job.get('company')}")
            logger.info(f"薪资范围: {job.get('salary')}")
            logger.info(f"工作地点: {job.get('location')}")
            logger.info(f"经验要求: {job.get('experience_level')}")
            logger.info(f"学历要求: {job.get('education_level')}")
        
        # 验证数据是否保存到MongoDB
        logger.info("\n验证数据是否保存到MongoDB...")
        db = await get_db()
        
        # 查询最近的搜索记录
        search_record = await db.job_searches.find_one(
            {"search_params.keywords": search_input.keywords},
            sort=[("timestamp", -1)]
        )
        
        if search_record:
            logger.info(f"找到搜索记录，ID: {search_record.get('_id')}")
            logger.info(f"搜索结果数量: {search_record.get('results_count')}")
            
            # 查询关联的职位记录
            job_count = await db.jobs.count_documents({"search_id": search_record.get("_id")})
            logger.info(f"关联的职位记录数量: {job_count}")
            
            # 验证数据一致性
            if job_count == len(result.jobs):
                logger.info("✅ 数据一致性验证通过！")
            else:
                logger.warning(f"❌ 数据一致性验证失败: 搜索结果有 {len(result.jobs)} 个职位，但数据库中有 {job_count} 个职位")
        else:
            logger.warning("❌ 未找到搜索记录，数据可能未保存到MongoDB")
        
        return result
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_search_jobs())
