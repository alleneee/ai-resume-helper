import { Request, Response } from 'express';
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import { v4 as uuidv4 } from 'uuid';
import { ResumeService } from '../services/resumeService';
import { AIService } from '../services/aiService';
import { createSuccessResponse, createErrorResponse, ErrorCodes } from '../utils/apiResponse';
import { config } from '../config/app';
import { logger } from '../utils/logger';
import { asyncHandler } from '../middleware/errorHandler';
import { validateRequest } from '../middleware/validateRequest';

// 确保上传目录存在
const uploadDir = config.upload.directory;
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir, { recursive: true });
}

// 配置 Multer 存储
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, uploadDir);
    },
    filename: (req, file, cb) => {
        const uniqueSuffix = `${Date.now()}-${uuidv4()}`;
        cb(null, `${uniqueSuffix}${path.extname(file.originalname)}`);
    }
});

// 文件过滤器
const fileFilter = (req: Request, file: Express.Multer.File, cb: multer.FileFilterCallback) => {
    const allowedMimeTypes = config.upload.allowedMimeTypes;
    if (allowedMimeTypes.includes(file.mimetype)) {
        cb(null, true);
    } else {
        cb(new Error(`不支持的文件类型：${file.mimetype}`));
    }
};

// 创建 Multer 实例
const upload = multer({
    storage,
    fileFilter,
    limits: {
        fileSize: config.upload.maxFileSize
    }
});

/**
 * 上传简历
 */
export const uploadResume = [
    // 使用 Multer 中间件处理文件上传
    upload.single('resume'),

    // 验证请求体中的其他字段
    validateRequest({
        body: {
            jobTitle: {
                type: 'string',
                required: false
            },
            jobDescription: {
                type: 'string',
                required: false
            }
        }
    }),

    // 处理上传请求
    asyncHandler(async (req: Request, res: Response) => {
        if (!req.file) {
            return res.status(400).json(
                createErrorResponse(
                    ErrorCodes.BAD_REQUEST,
                    '没有上传文件'
                )
            );
        }

        // 获取用户ID，暂时使用默认值
        const userId = req.user?.id || 'guest';

        try {
            // 读取上传的文件
            const fileBuffer = await fs.promises.readFile(req.file.path);

            // 使用 ResumeService 处理上传
            const resume = await ResumeService.uploadResume({
                originalName: req.file.originalname,
                mimeType: req.file.mimetype,
                size: req.file.size,
                buffer: fileBuffer,
                userId,
                jobTitle: req.body.jobTitle,
                jobDescription: req.body.jobDescription
            });

            // 删除临时文件（因为 ResumeService 已经保存了文件）
            await fs.promises.unlink(req.file.path);

            // 异步启动分析过程
            AIService.analyzeResume(resume._id.toString())
                .catch(error => {
                    logger.error('启动简历分析过程失败', { resumeId: resume._id, error });
                });

            // 返回成功响应
            return res.status(201).json(
                createSuccessResponse({
                    resumeId: resume._id,
                    fileName: resume.originalName,
                    uploadDate: resume.uploadDate,
                    status: resume.status
                })
            );
        } catch (error: any) {
            // 如果有临时文件，清理它
            if (req.file && fs.existsSync(req.file.path)) {
                await fs.promises.unlink(req.file.path).catch(() => { /* 忽略清理错误 */ });
            }

            // 返回错误响应
            return res.status(error.statusCode || 500).json(
                createErrorResponse(
                    error.code || ErrorCodes.RESUME_UPLOAD_FAILED,
                    error.message || '简历上传失败',
                    error.details
                )
            );
        }
    })
];

/**
 * 获取简历列表
 */
export const getResumes = [
    validateRequest({
        query: {
            page: {
                type: 'number',
                required: false
            },
            limit: {
                type: 'number',
                required: false
            },
            status: {
                type: 'string',
                required: false,
                enum: ['uploaded', 'processing', 'analyzed', 'failed']
            }
        }
    }),

    asyncHandler(async (req: Request, res: Response) => {
        // 获取用户ID，暂时使用默认值
        const userId = req.user?.id || 'guest';

        // 解析分页参数
        const page = parseInt(req.query.page as string) || 1;
        const limit = parseInt(req.query.limit as string) || 10;
        const skip = (page - 1) * limit;

        // 解析状态过滤器
        const status = req.query.status as string;

        try {
            // 获取简历列表
            const result = await ResumeService.getResumes({
                userId,
                status: status ? status as any : undefined,
                skip,
                limit
            });

            // 返回成功响应
            return res.json(
                createSuccessResponse(
                    result.resumes,
                    {
                        pagination: {
                            page: result.page,
                            limit: result.limit,
                            total: result.total,
                            totalPages: result.totalPages
                        }
                    }
                )
            );
        } catch (error: any) {
            return res.status(error.statusCode || 500).json(
                createErrorResponse(
                    error.code || ErrorCodes.SERVER_ERROR,
                    error.message || '获取简历列表失败',
                    error.details
                )
            );
        }
    })
];

/**
 * 获取简历详情
 */
export const getResumeById = [
    validateRequest({
        params: {
            id: {
                type: 'string',
                required: true
            }
        }
    }),

    asyncHandler(async (req: Request, res: Response) => {
        const resumeId = req.params.id;
        const userId = req.user?.id || 'guest';

        try {
            const resume = await ResumeService.getResumeById(resumeId, userId);

            return res.json(
                createSuccessResponse(resume)
            );
        } catch (error: any) {
            return res.status(error.statusCode || 500).json(
                createErrorResponse(
                    error.code || ErrorCodes.SERVER_ERROR,
                    error.message || '获取简历详情失败',
                    error.details
                )
            );
        }
    })
];

/**
 * 下载简历文件
 */
export const downloadResume = [
    validateRequest({
        params: {
            id: {
                type: 'string',
                required: true
            }
        }
    }),

    asyncHandler(async (req: Request, res: Response) => {
        const resumeId = req.params.id;
        const userId = req.user?.id || 'guest';

        try {
            const resume = await ResumeService.getResumeById(resumeId, userId);

            // 检查文件是否存在
            if (!fs.existsSync(resume.filePath)) {
                return res.status(404).json(
                    createErrorResponse(
                        ErrorCodes.NOT_FOUND,
                        '简历文件不存在'
                    )
                );
            }

            // 设置响应头
            res.setHeader('Content-Disposition', `attachment; filename="${encodeURIComponent(resume.originalName)}"`);
            res.setHeader('Content-Type', resume.mimeType);

            // 发送文件
            const fileStream = fs.createReadStream(resume.filePath);
            fileStream.pipe(res);
        } catch (error: any) {
            return res.status(error.statusCode || 500).json(
                createErrorResponse(
                    error.code || ErrorCodes.SERVER_ERROR,
                    error.message || '下载简历文件失败',
                    error.details
                )
            );
        }
    })
];

/**
 * 删除简历
 */
export const deleteResume = [
    validateRequest({
        params: {
            id: {
                type: 'string',
                required: true
            }
        }
    }),

    asyncHandler(async (req: Request, res: Response) => {
        const resumeId = req.params.id;
        const userId = req.user?.id || 'guest';

        try {
            await ResumeService.deleteResume(resumeId, userId);

            return res.json(
                createSuccessResponse({
                    message: '简历已成功删除'
                })
            );
        } catch (error: any) {
            return res.status(error.statusCode || 500).json(
                createErrorResponse(
                    error.code || ErrorCodes.SERVER_ERROR,
                    error.message || '删除简历失败',
                    error.details
                )
            );
        }
    })
]; 