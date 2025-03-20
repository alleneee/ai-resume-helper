import fs from 'fs';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';
import Resume, { ResumeDocument, ResumeStatus } from '../models/Resume';
import { logger } from '../utils/logger';
import { config } from '../config/app';
import { ApplicationError } from '../middleware/errorHandler';
import { ErrorCodes } from '../utils/apiResponse';

export interface ResumeUploadOptions {
    originalName: string;
    mimeType: string;
    size: number;
    buffer: Buffer;
    userId: string;
    jobTitle?: string;
    jobDescription?: string;
}

export interface ResumeQueryOptions {
    userId?: string;
    status?: ResumeStatus | ResumeStatus[];
    skip?: number;
    limit?: number;
    sortBy?: string;
    sortOrder?: 'asc' | 'desc';
}

export class ResumeService {
    /**
     * 上传简历
     */
    static async uploadResume(options: ResumeUploadOptions): Promise<ResumeDocument> {
        try {
            // 验证文件类型
            if (!this.isAllowedMimeType(options.mimeType)) {
                throw new ApplicationError(
                    ErrorCodes.UNSUPPORTED_FILE_TYPE,
                    '不支持的文件类型',
                    400
                );
            }

            // 验证文件大小
            if (options.size > config.upload.maxFileSize) {
                throw new ApplicationError(
                    ErrorCodes.FILE_TOO_LARGE,
                    `文件大小超出限制，最大支持${config.upload.maxFileSize / (1024 * 1024)}MB`,
                    400
                );
            }

            // 生成唯一文件名
            const fileName = this.generateFileName(options.originalName);
            const filePath = path.join(config.upload.directory, fileName);

            // 确保上传目录存在
            await this.ensureUploadDirectory();

            // 写入文件
            await fs.promises.writeFile(filePath, options.buffer);

            // 创建简历记录
            const resume = new Resume({
                userId: options.userId,
                fileName,
                originalName: options.originalName,
                mimeType: options.mimeType,
                fileSize: options.size,
                filePath,
                status: ResumeStatus.UPLOADED,
                jobTitle: options.jobTitle,
                jobDescription: options.jobDescription
            });

            // 保存到数据库
            await resume.save();

            logger.info('简历上传成功', {
                resumeId: resume._id,
                userId: options.userId,
                fileName
            });

            return resume;
        } catch (error) {
            // 如果发生错误，删除可能已经创建的文件
            try {
                const filePath = path.join(config.upload.directory, this.generateFileName(options.originalName));
                if (fs.existsSync(filePath)) {
                    await fs.promises.unlink(filePath);
                }
            } catch (e) {
                logger.error('清理上传文件失败', e);
            }

            logger.error('简历上传失败', error);
            throw error;
        }
    }

    /**
     * 获取简历列表
     */
    static async getResumes(options: ResumeQueryOptions = {}): Promise<{
        resumes: ResumeDocument[],
        total: number,
        page: number,
        limit: number,
        totalPages: number
    }> {
        try {
            const {
                userId,
                status,
                skip = 0,
                limit = 10,
                sortBy = 'uploadDate',
                sortOrder = 'desc'
            } = options;

            // 构建查询条件
            const query: any = {};

            if (userId) {
                query.userId = userId;
            }

            if (status) {
                if (Array.isArray(status)) {
                    query.status = { $in: status };
                } else {
                    query.status = status;
                }
            }

            // 计算总数
            const total = await Resume.countDocuments(query);

            // 获取简历列表
            const resumes = await Resume.find(query)
                .sort({ [sortBy]: sortOrder === 'desc' ? -1 : 1 })
                .skip(skip)
                .limit(limit);

            // 计算总页数
            const totalPages = Math.ceil(total / limit);
            const page = Math.floor(skip / limit) + 1;

            return {
                resumes,
                total,
                page,
                limit,
                totalPages
            };
        } catch (error) {
            logger.error('获取简历列表失败', error);
            throw error;
        }
    }

