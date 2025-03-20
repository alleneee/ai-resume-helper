import fs from 'fs';
import axios from 'axios';
import { config } from '../config/app';
import { logger } from '../utils/logger';
import { ApplicationError } from '../middleware/errorHandler';
import { ErrorCodes } from '../utils/apiResponse';
import { ResumeDocument, ResumeStatus } from '../models/Resume';
import { ResumeService } from './resumeService';

export class AIService {
    /**
     * 处理简历分析
     */
    static async analyzeResume(resumeId: string): Promise<ResumeDocument> {
        try {
            // 获取简历信息
            const resume = await ResumeService.getResumeById(resumeId);

            // 更新状态为处理中
            await ResumeService.updateResumeStatus(resumeId, ResumeStatus.PROCESSING);

            // 提取简历文本
            const resumeText = await this.extractTextFromFile(resume.filePath, resume.mimeType);

            // 构建分析提示
            const prompt = this.buildAnalysisPrompt(resumeText, resume.jobTitle, resume.jobDescription);

            // 调用AI服务进行分析
            const analysisResult = await this.callAIService(prompt);

            // 解析AI返回的结果
            const { analysis, score } = this.parseAnalysisResult(analysisResult);

            // 更新简历分析结果
            return await ResumeService.updateResumeAnalysis(resumeId, analysis, score);
        } catch (error: any) {
            logger.error('简历分析失败', {
                resumeId,
                error: error.message,
                stack: error.stack
            });

            // 更新状态为失败
            await ResumeService.updateResumeStatus(
                resumeId,
                ResumeStatus.FAILED,
                error.message || '分析过程中发生错误'
            );

            throw new ApplicationError(
                ErrorCodes.RESUME_ANALYSIS_FAILED,
                '简历分析失败: ' + (error.message || '未知错误'),
                500
            );
        }
    }

    /**
     * 从文件中提取文本
     */
    private static async extractTextFromFile(filePath: string, mimeType: string): Promise<string> {
        // 这里简化实现，实际生产环境应使用更健壮的解析库（如pdf.js、docx等）
        try {
            // 检查文件是否存在
            if (!fs.existsSync(filePath)) {
                throw new Error('文件不存在');
            }

            // 读取文件内容
            const fileBuffer = await fs.promises.readFile(filePath);

            // 根据文件类型进行处理
            switch (mimeType) {
                case 'application/pdf':
                    // 这里仅为示例，实际应使用pdf解析库
                    return '这里是从PDF提取的文本';

                case 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                case 'application/msword':
                    // 这里仅为示例，实际应使用docx解析库
                    return '这里是从Word文档提取的文本';

                case 'text/plain':
                    // 文本文件直接返回内容
                    return fileBuffer.toString('utf-8');

                case 'image/jpeg':
                case 'image/png':
                    // 这里仅为示例，实际应使用OCR服务
                    return '这里是从图片OCR提取的文本';

                default:
                    throw new Error(`不支持的文件类型: ${mimeType}`);
            }
        } catch (error) {
            logger.error('文本提取失败', { filePath, mimeType, error });
            throw new Error(`文本提取失败: ${(error as Error).message}`);
        }
    }

