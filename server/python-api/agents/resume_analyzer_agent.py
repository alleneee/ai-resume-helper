"""
简历分析Agent - 负责分析用户简历并识别核心竞争力
"""
import json
import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI
from openai_agents.agent import Agent

from .config import (
    OPENAI_API_KEY, OPENAI_MODEL, DEFAULT_AGENT_TEMPERATURE,
    ResumeAnalysisResult
)

logger = logging.getLogger(__name__)

class ResumeAnalyzerAgent(Agent):
    """
    简历分析Agent - 负责解析和分析用户简历，识别核心技能和竞争优势，
    并提供针对性的改进建议和关键词优化
    """

    def __init__(self, api_key: str = None, model: str = None):
        """初始化简历分析Agent"""
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or OPENAI_MODEL
        
        super().__init__(
            name="简历分析专家",
            handoff_description="专门分析简历内容并提供改进建议的专家",
            instructions=self._get_agent_instructions(),
            model=self.model,
        )
    
    def _get_agent_instructions(self) -> str:
        """获取Agent指令"""
        return """你是一个专业的简历分析专家，负责全面分析求职者的简历，提供专业化的评估和建议。

你的主要职责包括：
1. 识别简历中的核心技能和专业能力
2. 总结求职者的工作经验，强调关键成就
3. 识别简历的优势和特点，包括专业技能、经验和个人特质
4. 指出简历中需要改进的地方，包括格式、内容组织和表达方式
5. 建议适合加入简历的关键词，以提高在ATS系统中的竞争力

你需要从专业角度评估简历，提供详细具体的分析结果，包括：
- 核心技能列表：按相关性排序的专业技能
- 经验总结：简明扼要的工作经验概述
- 优势分析：详细说明简历的竞争优势
- 改进建议：具体可操作的改进点
- 关键词建议：针对求职方向的适合关键词
"""

    async def analyze_resume(self, resume_text: str, job_description: Optional[str] = None) -> ResumeAnalysisResult:
        """
        分析用户简历
        
        Args:
            resume_text: 简历文本内容
            job_description: 可选的目标职位描述，用于提供有针对性的分析
            
        Returns:
            ResumeAnalysisResult: 简历分析结果
        """
        try:
            # 准备分析提示
            prompt = self._prepare_analysis_prompt(resume_text, job_description)
            
            # 调用OpenAI API进行分析
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": """你是一个专业的简历分析专家。请分析提供的简历，并返回JSON格式的分析结果，包含以下字段：
                    - core_skills: 核心技能列表(字符串数组)
                    - experience_summary: 工作经验总结(字符串)
                    - strengths: 优势分析(对象数组，每个对象包含title和description字段)
                    - improvements: 改进建议(对象数组，每个对象包含area和suggestion字段)
                    - keywords: 建议添加的关键词(字符串数组)
                    - score: 简历评分(对象，包含overall分数和各个维度的分数)
                    
                    确保返回的是有效的JSON格式，不要包含任何其他文本。
                    """},
                    {"role": "user", "content": prompt}
                ],
                temperature=DEFAULT_AGENT_TEMPERATURE,
                response_format={"type": "json_object"}
            )
            
            # 解析JSON响应
            result_json = response.choices[0].message.content
            result_data = json.loads(result_json)
            
            # 构建结构化结果
            return ResumeAnalysisResult(
                core_skills=result_data.get("core_skills", []),
                experience_summary=result_data.get("experience_summary", ""),
                strengths=result_data.get("strengths", []),
                improvements=result_data.get("improvements", []),
                keywords=result_data.get("keywords", []),
                score=result_data.get("score", {})
            )
                
        except Exception as e:
            logger.error(f"简历分析失败: {str(e)}")
            # 发生错误时返回基本结果
            return ResumeAnalysisResult(
                core_skills=["解析出错"],
                experience_summary="无法解析简历内容",
                strengths=[{"title": "错误", "description": f"分析过程中出错: {str(e)}"}],
                improvements=[{"area": "格式", "suggestion": "请提供有效的简历文档"}],
                keywords=[]
            )
    
    def _prepare_analysis_prompt(self, resume_text: str, job_description: Optional[str] = None) -> str:
        """准备分析提示"""
        prompt = f"请分析以下简历内容，并提供详细的分析结果：\n\n{resume_text}\n\n"
        
        if job_description:
            prompt += f"目标职位描述：\n{job_description}\n\n"
            prompt += "请根据以上简历内容和目标职位描述，提供针对性的分析，特别关注简历与职位要求的匹配度。"
        else:
            prompt += "请根据以上简历内容进行全面分析，提供对简历的专业评估和建议。"
            
        return prompt 