    /**
     * 获取简历详情
     */
    static async getResumeById(resumeId: string, userId?: string): Promise<ResumeDocument> {
        try {
            const query: any = { _id: resumeId };

            // 如果提供了userId，添加到查询条件
            if (userId) {
                query.userId = userId;
            }

            const resume = await Resume.findOne(query);

            if (!resume) {
                throw new ApplicationError(
                    ErrorCodes.RESUME_NOT_FOUND,
                    '找不到指定的简历',
                    404
                );
            }

            return resume;
        } catch (error) {
            logger.error('获取简历详情失败', error);
            throw error;
        }
    }

    /**
     * 更新简历状态
     */
    static async updateResumeStatus(
        resumeId: string,
        status: ResumeStatus,
        error?: string
    ): Promise<ResumeDocument> {
        try {
            const resume = await Resume.findById(resumeId);

            if (!resume) {
                throw new ApplicationError(
                    ErrorCodes.RESUME_NOT_FOUND,
                    '找不到指定的简历',
                    404
                );
            }

            resume.status = status;
            resume.lastUpdated = new Date();

            if (error) {
                resume.error = error;
            }

            await resume.save();

            logger.info('简历状态已更新', {
                resumeId,
                status,
                error
            });

            return resume;
        } catch (error) {
            logger.error('更新简历状态失败', error);
            throw error;
        }
    }

    /**
     * 更新简历分析结果
     */
    static async updateResumeAnalysis(
        resumeId: string,
        analysis: any,
        score?: number
    ): Promise<ResumeDocument> {
        try {
            const resume = await Resume.findById(resumeId);

            if (!resume) {
                throw new ApplicationError(
                    ErrorCodes.RESUME_NOT_FOUND,
                    '找不到指定的简历',
                    404
                );
            }

            resume.analysis = analysis;

            if (score !== undefined) {
                resume.score = score;
            }

            resume.status = ResumeStatus.ANALYZED;
            resume.lastUpdated = new Date();

            await resume.save();

            logger.info('简历分析结果已更新', { resumeId });

            return resume;
        } catch (error) {
            logger.error('更新简历分析结果失败', error);
            throw error;
        }
    }

    /**
     * 删除简历
     */
    static async deleteResume(resumeId: string, userId?: string): Promise<void> {
        try {
            const query: any = { _id: resumeId };

            // 如果提供了userId，添加到查询条件
            if (userId) {
                query.userId = userId;
            }

            const resume = await Resume.findOne(query);

            if (!resume) {
                throw new ApplicationError(
                    ErrorCodes.RESUME_NOT_FOUND,
                    '找不到指定的简历',
                    404
                );
            }

            // 删除文件
            try {
                if (fs.existsSync(resume.filePath)) {
                    await fs.promises.unlink(resume.filePath);
                }
            } catch (error) {
                logger.warn('删除简历文件失败', {
                    resumeId,
                    filePath: resume.filePath,
                    error
                });
            }

            // 从数据库中删除记录
            await Resume.deleteOne({ _id: resumeId });

            logger.info('简历已删除', { resumeId });
        } catch (error) {
            logger.error('删除简历失败', error);
            throw error;
        }
    }

    /**
     * 检查文件类型是否被允许
     */
    private static isAllowedMimeType(mimeType: string): boolean {
        return config.upload.allowedMimeTypes.includes(mimeType);
    }

    /**
     * 生成唯一的文件名
     */
    private static generateFileName(originalName: string): string {
        const fileExt = path.extname(originalName);
        const uniqueId = uuidv4();
        const timestamp = Date.now();

        return `${uniqueId}-${timestamp}${fileExt}`;
    }

    /**
     * 确保上传目录存在
     */
    private static async ensureUploadDirectory(): Promise<void> {
        try {
            await fs.promises.access(config.upload.directory);
        } catch (error) {
            // 目录不存在，创建它
            await fs.promises.mkdir(config.upload.directory, { recursive: true });
        }
    }
} 