    /**
     * 构建分析提示
     */
    private static buildAnalysisPrompt(
        resumeText: string,
        jobTitle?: string,
        jobDescription?: string
    ): string {
        let prompt = `请分析以下简历文本，提取关键信息并给出评价：\n\n${resumeText}\n\n`;

        if (jobTitle) {
            prompt += `应聘职位: ${jobTitle}\n\n`;
        }

        if (jobDescription) {
            prompt += `职位描述: ${jobDescription}\n\n`;
        }

        prompt += `请提供以下分析结果：
1. 技能列表（包括技能名称、水平、类别和相关性）
2. 工作经历（包括职位、公司、时间段、职责描述和亮点）
3. 教育背景（包括学校、学位、专业和时间段）
4. 简历总结
5. 优势和不足
6. 针对职位的改进建议
7. 关键词
8. 评分（100分制，包括相关性、完整性、格式和语言）

请以JSON格式返回，格式如下：
{
  "skills": [{"name": "技能名称", "level": "水平", "category": "类别", "relevance": 数值}],
  "experience": [{"title": "职位", "company": "公司", "startDate": "开始日期", "endDate": "结束日期", "description": "描述", "highlights": ["亮点1", "亮点2"]}],
  "education": [{"institution": "学校", "degree": "学位", "field": "专业", "startDate": "开始日期", "endDate": "结束日期", "gpa": 分数}],
  "summary": "总结",
  "strengths": ["优势1", "优势2"],
  "weaknesses": ["不足1", "不足2"],
  "recommendations": ["建议1", "建议2"],
  "keywords": ["关键词1", "关键词2"],
  "scoreDetails": {
    "relevanceScore": 分数,
    "completenessScore": 分数,
    "formattingScore": 分数,
    "languageScore": 分数,
    "overallScore": 分数
  }
}`;

        return prompt;
    }

    /**
     * 调用AI服务
     */
    private static async callAIService(prompt: string): Promise<string> {
        try {
            // 根据配置选择不同的AI提供商
            switch (config.ai.provider) {
                case 'openai':
                    return await this.callOpenAI(prompt);

                // 可以添加其他AI提供商的支持
                default:
                    throw new Error(`不支持的AI提供商: ${config.ai.provider}`);
            }
        } catch (error) {
            logger.error('AI服务调用失败', error);
            throw new Error(`AI服务调用失败: ${(error as Error).message}`);
        }
    }

    /**
     * 调用OpenAI API
     */
    private static async callOpenAI(prompt: string): Promise<string> {
        try {
            // 检查API密钥是否配置
            if (!config.ai.apiKey) {
                throw new Error('未配置OpenAI API密钥');
            }

            // 调用OpenAI API
            const response = await axios.post(
                'https://api.openai.com/v1/chat/completions',
                {
                    model: config.ai.model,
                    messages: [
                        {
                            role: 'system',
                            content: '你是一个专业的简历分析师，擅长提取简历中的关键信息并给出客观评价。请以JSON格式返回分析结果。'
                        },
                        {
                            role: 'user',
                            content: prompt
                        }
                    ],
                    max_tokens: config.ai.maxTokens,
                    temperature: config.ai.temperature
                },
                {
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${config.ai.apiKey}`
                    }
                }
            );

            // 提取AI返回的文本
            return response.data.choices[0].message.content;
        } catch (error: any) {
            logger.error('OpenAI API调用失败', {
                error: error.message,
                response: error.response?.data
            });

            throw new Error(`OpenAI API调用失败: ${error.message}`);
        }
    }

    /**
     * 解析AI返回的分析结果
     */
    private static parseAnalysisResult(resultText: string): {
        analysis: any;
        score: number;
    } {
        try {
            // 提取JSON部分
            const jsonMatch = resultText.match(/\{[\s\S]*\}/);
            if (!jsonMatch) {
                throw new Error('无法从AI响应中提取JSON数据');
            }

            // 解析JSON
            const analysisData = JSON.parse(jsonMatch[0]);

            // 确保scoreDetails存在
            if (!analysisData.scoreDetails) {
                analysisData.scoreDetails = {
                    relevanceScore: 0,
                    completenessScore: 0,
                    formattingScore: 0,
                    languageScore: 0,
                    overallScore: 0
                };
            }

            // 计算总分
            const score = analysisData.scoreDetails.overallScore ||
                Math.round(
                    (analysisData.scoreDetails.relevanceScore +
                        analysisData.scoreDetails.completenessScore +
                        analysisData.scoreDetails.formattingScore +
                        analysisData.scoreDetails.languageScore) / 4
                );

            return {
                analysis: analysisData,
                score
            };
        } catch (error) {
            logger.error('解析AI分析结果失败', { resultText, error });
            throw new Error(`解析AI分析结果失败: ${(error as Error).message}`);
        }
    }
} 