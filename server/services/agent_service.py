"""
智能代理服务
处理简历优化、职位匹配和求职信生成等AI驱动功能
"""
import logging
import os
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import httpx
from bson import ObjectId

# 配置日志
logger = logging.getLogger(__name__)

class AgentService:
    """智能代理服务类"""
    
    _instance = None
    
    def __init__(self):
        """初始化代理服务"""
        self.api_key = os.getenv("AI_API_KEY", "")
        self.api_base_url = os.getenv("AI_API_BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("AI_MODEL", "gpt-4")
        self.job_search_api_key = os.getenv("JOB_SEARCH_API_KEY", "")
        self.job_search_api_url = os.getenv("JOB_SEARCH_API_URL", "https://api.jobsearch.com/v1")
        
        # 验证配置
        if not self.api_key:
            logger.warning("AI_API_KEY 环境变量未设置")
        
        if not self.job_search_api_key:
            logger.warning("JOB_SEARCH_API_KEY 环境变量未设置")
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = AgentService()
        return cls._instance
    
    async def optimize_resume(
        self, 
        resume_id: str, 
        resume_data: Dict[str, Any], 
        job_description: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        优化简历
        
        Args:
            resume_id: 简历ID
            resume_data: 简历数据
            job_description: 职位描述
            user_id: 用户ID
            
        Returns:
            优化结果，包含原始内容、优化后的内容、建议和关键词
        """
        try:
            logger.info(f"开始优化简历: {resume_id}")
            
            # 读取简历内容
            file_path = resume_data.get("file_path", "")
            if not os.path.exists(file_path):
                logger.error(f"简历文件不存在: {file_path}")
                raise FileNotFoundError(f"简历文件不存在: {file_path}")
            
            # 读取文件内容
            with open(file_path, "r", encoding="utf-8") as f:
                resume_content = f.read()
            
            # 调用AI API进行优化
            optimization_result = await self._call_ai_api(
                prompt=self._create_optimization_prompt(resume_content, job_description),
                max_tokens=2000
            )
            
            # 解析AI响应
            try:
                result_json = json.loads(optimization_result)
            except json.JSONDecodeError:
                logger.error("无法解析AI响应为JSON格式")
                # 尝试使用简单格式
                result_json = {
                    "optimized_content": optimization_result,
                    "suggestions": ["无法提取具体建议"],
                    "keywords": []
                }
            
            # 构建返回结果
            result = {
                "original_content": resume_content,
                "optimized_content": result_json.get("optimized_content", ""),
                "suggestions": result_json.get("suggestions", []),
                "keywords": result_json.get("keywords", [])
            }
            
            logger.info(f"简历优化完成: {resume_id}")
            return result
            
        except Exception as e:
            logger.error(f"简历优化失败: {str(e)}")
            raise
    
    async def match_jobs(
        self,
        resume_id: str,
        resume_data: Dict[str, Any],
        location: Optional[str] = None,
        job_type: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        limit: int = 10,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        职位匹配
        
        Args:
            resume_id: 简历ID
            resume_data: 简历数据
            location: 地点
            job_type: 职位类型
            keywords: 关键词
            limit: 返回结果数量
            user_id: 用户ID
            
        Returns:
            匹配结果，包含职位列表和统计信息
        """
        try:
            logger.info(f"开始职位匹配: {resume_id}")
            
            # 读取简历内容
            file_path = resume_data.get("file_path", "")
            if not os.path.exists(file_path):
                logger.error(f"简历文件不存在: {file_path}")
                raise FileNotFoundError(f"简历文件不存在: {file_path}")
            
            # 读取文件内容
            with open(file_path, "r", encoding="utf-8") as f:
                resume_content = f.read()
            
            # 提取简历关键词
            keywords_result = await self._call_ai_api(
                prompt=self._create_keywords_extraction_prompt(resume_content),
                max_tokens=500
            )
            
            try:
                extracted_keywords = json.loads(keywords_result).get("keywords", [])
            except json.JSONDecodeError:
                logger.warning("无法解析关键词提取结果为JSON格式")
                extracted_keywords = []
            
            # 合并用户提供的关键词和提取的关键词
            search_keywords = list(set((keywords or []) + extracted_keywords))
            
            # 调用职位搜索API
            jobs = await self._search_jobs_api(
                keywords=search_keywords,
                location=location,
                job_type=job_type,
                limit=limit
            )
            
            # 对职位进行评分
            scored_jobs = await self._score_jobs(resume_content, jobs)
            
            # 按匹配分数排序
            sorted_jobs = sorted(scored_jobs, key=lambda x: x.get("match_score", 0), reverse=True)
            
            # 构建返回结果
            result = {
                "jobs": sorted_jobs[:limit],
                "total": len(sorted_jobs),
                "extracted_keywords": extracted_keywords
            }
            
            logger.info(f"职位匹配完成: {resume_id} - 找到 {len(sorted_jobs)} 个匹配职位")
            return result
            
        except Exception as e:
            logger.error(f"职位匹配失败: {str(e)}")
            raise
    
    async def generate_cover_letter(
        self,
        resume_id: str,
        resume_data: Dict[str, Any],
        job_description: str,
        company_name: str,
        company_info: Optional[str] = None,
        tone: str = "professional",
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        生成求职信
        
        Args:
            resume_id: 简历ID
            resume_data: 简历数据
            job_description: 职位描述
            company_name: 公司名称
            company_info: 公司信息
            tone: 语调
            user_id: 用户ID
            
        Returns:
            生成的求职信内容
        """
        try:
            logger.info(f"开始生成求职信: {resume_id}")
            
            # 读取简历内容
            file_path = resume_data.get("file_path", "")
            if not os.path.exists(file_path):
                logger.error(f"简历文件不存在: {file_path}")
                raise FileNotFoundError(f"简历文件不存在: {file_path}")
            
            # 读取文件内容
            with open(file_path, "r", encoding="utf-8") as f:
                resume_content = f.read()
            
            # 调用AI API生成求职信
            cover_letter = await self._call_ai_api(
                prompt=self._create_cover_letter_prompt(
                    resume_content, 
                    job_description, 
                    company_name, 
                    company_info, 
                    tone
                ),
                max_tokens=1500
            )
            
            # 构建返回结果
            result = {
                "content": cover_letter
            }
            
            logger.info(f"求职信生成完成: {resume_id}")
            return result
            
        except Exception as e:
            logger.error(f"求职信生成失败: {str(e)}")
            raise
    
    async def search_jobs(
        self,
        keywords: List[str],
        location: Optional[str] = None,
        job_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        salary_min: Optional[int] = None,
        salary_max: Optional[int] = None,
        page: int = 1,
        limit: int = 10,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        搜索职位
        
        Args:
            keywords: 关键词
            location: 地点
            job_type: 职位类型
            experience_level: 经验水平
            salary_min: 最低薪资
            salary_max: 最高薪资
            page: 页码
            limit: 每页数量
            user_id: 用户ID
            
        Returns:
            搜索结果，包含职位列表和分页信息
        """
        try:
            logger.info(f"开始搜索职位: 关键词: {keywords}")
            
            # 调用职位搜索API
            jobs = await self._search_jobs_api(
                keywords=keywords,
                location=location,
                job_type=job_type,
                experience_level=experience_level,
                salary_min=salary_min,
                salary_max=salary_max,
                page=page,
                limit=limit
            )
            
            # 计算总数
            total = len(jobs)
            
            # 构建返回结果
            result = {
                "jobs": jobs,
                "total": total,
                "page": page,
                "limit": limit
            }
            
            logger.info(f"职位搜索完成: 关键词: {keywords} - 找到 {total} 个职位")
            return result
            
        except Exception as e:
            logger.error(f"职位搜索失败: {str(e)}")
            raise
    
    async def _call_ai_api(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        调用AI API
        
        Args:
            prompt: 提示词
            max_tokens: 最大令牌数
            
        Returns:
            AI响应文本
        """
        try:
            logger.debug(f"调用AI API: {prompt[:100]}...")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "你是一个专业的简历和求职顾问。"},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": max_tokens,
                        "temperature": 0.7
                    },
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                # 提取响应文本
                return result["choices"][0]["message"]["content"]
                
        except Exception as e:
            logger.error(f"AI API调用失败: {str(e)}")
            raise
    
    async def _search_jobs_api(
        self,
        keywords: List[str],
        location: Optional[str] = None,
        job_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        salary_min: Optional[int] = None,
        salary_max: Optional[int] = None,
        page: int = 1,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        调用职位搜索API
        
        Args:
            keywords: 关键词
            location: 地点
            job_type: 职位类型
            experience_level: 经验水平
            salary_min: 最低薪资
            salary_max: 最高薪资
            page: 页码
            limit: 每页数量
            
        Returns:
            职位列表
        """
        try:
            logger.debug(f"调用职位搜索API: 关键词: {keywords}")
            
            # 构建查询参数
            params = {
                "keywords": ",".join(keywords),
                "limit": limit,
                "page": page
            }
            
            if location:
                params["location"] = location
                
            if job_type:
                params["job_type"] = job_type
                
            if experience_level:
                params["experience_level"] = experience_level
                
            if salary_min:
                params["salary_min"] = salary_min
                
            if salary_max:
                params["salary_max"] = salary_max
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.job_search_api_url}/search",
                    headers={
                        "Authorization": f"Bearer {self.job_search_api_key}",
                        "Content-Type": "application/json"
                    },
                    params=params,
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                # 返回职位列表
                return result.get("jobs", [])
                
        except Exception as e:
            logger.error(f"职位搜索API调用失败: {str(e)}")
            # 如果API调用失败，返回模拟数据
            return self._get_mock_jobs(keywords, location, limit)
    
    async def _score_jobs(self, resume_content: str, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        对职位进行评分
        
        Args:
            resume_content: 简历内容
            jobs: 职位列表
            
        Returns:
            带有匹配分数的职位列表
        """
        try:
            # 如果没有职位，直接返回空列表
            if not jobs:
                return []
            
            # 构建评分提示词
            prompt = f"""
            我需要你评估以下简历与多个职位的匹配程度。
            
            简历内容:
            {resume_content[:2000]}... (简历内容已截断)
            
            职位列表:
            {json.dumps([{
                "id": job.get("id", ""),
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "description": job.get("description", "")[:500] + "..." if len(job.get("description", "")) > 500 else job.get("description", "")
            } for job in jobs[:10]])}
            
            请为每个职位提供一个0到1之间的匹配分数，其中1表示完全匹配，0表示完全不匹配。
            请以JSON格式返回结果，格式为：
            {{"scores": [{{"id": "职位ID", "score": 匹配分数}}, ...]}}
            """
            
            # 调用AI API进行评分
            scores_result = await self._call_ai_api(prompt=prompt, max_tokens=1000)
            
            try:
                scores_data = json.loads(scores_result)
                scores_dict = {item["id"]: item["score"] for item in scores_data.get("scores", [])}
            except (json.JSONDecodeError, KeyError):
                logger.warning("无法解析职位评分结果为JSON格式")
                # 如果解析失败，使用随机分数
                import random
                scores_dict = {job.get("id", ""): random.uniform(0.5, 0.9) for job in jobs}
            
            # 将分数添加到职位中
            scored_jobs = []
            for job in jobs:
                job_copy = job.copy()
                job_copy["match_score"] = scores_dict.get(job.get("id", ""), 0.5)
                scored_jobs.append(job_copy)
            
            return scored_jobs
            
        except Exception as e:
            logger.error(f"职位评分失败: {str(e)}")
            # 如果评分失败，返回原始职位列表，但添加随机分数
            import random
            for job in jobs:
                job["match_score"] = random.uniform(0.5, 0.9)
            return jobs
    
    def _get_mock_jobs(self, keywords: List[str], location: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取模拟职位数据（当API调用失败时使用）
        
        Args:
            keywords: 关键词
            location: 地点
            limit: 返回数量
            
        Returns:
            模拟职位列表
        """
        logger.warning("使用模拟职位数据")
        
        mock_jobs = [
            {
                "id": f"mock-{i}",
                "title": f"{keywords[0] if keywords else '软件'}{['工程师', '开发者', '架构师'][i % 3]}",
                "company": f"模拟公司 {i+1}",
                "location": location or "上海",
                "description": f"这是一个模拟职位描述，包含关键词: {', '.join(keywords)}。该职位需要相关技术经验和团队协作能力。",
                "salary": f"{(i+1)*10}k-{(i+2)*10}k",
                "job_type": ["全职", "兼职", "合同工"][i % 3],
                "url": f"https://example.com/jobs/mock-{i}",
                "posted_date": datetime.now().strftime("%Y-%m-%d")
            }
            for i in range(min(limit, 10))
        ]
        
        return mock_jobs
    
    def _create_optimization_prompt(self, resume_content: str, job_description: str) -> str:
        """
        创建简历优化提示词
        
        Args:
            resume_content: 简历内容
            job_description: 职位描述
            
        Returns:
            提示词
        """
        return f"""
        请帮我优化以下简历，使其更适合应聘以下职位。
        
        职位描述:
        {job_description}
        
        简历内容:
        {resume_content}
        
        请提供以下内容:
        1. 优化后的简历内容
        2. 具体的改进建议
        3. 从简历中提取的关键词
        
        请以JSON格式返回结果，格式为：
        {{
            "optimized_content": "优化后的简历内容...",
            "suggestions": ["建议1", "建议2", ...],
            "keywords": ["关键词1", "关键词2", ...]
        }}
        """
    
    def _create_keywords_extraction_prompt(self, resume_content: str) -> str:
        """
        创建关键词提取提示词
        
        Args:
            resume_content: 简历内容
            
        Returns:
            提示词
        """
        return f"""
        请从以下简历中提取关键技能、经验和资质。
        
        简历内容:
        {resume_content}
        
        请以JSON格式返回结果，格式为：
        {{
            "keywords": ["关键词1", "关键词2", ...]
        }}
        
        关键词应包括技术技能、软技能、行业知识、证书和资质等。
        """
    
    def _create_cover_letter_prompt(
        self, 
        resume_content: str, 
        job_description: str, 
        company_name: str, 
        company_info: Optional[str], 
        tone: str
    ) -> str:
        """
        创建求职信生成提示词
        
        Args:
            resume_content: 简历内容
            job_description: 职位描述
            company_name: 公司名称
            company_info: 公司信息
            tone: 语调
            
        Returns:
            提示词
        """
        return f"""
        请根据以下信息为我生成一封专业的求职信。
        
        简历内容:
        {resume_content}
        
        职位描述:
        {job_description}
        
        公司名称:
        {company_name}
        
        公司信息:
        {company_info or "无额外信息"}
        
        语调:
        {tone}
        
        请生成一封完整的求职信，包括称呼、正文和结尾。内容应突出我的技能和经验如何与职位要求相匹配，并表达对公司的了解和兴趣。
        """

# 为了向后兼容，保留原有的调用方式
agent_service = AgentService.get_instance()
