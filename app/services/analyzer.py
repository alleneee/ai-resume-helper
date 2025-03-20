from typing import List, Dict, Any, Optional
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import json
import re

from app.models.resume import ResumeData
from app.models.analysis import (
    ResumeAnalysis, QualityScores, KeywordAnalysis, 
    ContentSuggestion, SuggestionType, ATSCompatibility,
    JobSpecificMatch
)
from app.config import get_settings


class ResumeAnalysisService:
    """简历分析服务"""
    
    def __init__(self):
        settings = get_settings()
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.OPENAI_MODEL,
            temperature=0.2
        )
        
        # 定义质量评分的提示模板
        self.quality_prompt = PromptTemplate(
            input_variables=["resume_text"],
            template="""
            你是一位专业的简历分析专家，负责评估简历的质量。
            请对以下简历文本进行全面评估，并提供详细的分数和评价。
            
            评分标准 (0-100):
            1. 完整性 (Completeness): 简历是否包含所有必要信息
            2. 影响力 (Impact): 成就和贡献的表述是否有影响力
            3. 相关性 (Relevance): 内容与目标职位的相关度
            4. 清晰度 (Clarity): 信息组织和表述的清晰程度
            5. ATS兼容性 (ATS Compatibility): 是否能顺利通过申请跟踪系统
            
            简历文本:
            ```
            {resume_text}
            ```
            
            以JSON格式返回你的评分结果:
            ```json
            {{
                "scores": {{
                    "completeness": XX,
                    "impact": XX,
                    "relevance": XX,
                    "clarity": XX,
                    "ats_compatibility": XX
                }},
                "overall_score": XX,
                "comments": {{
                    "completeness": "...",
                    "impact": "...",
                    "relevance": "...",
                    "clarity": "...",
                    "ats_compatibility": "..."
                }}
            }}
            ```
            """
        )
        
        # 定义内容建议的提示模板
        self.suggestion_prompt = PromptTemplate(
            input_variables=["resume_text"],
            template="""
            你是一位专业的简历优化专家，负责提供改进建议。
            请分析以下简历文本，并提供具体的优化建议，包括内容改进、格式调整、成就量化等方面。
            
            简历文本:
            ```
            {resume_text}
            ```
            
            请提供至少5条具体的改进建议，以JSON格式返回:
            ```json
            {{
                "suggestions": [
                    {{
                        "type": "content|format|grammar|keyword|quantification|redundancy",
                        "section": "experience|education|skills|summary|...",
                        "original": "原文内容",
                        "suggested": "建议修改内容",
                        "reason": "建议理由"
                    }}
                ]
            }}
            ```
            
            建议应该具体且可操作，避免泛泛而谈。
            """
        )
        
        # 定义关键词分析的提示模板
        self.keyword_prompt = PromptTemplate(
            input_variables=["resume_text"],
            template="""
            你是一位专业的简历关键词分析专家，负责分析简历中的关键词。
            请分析以下简历文本，识别关键词，并提供改进建议。
            
            简历文本:
            ```
            {resume_text}
            ```
            
            请以JSON格式返回你的分析结果:
            ```json
            {{
                "detected_keywords": ["关键词1", "关键词2", "..."],
                "missing_keywords": ["建议添加的关键词1", "..."],
                "keyword_density": XX.XX,
                "industry_keywords": ["行业关键词1", "..."]
            }}
            ```
            """
        )
        
        # 定义ATS兼容性分析的提示模板
        self.ats_prompt = PromptTemplate(
            input_variables=["resume_text"],
            template="""
            你是一位ATS(申请跟踪系统)兼容性分析专家，负责评估简历是否符合ATS要求。
            请分析以下简历文本，评估其ATS兼容性，并提供改进建议。
            
            简历文本:
            ```
            {resume_text}
            ```
            
            请以JSON格式返回你的分析结果:
            ```json
            {{
                "ats_score": XX,
                "issues": ["问题1", "问题2", "..."],
                "formatting_issues": ["格式问题1", "..."],
                "content_issues": ["内容问题1", "..."],
                "recommendations": ["建议1", "建议2", "..."]
            }}
            ```
            """
        )
        
        # 创建LLM链
        self.quality_chain = LLMChain(llm=self.llm, prompt=self.quality_prompt)
        self.suggestion_chain = LLMChain(llm=self.llm, prompt=self.suggestion_prompt)
        self.keyword_chain = LLMChain(llm=self.llm, prompt=self.keyword_prompt)
        self.ats_chain = LLMChain(llm=self.llm, prompt=self.ats_prompt)
    
    async def analyze_resume(self, resume_data: ResumeData, resume_id: str) -> ResumeAnalysis:
        """
        分析简历数据
        
        Args:
            resume_data: 简历数据
            resume_id: 简历ID
            
        Returns:
            ResumeAnalysis: 分析结果
        """
        # 提取原始文本
        raw_text = resume_data.raw_text
        
        # 并行执行各项分析
        quality_task = self.quality_chain.arun(resume_text=raw_text)
        suggestion_task = self.suggestion_chain.arun(resume_text=raw_text)
        keyword_task = self.keyword_chain.arun(resume_text=raw_text)
        ats_task = self.ats_chain.arun(resume_text=raw_text)
        
        # 等待所有分析完成
        quality_result = await quality_task
        suggestion_result = await suggestion_task
        keyword_result = await keyword_task
        ats_result = await ats_task
        
        # 解析结果
        quality_data = self._parse_json_result(quality_result)
        suggestion_data = self._parse_json_result(suggestion_result)
        keyword_data = self._parse_json_result(keyword_result)
        ats_data = self._parse_json_result(ats_result)
        
        # 构建分析结果
        quality_scores = QualityScores(
            completeness=quality_data.get("scores", {}).get("completeness", 50),
            impact=quality_data.get("scores", {}).get("impact", 50),
            relevance=quality_data.get("scores", {}).get("relevance", 50),
            clarity=quality_data.get("scores", {}).get("clarity", 50),
            ats_compatibility=quality_data.get("scores", {}).get("ats_compatibility", 50)
        )
        
        content_suggestions = []
        for suggestion in suggestion_data.get("suggestions", []):
            try:
                content_suggestions.append(ContentSuggestion(
                    type=SuggestionType(suggestion.get("type", "content")),
                    section=suggestion.get("section", "general"),
                    original=suggestion.get("original"),
                    suggested=suggestion.get("suggested", ""),
                    reason=suggestion.get("reason", "")
                ))
            except Exception as e:
                print(f"创建建议时出错: {str(e)}")
        
        keyword_analysis = KeywordAnalysis(
            detected=keyword_data.get("detected_keywords", []),
            missing=keyword_data.get("missing_keywords", []),
            density=float(keyword_data.get("keyword_density", 0.05))
        )
        
        ats_compatibility = ATSCompatibility(
            score=ats_data.get("ats_score", 50),
            issues=ats_data.get("issues", []),
            formatting_issues=ats_data.get("formatting_issues", []),
            content_issues=ats_data.get("content_issues", []),
            recommendations=ats_data.get("recommendations", [])
        )
        
        # 计算总体评分
        overall_score = self._calculate_overall_score(quality_scores, ats_compatibility.score)
        
        return ResumeAnalysis(
            resume_id=resume_id,
            overall_score=overall_score,
            quality_scores=quality_scores,
            content_suggestions=content_suggestions,
            keyword_analysis=keyword_analysis,
            ats_compatibility=ats_compatibility
        )
    
    async def analyze_job_match(
        self, 
        resume_data: ResumeData, 
        job_description: str
    ) -> JobSpecificMatch:
        """
        分析简历与职位的匹配度
        
        Args:
            resume_data: 简历数据
            job_description: 职位描述
            
        Returns:
            JobSpecificMatch: 匹配分析结果
        """
        # 实现待补充...
        # 这里应该实现职位匹配分析的逻辑
        pass
    
    def _parse_json_result(self, result: str) -> Dict[str, Any]:
        """
        解析LLM返回的JSON结果
        
        Args:
            result: LLM返回的字符串
            
        Returns:
            Dict: 解析后的数据字典
        """
        try:
            # 尝试从文本中提取JSON部分
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', result)
            if json_match:
                return json.loads(json_match.group(1))
            
            # 如果没有明确的JSON标记，尝试直接解析整个文本
            return json.loads(result)
        except Exception as e:
            print(f"JSON解析错误: {str(e)}")
            return {}
    
    def _calculate_overall_score(self, quality_scores: QualityScores, ats_score: int) -> int:
        """
        计算总体评分
        
        Args:
            quality_scores: 质量评分
            ats_score: ATS兼容性评分
            
        Returns:
            int: 总体评分
        """
        # 权重配置
        weights = {
            "completeness": 0.2,
            "impact": 0.25,
            "relevance": 0.2,
            "clarity": 0.15,
            "ats": 0.2
        }
        
        # 加权计算
        weighted_score = (
            quality_scores.completeness * weights["completeness"] +
            quality_scores.impact * weights["impact"] +
            quality_scores.relevance * weights["relevance"] +
            quality_scores.clarity * weights["clarity"] +
            ats_score * weights["ats"]
        )
        
        return round(weighted_score) 