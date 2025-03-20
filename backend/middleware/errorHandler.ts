import { Request, Response, NextFunction } from 'express';
import { createErrorResponse, ErrorCodes } from '../utils/apiResponse';
import { logger } from '../utils/logger';

export interface AppError extends Error {
    statusCode?: number;
    code?: string;
    details?: any;
    isOperational?: boolean;
}

/**
 * 自定义错误类，用于应用程序中抛出操作性错误
 */
export class ApplicationError extends Error implements AppError {
    statusCode: number;
    code: string;
    details?: any;
    isOperational: boolean;

    constructor(code: string, message: string, statusCode: number = 400, details?: any) {
        super(message);
        this.statusCode = statusCode;
        this.code = code;
        this.details = details;
        this.isOperational = true; // 这是一个可控制的业务错误

        // 设置原型链，以便错误实例正确地被instanceof检测
        Object.setPrototypeOf(this, ApplicationError.prototype);
    }
}

/**
 * 捕获异步路由处理器中的错误
 */
export const asyncHandler = (fn: Function) =>
    (req: Request, res: Response, next: NextFunction): Promise<void> => {
        Promise.resolve(fn(req, res, next)).catch(next);
    };

/**
 * 处理404错误（未找到路由）
 */
export const notFoundHandler = (req: Request, res: Response, next: NextFunction): void => {
    const error = new ApplicationError(
        ErrorCodes.NOT_FOUND,
        `未找到路径: ${req.originalUrl}`,
        404
    );
    next(error);
};

/**
 * 全局错误处理中间件
 */
export const errorHandler = (
    err: AppError,
    req: Request,
    res: Response,
    next: NextFunction // eslint-disable-line @typescript-eslint/no-unused-vars
): void => {
    // 设置默认状态码和错误代码
    const statusCode = err.statusCode || 500;
    const errorCode = err.code || ErrorCodes.SERVER_ERROR;

    // 记录错误
    if (statusCode >= 500) {
        logger.error('服务器错误', {
            path: req.path,
            method: req.method,
            error: err.message,
            stack: err.stack
        });
    } else {
        logger.warn('客户端错误', {
            path: req.path,
            method: req.method,
            error: err.message,
            code: errorCode,
            details: err.details
        });
    }

    // 发送适当的响应
    res.status(statusCode).json(
        createErrorResponse(
            errorCode,
            err.message,
            process.env.NODE_ENV === 'development' ? err.details || err.stack : err.details
        )
    );
};

/**
 * 未捕获异常处理
 */
export const setupUncaughtExceptionHandling = (): void => {
    // 处理未捕获的异常
    process.on('uncaughtException', (error: Error) => {
        logger.error('未捕获的异常', { error: error.message, stack: error.stack });
        console.error('未捕获的异常:', error);

        // 给应用程序一些时间来完成待处理的请求并关闭资源
        setTimeout(() => {
            console.error('应用程序正在关闭...');
            process.exit(1);
        }, 1000);
    });

    // 处理未处理的Promise拒绝
    process.on('unhandledRejection', (reason: any, promise: Promise<any>) => {
        logger.error('未处理的Promise拒绝', { reason, promise });
        console.error('未处理的Promise拒绝:', reason);

        // 将未处理的拒绝转换为未捕获的异常
        throw reason;
    });
}; 