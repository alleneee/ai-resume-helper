"""
简历解析服务 - 负责从各种格式的简历文件中提取文本和结构化数据
"""
import logging
import io
import os
from typing import Dict, List, Optional, Any
import fitz  # PyMuPDF
from docx import Document
import pytesseract
from PIL import Image
import re
import spacy
import tempfile

logger = logging.getLogger(__name__)

class ResumeParserService:
    """解析各种格式的简历文件并提取结构化信息"""
    
    def __init__(self):
        # 加载NLP模型用于实体识别
        try:
            self.nlp = spacy.load("zh_core_web_sm")
            logger.info("加载中文NLP模型成功")
        except:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("加载英文NLP模型成功")
            except:
                logger.warning("无法加载NLP模型，将使用基础模型")
                self.nlp = spacy.blank("zh")
                self.nlp.add_pipe("ner")
    
    async def parse_resume(self, file_content: bytes, content_type: str) -> Dict[str, Any]:
        """
        解析简历文件，提取文本和结构化数据
        
        Args:
            file_content: 文件二进制内容
            content_type: 文件MIME类型
            
        Returns:
            Dict包含解析结果，包括原始文本和结构化数据
        """
        logger.info(f"开始解析简历，文件类型: {content_type}")
        
        # 提取文本
        if content_type == 'application/pdf':
            text = await self._extract_text_from_pdf(file_content)
        elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            text = await self._extract_text_from_docx(file_content)
        elif content_type in ['image/jpeg', 'image/png']:
            text = await self._extract_text_from_image(file_content)
        elif content_type == 'text/plain':
            text = file_content.decode('utf-8')
        else:
            raise ValueError(f"不支持的文件类型: {content_type}")
        
        # 提取结构化信息
        structured_data = await self._extract_structured_info(text)
        
        return {
            "raw_text": text,
            "structured_data": structured_data
        }
    
    async def _extract_text_from_pdf(self, file_content: bytes) -> str:
        """从PDF文件中提取文本"""
        try:
            with fitz.open(stream=file_content, filetype="pdf") as doc:
                text = ""
                for page in doc:
                    text += page.get_text()
                return text
        except Exception as e:
            logger.error(f"PDF文本提取错误: {str(e)}")
            raise
    
    async def _extract_text_from_docx(self, file_content: bytes) -> str:
        """从DOCX文件中提取文本"""
        try:
            with io.BytesIO(file_content) as f:
                doc = Document(f)
                return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            logger.error(f"DOCX文本提取错误: {str(e)}")
            raise
    
    async def _extract_text_from_image(self, file_content: bytes) -> str:
        """从图片中提取文本"""
        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                temp.write(file_content)
                temp_filename = temp.name
            
            img = Image.open(temp_filename)
            text = pytesseract.image_to_string(img, lang='chi_sim+eng')
            
            # 清理临时文件
            os.unlink(temp_filename)
            
            return text
        except Exception as e:
            logger.error(f"图片文本提取错误: {str(e)}")
            raise
    
    async def _extract_structured_info(self, text: str) -> Dict[str, Any]:
        """
        从文本中提取结构化信息
        
        Args:
            text: 简历文本
            
        Returns:
            包含结构化数据的字典
        """
        # 基本结构
        result = {
            "contact_info": await self._extract_contact_info(text),
            "education": await self._extract_education(text),
            "experience": await self._extract_work_experience(text),
            "skills": await self._extract_skills(text),
            "projects": await self._extract_projects(text),
            "certifications": await self._extract_certifications(text)
        }
        
        return result
    
    async def _extract_contact_info(self, text: str) -> Dict[str, str]:
        """提取联系信息"""
        contact_info = {
            "name": None,
            "phone": None,
            "email": None,
            "location": None,
            "links": []
        }
        
        # 提取电子邮件
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, text)
        if email_matches:
            contact_info["email"] = email_matches[0]
        
        # 提取手机号
        phone_pattern = r'(?:13[0-9]|14[01456879]|15[0-35-9]|16[2567]|17[0-8]|18[0-9]|19[0-35-9])\d{8}'
        phone_matches = re.findall(phone_pattern, text)
        if phone_matches:
            contact_info["phone"] = phone_matches[0]
        
        # 尝试提取姓名 (这通常需要更复杂的逻辑或NLP)
        # 这里简单处理：假设姓名出现在开头的几行
        first_lines = text.split('\n')[:5]
        for line in first_lines:
            line = line.strip()
            if line and len(line) < 10 and not any(char.isdigit() for char in line):
                if not re.search(email_pattern, line) and not re.search(phone_pattern, line):
                    contact_info["name"] = line
                    break
        
        # 提取链接
        link_pattern = r'https?://\S+'
        links = re.findall(link_pattern, text)
        if links:
            contact_info["links"] = links
        
        return contact_info
    
    async def _extract_education(self, text: str) -> List[Dict[str, Any]]:
        """提取教育经历"""
        education = []
        
        # 查找教育部分
        education_section = self._find_section(text, ['教育背景', '教育经历', 'Education', '学历'])
        if not education_section:
            return education
        
        # 简单的模式匹配
        # 这里使用正则表达式来查找常见的教育信息模式
        school_pattern = r'((?:北京|清华|复旦|上海|南京|浙江|中国|人民|科技|师范|西安|南开|武汉|山东|四川|华中|电子|交通|哈尔滨|华南|东南|暨南|深圳|广州|厦门|天津|重庆|兰州|吉林|东北|西南|西北|华东|中山|海南|宁波|合肥|大连|苏州|西安交通|北京师范|华南理工|对外经济贸易|中国人民|中国科学技术)[^，。,.\n]{0,10}(?:大学|学院|University))'
        degree_pattern = r'((?:博士|硕士|学士|本科|专科|研究生|PhD|Master|Bachelor)(?:学位)?)'
        date_pattern = r'((?:19|20)\d{2}年\d{1,2}月|(?:19|20)\d{2}/\d{1,2}|(?:19|20)\d{2}\.\d{1,2}|(?:19|20)\d{2}[-/][0-9]{1,2})'
        
        # 查找所有匹配项
        schools = re.findall(school_pattern, education_section)
        degrees = re.findall(degree_pattern, education_section)
        dates = re.findall(date_pattern, education_section)
        
        # 如果找到足够的信息，创建教育条目
        if schools:
            for i, school in enumerate(schools):
                edu_entry = {
                    "institution": school,
                    "degree": degrees[i] if i < len(degrees) else None,
                    "startDate": None,
                    "endDate": None,
                    "major": None
                }
                
                # 尝试从上下文中提取专业
                school_index = education_section.find(school)
                if school_index != -1:
                    context = education_section[school_index:school_index + 100]
                    major_match = re.search(r'专业[:：]?\s*([^，。,.\n]{2,20})', context)
                    if major_match:
                        edu_entry["major"] = major_match.group(1)
                
                # 添加日期（如果可用）
                if i*2+1 < len(dates):
                    edu_entry["startDate"] = dates[i*2]
                    edu_entry["endDate"] = dates[i*2+1]
                
                education.append(edu_entry)
        
        return education
    
    async def _extract_work_experience(self, text: str) -> List[Dict[str, Any]]:
        """提取工作经验"""
        experience = []
        
        # 查找工作经验部分
        work_section = self._find_section(text, ['工作经历', '工作经验', 'Experience', '实习经历', '实习经验'])
        if not work_section:
            return experience
        
        # 查找公司名和职位
        company_pattern = r'([\u4e00-\u9fa5a-zA-Z0-9]{2,}(?:公司|集团|企业|科技|银行|有限|责任|株式会社|Corporation|Inc\.|Ltd\.|LLC|Company))'
        position_pattern = r'((?:高级|初级|资深|主任|主管|总监|经理|助理|实习|工程师|开发|设计师|架构师|专员|顾问|分析师|产品|运营|研发|测试|市场|销售|客户|技术支持|客服|行政|人力资源|财务|会计|审计|法务|采购|物流|仓储|质控|安全|维护|管理|总裁|副总裁|CEO|CTO|CFO|COO|GM|VP|PM|UI|UX|HR|PR|BD)(?:[^，。,.\n]{0,10})?(?:工程师|开发|设计师|架构师|专员|顾问|分析师|经理|助理|主管|总监|负责人)?)'
        date_pattern = r'((?:19|20)\d{2}年\d{1,2}月|(?:19|20)\d{2}/\d{1,2}|(?:19|20)\d{2}\.\d{1,2}|(?:19|20)\d{2}[-/][0-9]{1,2})'
        
        # 查找所有匹配项
        companies = re.findall(company_pattern, work_section)
        positions = re.findall(position_pattern, work_section)
        dates = re.findall(date_pattern, work_section)
        
        # 创建工作经验条目
        for i, company in enumerate(companies):
            if i >= len(positions):
                break
                
            exp_entry = {
                "company": company,
                "position": positions[i],
                "startDate": None,
                "endDate": None,
                "description": "",
                "achievements": []
            }
            
            # 添加日期（如果可用）
            if i*2+1 < len(dates):
                exp_entry["startDate"] = dates[i*2]
                exp_entry["endDate"] = dates[i*2+1]
            
            # 尝试提取工作描述
            company_index = work_section.find(company)
            if company_index != -1:
                # 假设描述在公司名之后，可能持续到下一个公司名或部分的开始
                next_company_index = work_section.find(companies[i+1]) if i+1 < len(companies) else len(work_section)
                description_text = work_section[company_index + len(company):next_company_index].strip()
                
                # 清理描述文本
                description_text = re.sub(r'\s+', ' ', description_text)
                exp_entry["description"] = description_text
                
                # 尝试提取成就
                achievement_lines = re.findall(r'[•·-]\s*([^•·\n-]+)', description_text)
                if achievement_lines:
                    exp_entry["achievements"] = achievement_lines
            
            experience.append(exp_entry)
        
        return experience
    
    async def _extract_skills(self, text: str) -> List[str]:
        """提取技能"""
        skills = []
        
        # 查找技能部分
        skills_section = self._find_section(text, ['技能', '技术', 'Skills', '专业技能', '专业知识'])
        if not skills_section:
            return skills
        
        # 技术技能常见关键词
        tech_skills = [
            "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "PHP", "Ruby", "Swift", "Kotlin",
            "React", "Vue", "Angular", "Node.js", "Django", "Flask", "Spring", "Express", "Laravel", "Ruby on Rails",
            "HTML", "CSS", "SQL", "NoSQL", "MongoDB", "MySQL", "PostgreSQL", "Oracle", "Redis", "Elasticsearch",
            "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Git", "Jenkins", "CI/CD", "Linux", "Unix",
            "机器学习", "深度学习", "人工智能", "数据分析", "自然语言处理", "计算机视觉", "统计学", "大数据",
            "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "Pandas", "NumPy", "Matplotlib", "SPSS", "R",
            "UI设计", "UX设计", "产品设计", "交互设计", "视觉设计", "平面设计", "Figma", "Sketch", "Adobe XD",
            "Photoshop", "Illustrator", "InDesign", "After Effects", "Premiere Pro"
        ]
        
        # 软技能关键词
        soft_skills = [
            "沟通", "团队协作", "领导力", "解决问题", "创新", "创意", "批判性思维", "时间管理", "项目管理",
            "自主学习", "适应性", "灵活性", "抗压能力", "谈判", "演讲", "表达能力", "情商", "责任心"
        ]
        
        # 寻找技能
        all_skills = tech_skills + soft_skills
        found_skills = set()
        
        for skill in all_skills:
            if skill.lower() in skills_section.lower() or skill in skills_section:
                found_skills.add(skill)
        
        # 额外尝试寻找列表中的技能
        # 通常技能以列表形式呈现（逗号分隔、分号分隔或换行分隔）
        skill_candidates = re.split(r'[,，;；、\n]+', skills_section)
        for candidate in skill_candidates:
            candidate = candidate.strip()
            if 2 <= len(candidate) <= 20 and any(char.isalnum() for char in candidate):
                found_skills.add(candidate)
        
        return list(found_skills)
    
    async def _extract_projects(self, text: str) -> List[Dict[str, Any]]:
        """提取项目经验"""
        projects = []
        
        # 查找项目经验部分
        project_section = self._find_section(text, ['项目经验', '项目', 'Projects', '项目经历'])
        if not project_section:
            return projects
        
        # 查找项目名称
        project_pattern = r'项目[:：]?\s*([^，。,.\n]{2,30})|([^，。,.\n]{2,30})\s*项目'
        role_pattern = r'角色[:：]?\s*([^，。,.\n]{2,20})|担任\s*([^，。,.\n]{2,20})'
        tech_pattern = r'技术栈[:：]?\s*([^，。,.\n]{2,50})|技术[:：]?\s*([^，。,.\n]{2,50})'
        
        # 查找所有匹配项
        project_matches = re.findall(project_pattern, project_section)
        
        # 处理项目匹配结果
        for match in project_matches:
            project_name = match[0] if match[0] else match[1]
            
            if not project_name:
                continue
                
            project_entry = {
                "name": project_name,
                "role": None,
                "technologies": [],
                "description": ""
            }
            
            # 尝试从上下文中提取更多信息
            project_index = project_section.find(project_name)
            if project_index != -1:
                # 假设描述在项目名之后，可能持续到下一个项目或部分的开始
                next_project_index = -1
                for other_match in project_matches:
                    other_name = other_match[0] if other_match[0] else other_match[1]
                    if other_name != project_name:
                        other_index = project_section.find(other_name, project_index + len(project_name))
                        if other_index != -1 and (next_project_index == -1 or other_index < next_project_index):
                            next_project_index = other_index
                
                if next_project_index == -1:
                    next_project_index = len(project_section)
                
                context = project_section[project_index:next_project_index]
                
                # 提取角色
                role_match = re.search(role_pattern, context)
                if role_match:
                    project_entry["role"] = role_match.group(1) if role_match.group(1) else role_match.group(2)
                
                # 提取技术栈
                tech_match = re.search(tech_pattern, context)
                if tech_match:
                    tech_text = tech_match.group(1) if tech_match.group(1) else tech_match.group(2)
                    technologies = re.split(r'[,，;；、/]+', tech_text)
                    project_entry["technologies"] = [tech.strip() for tech in technologies if tech.strip()]
                
                # 清理并添加描述
                description_text = re.sub(r'\s+', ' ', context).strip()
                project_entry["description"] = description_text
            
            projects.append(project_entry)
        
        return projects
    
    async def _extract_certifications(self, text: str) -> List[Dict[str, str]]:
        """提取证书"""
        certifications = []
        
        # 查找证书部分
        cert_section = self._find_section(text, ['证书', '资格证书', 'Certifications', '职业资格', '认证'])
        if not cert_section:
            return certifications
        
        # 常见证书名称模式
        cert_pattern = r'(?:CET-[46]|托福|雅思|TOEFL|IELTS|PMP|PRINCE2|CSM|CSPO|PMI-ACP|CAPM|ITIL|MCSE|MCSA|MCSD|RHCE|RHCSA|AWS|Azure|GCP|CompTIA|CISA|CISM|CISSP|CEH|CCNA|CCNP|CCIE|OCP|OCA|CFA|CPA|FRM|ACCA)[^，。,.\n]{0,30}'
        
        # 查找所有匹配项
        cert_matches = re.findall(cert_pattern, cert_section)
        
        # 创建证书条目
        for cert in cert_matches:
            certifications.append({
                "name": cert.strip(),
                "issuer": None,
                "date": None
            })
        
        # 如果没有常见证书匹配，尝试从文本中提取可能的证书
        if not certifications:
            lines = cert_section.split('\n')
            for line in lines:
                line = line.strip()
                if line and 3 <= len(line) <= 50 and not line.startswith('证书') and '证' in line:
                    certifications.append({
                        "name": line,
                        "issuer": None,
                        "date": None
                    })
        
        return certifications
    
    def _find_section(self, text: str, section_names: List[str]) -> Optional[str]:
        """
        在文本中查找特定部分(如教育、工作经验等)
        
        Args:
            text: 完整文本
            section_names: 可能的部分标题列表
            
        Returns:
            找到的部分文本，如果没找到则返回None
        """
        lines = text.split('\n')
        start_index = -1
        
        # 寻找部分开始
        for i, line in enumerate(lines):
            if any(name in line for name in section_names):
                start_index = i
                break
        
        if start_index == -1:
            return None
        
        # 寻找部分结束 (下一个主要部分的开始)
        common_sections = [
            '教育', '工作', '项目', '技能', '证书', '自我评价', '个人信息',
            'Education', 'Experience', 'Projects', 'Skills', 'Certifications'
        ]
        
        end_index = len(lines)
        for i in range(start_index + 1, len(lines)):
            line = lines[i]
            # 检查是否是一个新的主要部分
            if any(section in line and section not in section_names for section in common_sections):
                end_index = i
                break
        
        # 提取并返回部分内容
        section_text = '\n'.join(lines[start_index:end_index])
        return section_text 