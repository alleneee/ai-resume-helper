import { Request, Response } from 'express';
import { ApiResponse } from '../utils/apiResponse';
import { agentService } from '../services/agentService';
import { logger } from '../utils/logger';

/**
 * Agent 控制器
 * 负责处理与Agent系统相关的请求
 */
export class AgentController {
    /**
     * 优化简历
     * @route POST /api/agent/optimize-resume
     */
    async optimizeResume(req: Request, res: Response) {
        try {
            const { resumeId, jobTitle, location } = req.body;
            const userId = req.user?._id;

            // 验证必要参数
            if (!resumeId) {
                return ApiResponse.validationError(res, 'resumeId 是必需的');
            }

            if (!jobTitle) {
                return ApiResponse.validationError(res, 'jobTitle 是必需的');
            }

            logger.info('开始简历优化流程', { resumeId, jobTitle, userId });

            // 调用Agent服务进行简历优化
            const result = await agentService.run({
                action: 'optimize_resume',
                resumeId,
                jobTitle,
                location
            });

            logger.info('简历优化完成', { resumeId });
            return ApiResponse.success(res, '简历优化成功', result);
        } catch (error: any) {
            logger.error('简历优化失败', { error: error.message });
            return ApiResponse.error(res, error.message);
        }
    }

    /**
     * 获取职位列表
     * @route GET /api/agent/jobs
     */
    async searchJobs(req: Request, res: Response) {
        try {
            const { jobTitle, location, count = 5 } = req.query;
            const userId = req.user?._id;

            // 验证必要参数
            if (!jobTitle) {
                return ApiResponse.validationError(res, 'jobTitle 查询参数是必需的');
            }

            logger.info('开始搜索职位列表', {
                jobTitle: jobTitle as string,
                location: location as string,
                count: Number(count),
                userId
            });

            // 调用爬虫Agent获取职位列表
            const result = await agentService.run({
                action: 'search',
                jobTitle: jobTitle as string,
                location: location as string,
                count: Number(count)
            });

            logger.info('职位搜索完成', { count: result.length });
            return ApiResponse.success(res, '职位搜索成功', result);
        } catch (error: any) {
            logger.error('职位搜索失败', { error: error.message });
            return ApiResponse.error(res, error.message);
        }
    }

    /**
     * 获取职位详情
     * @route GET /api/agent/jobs/:jobId
     */
    async getJobDetails(req: Request, res: Response) {
        try {
            const { jobId } = req.params;
            const userId = req.user?._id;

            if (!jobId) {
                return ApiResponse.validationError(res, 'jobId 参数是必需的');
            }

            logger.info('获取职位详情', { jobId, userId });

            // 调用爬虫Agent获取职位详情
            const result = await agentService.run({
                action: 'details',
                jobId
            });

            logger.info('获取职位详情成功', { jobId });
            return ApiResponse.success(res, '获取职位详情成功', result);
        } catch (error: any) {
            logger.error('获取职位详情失败', { error: error.message });
            return ApiResponse.error(res, error.message);
        }
    }

    /**
     * 分析简历与职位匹配度
     * @route POST /api/agent/analyze-resume
     */
    async analyzeResume(req: Request, res: Response) {
        try {
            const { resumeId, jobId } = req.body;
            const userId = req.user?._id;

            // 验证必要参数
            if (!resumeId) {
                return ApiResponse.validationError(res, 'resumeId 是必需的');
            }

            if (!jobId) {
                return ApiResponse.validationError(res, 'jobId 是必需的');
            }

            logger.info('开始分析简历与职位匹配度', { resumeId, jobId, userId });

            // 1. 获取简历数据
            const resumeData = await agentService.run({
                action: 'get_resume',
                resumeId
            });

            // 2. 获取职位详情
            const jobData = await agentService.run({
                action: 'details',
                jobId
            });

            // 3. 分析匹配度
            const result = await agentService.run({
                action: 'analyze_resume',
                resumeData,
                jobData
            });

            logger.info('简历分析完成', { resumeId, jobId });
            return ApiResponse.success(res, '简历分析成功', result);
        } catch (error: any) {
            logger.error('简历分析失败', { error: error.message });
            return ApiResponse.error(res, error.message);
        }
    }
}

export const agentController = new AgentController();
export default agentController; 