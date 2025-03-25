"""
测试agent_service.py中的爬取功能 - 真实请求版本
"""
import asyncio
import os
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.agent_service import AgentService

# 真实的职位URL示例
REAL_JOB_URLS = [
    "https://www.linkedin.com/jobs/view/3839893362",  # LinkedIn职位
    "https://jobs.bytedance.com/referral/pc/position/7358830398693773623/detail",  # 字节跳动职位
    "https://careers.tencent.com/jobdesc.html?postId=1394780860745367552"  # 腾讯职位
]

# 测试职位数据
TEST_JOB_DATA = [
    {
        "id": "job123",
        "title": "Python开发工程师",
        "company": "LinkedIn",
        "location": "北京",
        "url": REAL_JOB_URLS[0],
        "description": "这是一个Python开发工程师职位",
        "salary": "25k-35k"
    },
    {
        "id": "job456",
        "title": "前端开发工程师",
        "company": "字节跳动",
        "location": "上海",
        "url": REAL_JOB_URLS[1],
        "description": "这是一个前端开发工程师职位",
        "salary": "30k-45k"
    },
    {
        "id": "job789",
        "title": "产品经理",
        "company": "腾讯",
        "location": "深圳",
        "url": REAL_JOB_URLS[2],
        "description": "这是一个产品经理职位",
        "salary": "35k-50k"
    }
]


async def test_scrape_single_job_detail():
    """测试爬取单个职位详情"""
    print("开始测试爬取单个职位详情...")
    
    # 创建AgentService实例
    agent_service = AgentService()
    
    # 测试第一个职位
    job = TEST_JOB_DATA[0]
    print(f"爬取职位: {job['title']} - {job['company']}")
    print(f"URL: {job['url']}")
    
    # 执行爬取
    result = await agent_service._scrape_single_job_detail(job)
    
    # 打印结果
    print("\n爬取结果:")
    for key, value in result.items():
        if key not in job or job[key] != value:
            print(f"  {key}: {value}")
    
    # 验证结果
    assert result is not None
    assert result["url"] == job["url"]
    assert "company_description" in result or "description" in result
    
    print("单个职位爬取测试完成!\n")
    return result


async def test_scrape_job_details():
    """测试爬取多个职位详情"""
    print("开始测试爬取多个职位详情...")
    
    # 创建AgentService实例
    agent_service = AgentService()
    
    # 执行爬取
    results = await agent_service._scrape_job_details(TEST_JOB_DATA[:2])  # 只测试前两个职位
    
    # 打印结果
    print(f"\n成功爬取 {len(results)} 个职位")
    for i, result in enumerate(results):
        print(f"\n职位 {i+1}: {result.get('title')} - {result.get('company')}")
        for key in ["company_description", "experience_level", "education_level", 
                   "company_size", "funding_stage"]:
            if key in result:
                print(f"  {key}: {result[key]}")
    
    # 验证结果
    assert len(results) > 0
    
    print("多个职位爬取测试完成!")
    return results


async def run_tests():
    """运行所有测试"""
    # 测试单个职位爬取
    await test_scrape_single_job_detail()
    
    # 测试多个职位爬取
    await test_scrape_job_details()


def save_results_to_file(results, filename="job_scrape_results.json"):
    """将爬取结果保存到文件"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"结果已保存到 {filename}")


if __name__ == "__main__":
    # 运行测试
    single_result = asyncio.run(test_scrape_single_job_detail())
    
    # 是否运行多职位测试
    run_multi = input("\n是否运行多职位爬取测试? (y/n): ").strip().lower()
    if run_multi == 'y':
        multi_results = asyncio.run(test_scrape_job_details())
        
        # 保存结果
        save_results_to_file(multi_results, "multi_job_scrape_results.json")
    
    # 保存单个职位结果
    save_results_to_file([single_result], "single_job_scrape_result.json")
    
    print("\n所有测试完成!")
