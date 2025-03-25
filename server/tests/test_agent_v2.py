"""
Agent V2 API测试模块
测试基于OpenAI Agents SDK的API路由
"""
import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from bson import ObjectId

from main import app
from models.agent import (
    ResumeOptimizationRequest, 
    JobMatchRequest, 
    CoverLetterRequest,
    JobSearchRequest
)
from utils.openai_client import get_openai_agents_client

# 创建测试客户端
client = TestClient(app)

# 测试数据
TEST_USER = {
    "_id": "64f89521a95d32a74d88c32b",
    "email": "test@example.com",
    "name": "测试用户",
    "permissions": ["resume:read", "resume:write"]
}

TEST_RESUME = {
    "_id": ObjectId("64f89521a95d32a74d88c32c"),
    "user_id": ObjectId("64f89521a95d32a74d88c32b"),
    "title": "测试简历",
    "content": "# 测试用户简历\n\n## 教育背景\n中国科学技术大学 计算机科学 2018-2022\n\n## 工作经验\n某科技公司 软件工程师 2022-至今\n\n## 技能\nPython, FastAPI, React"
}

TEST_JOB_DESCRIPTION = "招聘Python全栈开发工程师，需要有FastAPI和React经验..."

# 模拟鉴权中间件
@pytest.fixture
def mock_auth_middleware():
    with patch("middleware.auth.get_current_user_with_permissions") as mock:
        mock.return_value = lambda: TEST_USER
        yield mock

# 模拟数据库
@pytest.fixture
def mock_db():
    with patch("models.database.get_mongo_db") as mock:
        db_mock = AsyncMock()
        
        # 模拟resumes集合
        resumes_mock = AsyncMock()
        resumes_mock.find_one.return_value = TEST_RESUME
        db_mock.resumes = resumes_mock
        
        # 模拟resume_optimizations集合
        optimizations_mock = AsyncMock()
        optimizations_mock.insert_one.return_value = MagicMock(inserted_id=ObjectId())
        db_mock.resume_optimizations = optimizations_mock
        
        # 模拟cover_letters集合
        cover_letters_mock = AsyncMock()
        cover_letters_mock.insert_one.return_value = MagicMock(inserted_id=ObjectId())
        db_mock.cover_letters = cover_letters_mock
        
        # 模拟job_search_history集合
        job_search_history_mock = AsyncMock()
        job_search_history_mock.insert_one.return_value = MagicMock(inserted_id=ObjectId())
        db_mock.job_search_history = job_search_history_mock
        
        yield db_mock

# 模拟OpenAI Agents
@pytest.fixture
def mock_openai_agents():
    with patch("services.agents.resume_agent.optimize_resume") as mock_optimize, \
         patch("services.agents.resume_agent.analyze_resume") as mock_analyze, \
         patch("services.agents.job_agent.search_jobs") as mock_search, \
         patch("services.agents.job_agent.match_job") as mock_match, \
         patch("services.agents.cover_letter_agent.generate_cover_letter") as mock_generate:
        
        # 简历优化返回值
        mock_optimize.return_value = {
            "success": True,
            "message": "简历优化成功",
            "data": {
                "optimized_content": "# 优化后的简历\n\n## 教育背景\n...",
                "suggestions": ["建议1", "建议2"],
                "keywords": ["python", "fastapi", "react"],
                "match_score": 85
            }
        }
        
        # 简历分析返回值
        mock_analyze.return_value = {
            "success": True,
            "message": "简历分析成功",
            "data": {
                "strengths": ["优势1", "优势2"],
                "weaknesses": ["劣势1", "劣势2"],
                "skills": ["python", "fastapi", "react"],
                "experience_years": 2
            }
        }
        
        # 职位搜索返回值
        mock_search.return_value = {
            "success": True,
            "message": "职位搜索成功",
            "data": {
                "jobs": [
                    {
                        "id": "job1",
                        "title": "Python开发工程师",
                        "company": "公司A",
                        "location": "北京",
                        "description": "职位描述...",
                        "salary": "20k-30k",
                        "url": "https://example.com/job1"
                    }
                ],
                "total": 1,
                "page": 1,
                "limit": 10
            }
        }
        
        # 职位匹配返回值
        mock_match.return_value = {
            "success": True,
            "message": "职位匹配成功",
            "data": {
                "match_score": 85,
                "matching_skills": ["python", "fastapi"],
                "missing_skills": ["django"],
                "recommendations": ["建议1", "建议2"]
            }
        }
        
        # 求职信生成返回值
        mock_generate.return_value = {
            "success": True,
            "message": "求职信生成成功",
            "data": {
                "content": "尊敬的招聘经理：\n\n我对贵公司的Python全栈开发工程师职位非常感兴趣...",
                "suggestions": ["建议保持专业的语气", "突出你的FastAPI和React经验"]
            }
        }
        
        yield {
            "optimize": mock_optimize,
            "analyze": mock_analyze,
            "search": mock_search,
            "match": mock_match,
            "generate": mock_generate
        }

