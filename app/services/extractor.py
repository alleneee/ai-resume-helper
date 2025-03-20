import re
from typing import List, Dict, Any, Optional
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
import datetime

from app.models.resume import ResumeData, ContactInfo, EducationExperience, WorkExperience, Project, Certification, Language
from app.config import get_settings


class StructuredInfoExtractor:
    """结构化信息提取服务"""
    
    def __init__(self):
        settings = get_settings()
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.OPENAI_MODEL,
            temperature=0.2
        )
        
        # 定义提取信息的提示模板
        self.extraction_prompt = PromptTemplate(
            input_variables=["resume_text"],
            template="""
            你是一位专业的简历解析专家，从简历文本中提取结构化信息。
            请从下面的简历文本中提取以下信息:
            1. 联系信息（姓名、邮箱、电话、地址、链接）
            2. 教育经历（学校、学位、专业、时间段、GPA）
            3. 工作经历（公司、职位、时间段、地点、描述、成就）
            4. 项目经历（名称、描述、时间段、技术、链接、成就）
            5. 技能列表
            6. 证书（名称、颁发机构、日期）
            7. 语言能力（语言、水平）
            8. 个人总结/概述

            简历文本:
            ```
            {resume_text}
            ```

            以JSON格式返回结果，格式如下:
            ```json
            {{
                "contact_info": {{
                    "name": "姓名",
                    "email": "邮箱",
                    "phone": "电话",
                    "location": "地址",
                    "links": ["链接1", "链接2"]
                }},
                "education": [
                    {{
                        "institution": "学校名称",
                        "degree": "学位",
                        "field_of_study": "专业",
                        "start_date": "开始日期 (YYYY-MM)",
                        "end_date": "结束日期 (YYYY-MM) 或 'present'",
                        "gpa": "GPA信息",
                        "description": "描述",
                        "achievements": ["成就1", "成就2"]
                    }}
                ],
                "work_experience": [
                    {{
                        "company": "公司名称",
                        "position": "职位",
                        "start_date": "开始日期 (YYYY-MM)",
                        "end_date": "结束日期 (YYYY-MM) 或 'present'",
                        "location": "地点",
                        "description": "职责描述",
                        "achievements": ["成就1", "成就2"]
                    }}
                ],
                "projects": [
                    {{
                        "name": "项目名称",
                        "description": "项目描述",
                        "start_date": "开始日期 (YYYY-MM)",
                        "end_date": "结束日期 (YYYY-MM) 或 'present'",
                        "technologies": ["技术1", "技术2"],
                        "link": "项目链接",
                        "achievements": ["成就1", "成就2"]
                    }}
                ],
                "skills": ["技能1", "技能2", "技能3"],
                "certifications": [
                    {{
                        "name": "证书名称",
                        "issuer": "颁发机构",
                        "date": "获得日期 (YYYY-MM)",
                        "expiry_date": "过期日期 (YYYY-MM)"
                    }}
                ],
                "languages": [
                    {{
                        "name": "语言名称",
                        "level": "水平描述"
                    }}
                ],
                "summary": "个人总结/概述"
            }}
            ```

            请确保JSON格式正确，没有多余的逗号。对于缺失的信息，请使用空值（null）或空数组（[]）或空字符串（""）。
            如果无法确定日期的具体月份，请使用 YYYY-01 表示当年一月。
            """
        )
        
        self.extraction_chain = LLMChain(
            llm=self.llm,
            prompt=self.extraction_prompt
        )
    
    async def extract_info(self, raw_text: str) -> ResumeData:
        """
        从原始文本中提取结构化信息
        
        Args:
            raw_text: 简历原始文本
            
        Returns:
            ResumeData: 结构化的简历数据
        """
        try:
            # 使用LLM提取信息
            extraction_result = await self.extraction_chain.arun(resume_text=raw_text)
            
            # 解析返回的JSON
            parsed_data = self._parse_extraction_result(extraction_result)
            
            # 创建并返回ResumeData对象
            return ResumeData(
                raw_text=raw_text,
                contact_info=self._create_contact_info(parsed_data.get("contact_info", {})),
                education=self._create_education_list(parsed_data.get("education", [])),
                work_experience=self._create_work_experience_list(parsed_data.get("work_experience", [])),
                skills=parsed_data.get("skills", []),
                projects=self._create_project_list(parsed_data.get("projects", [])),
                certifications=self._create_certification_list(parsed_data.get("certifications", [])),
                languages=self._create_language_list(parsed_data.get("languages", [])),
                summary=parsed_data.get("summary", "")
            )
        except Exception as e:
            # 实际应用中应该使用日志记录错误
            print(f"提取结构化信息错误: {str(e)}")
            # 返回仅包含原始文本的对象
            return ResumeData(raw_text=raw_text)
    
    def _parse_extraction_result(self, result: str) -> Dict[str, Any]:
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
                import json
                return json.loads(json_match.group(1))
            
            # 如果没有明确的JSON标记，尝试直接解析整个文本
            import json
            return json.loads(result)
        except Exception as e:
            print(f"JSON解析错误: {str(e)}")
            return {}
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime.date]:
        """
        解析日期字符串
        
        Args:
            date_str: 日期字符串，格式为YYYY-MM
            
        Returns:
            datetime.date: 解析后的日期对象
        """
        if not date_str or date_str.lower() == 'present' or date_str.lower() == 'current':
            return None
        
        try:
            # 尝试解析YYYY-MM格式
            if re.match(r'^\d{4}-\d{2}$', date_str):
                year, month = map(int, date_str.split('-'))
                return datetime.date(year, month, 1)
            
            # 尝试解析YYYY格式
            if re.match(r'^\d{4}$', date_str):
                year = int(date_str)
                return datetime.date(year, 1, 1)
            
            return None
        except ValueError:
            return None
    
    def _create_contact_info(self, data: Dict[str, Any]) -> ContactInfo:
        """创建联系信息对象"""
        return ContactInfo(
            name=data.get("name", ""),
            email=data.get("email"),
            phone=data.get("phone"),
            location=data.get("location"),
            links=data.get("links", [])
        )
    
    def _create_education_list(self, data_list: List[Dict[str, Any]]) -> List[EducationExperience]:
        """创建教育经历列表"""
        result = []
        for data in data_list:
            result.append(EducationExperience(
                institution=data.get("institution", ""),
                degree=data.get("degree"),
                field_of_study=data.get("field_of_study"),
                start_date=self._parse_date(data.get("start_date")),
                end_date=self._parse_date(data.get("end_date")),
                gpa=data.get("gpa"),
                description=data.get("description"),
                achievements=data.get("achievements", [])
            ))
        return result
    
    def _create_work_experience_list(self, data_list: List[Dict[str, Any]]) -> List[WorkExperience]:
        """创建工作经历列表"""
        result = []
        for data in data_list:
            result.append(WorkExperience(
                company=data.get("company", ""),
                position=data.get("position", ""),
                start_date=self._parse_date(data.get("start_date")),
                end_date=self._parse_date(data.get("end_date")),
                location=data.get("location"),
                description=data.get("description"),
                achievements=data.get("achievements", [])
            ))
        return result
    
    def _create_project_list(self, data_list: List[Dict[str, Any]]) -> List[Project]:
        """创建项目经历列表"""
        result = []
        for data in data_list:
            result.append(Project(
                name=data.get("name", ""),
                description=data.get("description"),
                start_date=self._parse_date(data.get("start_date")),
                end_date=self._parse_date(data.get("end_date")),
                technologies=data.get("technologies", []),
                link=data.get("link"),
                achievements=data.get("achievements", [])
            ))
        return result
    
    def _create_certification_list(self, data_list: List[Dict[str, Any]]) -> List[Certification]:
        """创建证书列表"""
        result = []
        for data in data_list:
            result.append(Certification(
                name=data.get("name", ""),
                issuer=data.get("issuer"),
                date=self._parse_date(data.get("date")),
                expiry_date=self._parse_date(data.get("expiry_date")),
                description=data.get("description"),
                link=data.get("link")
            ))
        return result
    
    def _create_language_list(self, data_list: List[Dict[str, Any]]) -> List[Language]:
        """创建语言能力列表"""
        result = []
        for data in data_list:
            result.append(Language(
                name=data.get("name", ""),
                level=data.get("level")
            ))
        return result 