@pytest.mark.asyncio
async def test_optimize_resume(mock_auth_middleware, mock_db, mock_openai_agents):
    """测试简历优化API"""
    # 请求数据
    data = {
        "resume_id": str(TEST_RESUME["_id"]),
        "job_description": TEST_JOB_DESCRIPTION,
        "focus_areas": ["技能匹配", "经验描述", "教育背景"],
        "target_job_title": "Python开发工程师"
    }
    
    # 发送请求
    response = client.post(
        "/api/agent/v2/optimize-resume",
        json=data,
        headers={"Authorization": "Bearer test_token"}
    )
    
    # 验证响应
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["message"] == "简历优化成功"
    assert "optimized_content" in result["data"]
    assert "suggestions" in result["data"]
    assert "keywords" in result["data"]
    
    # 验证函数调用
    mock_openai_agents["optimize"].assert_called_once()
    mock_db.resume_optimizations.insert_one.assert_called_once()

@pytest.mark.asyncio
async def test_analyze_resume(mock_auth_middleware, mock_db, mock_openai_agents):
    """测试简历分析API"""
    # 请求数据
    resume_id = str(TEST_RESUME["_id"])
    
    # 发送请求
    response = client.post(
        "/api/agent/v2/analyze-resume",
        json={"resume_id": resume_id},
        headers={"Authorization": "Bearer test_token"}
    )
    
    # 验证响应
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["message"] == "简历分析成功"
    assert "strengths" in result["data"]
    assert "weaknesses" in result["data"]
    assert "skills" in result["data"]
    
    # 验证函数调用
    mock_openai_agents["analyze"].assert_called_once()

@pytest.mark.asyncio
async def test_search_jobs(mock_auth_middleware, mock_db, mock_openai_agents):
    """测试职位搜索API"""
    # 请求数据
    data = {
        "keywords": ["python", "fastapi"],
        "location": "北京",
        "job_type": "FULL_TIME",
        "limit": 10
    }
    
    # 发送请求
    response = client.post(
        "/api/agent/v2/search-jobs",
        json=data,
        headers={"Authorization": "Bearer test_token"}
    )
    
    # 验证响应
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["message"] == "职位搜索成功"
    assert "jobs" in result["data"]
    assert len(result["data"]["jobs"]) > 0
    
    # 验证函数调用
    mock_openai_agents["search"].assert_called_once()
    mock_db.job_search_history.insert_one.assert_called_once()

@pytest.mark.asyncio
async def test_match_jobs(mock_auth_middleware, mock_db, mock_openai_agents):
    """测试职位匹配API"""
    # 请求数据
    data = {
        "resume_id": str(TEST_RESUME["_id"]),
        "keywords": ["python", "fastapi"],
        "location": "北京",
        "job_type": "FULL_TIME",
        "limit": 10
    }
    
    # 发送请求
    response = client.post(
        "/api/agent/v2/match-jobs",
        json=data,
        headers={"Authorization": "Bearer test_token"}
    )
    
    # 验证响应
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["message"] == "职位匹配成功"
    assert "jobs" in result["data"]
    
    # 验证函数调用
    mock_openai_agents["search"].assert_called_once()
    mock_openai_agents["match"].assert_called()

@pytest.mark.asyncio
async def test_generate_cover_letter(mock_auth_middleware, mock_db, mock_openai_agents):
    """测试求职信生成API"""
    # 请求数据
    data = {
        "resume_id": str(TEST_RESUME["_id"]),
        "job_description": TEST_JOB_DESCRIPTION,
        "company_name": "测试公司",
        "company_info": "一家领先的科技公司...",
        "tone": "PROFESSIONAL"
    }
    
    # 发送请求
    response = client.post(
        "/api/agent/v2/generate-cover-letter",
        json=data,
        headers={"Authorization": "Bearer test_token"}
    )
    
    # 验证响应
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["message"] == "求职信生成成功"
    assert "content" in result["data"]
    
    # 验证函数调用
    mock_openai_agents["generate"].assert_called_once()
    mock_db.cover_letters.insert_one.assert_called_once()

@pytest.mark.asyncio
async def test_unauthorized_access(mock_db):
    """测试未授权访问"""
    # 发送请求（没有认证头）
    response = client.post(
        "/api/agent/v2/optimize-resume",
        json={"resume_id": str(TEST_RESUME["_id"]), "job_description": TEST_JOB_DESCRIPTION}
    )
    
    # 验证响应
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_invalid_resume_id(mock_auth_middleware, mock_db):
    """测试无效的简历ID"""
    # 模拟数据库查询返回None
    mock_db.resumes.find_one.return_value = None
    
    # 请求数据
    data = {
        "resume_id": "invalid_id",
        "job_description": TEST_JOB_DESCRIPTION
    }
    
    # 发送请求
    response = client.post(
        "/api/agent/v2/optimize-resume",
        json=data,
        headers={"Authorization": "Bearer test_token"}
    )
    
    # 验证响应
    assert response.status_code == 404
    result = response.json()
    assert result["success"] is False
    assert "不存在" in result["message"]
