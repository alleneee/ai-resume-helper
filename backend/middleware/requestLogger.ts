import { Request, Response, NextFunction } from 'express';
import { logger } from '../utils/logger';

/**
 * 请求日志记录中间件
 * 记录每个请求的详细信息和处理时间
 */
export function requestLogger(req: Request, res: Response, next: NextFunction) {
    // 记录请求开始时间
    req.startTime = Date.now();

    // 获取原始的 res.end 方法，以便在请求完成时拦截
    const originalEnd = res.end;

    // 覆盖 res.end 方法
    res.end = function (chunk?: any, encoding?: BufferEncoding | undefined): Response {
        // 计算请求处理时间
        const responseTime = Date.now() - (req.startTime || 0);

        // 恢复原始的 end 方法并应用
        res.end = originalEnd;
        res.end(chunk, encoding);

        // 记录请求详情
        logger.logRequest(req, res, responseTime);

        return res;
    };

    next();
}

/**
 * 请求计时中间件
 * 仅记录请求的处理时间，比完整的日志记录更轻量
 */
export function requestTimer(req: Request, res: Response, next: NextFunction) {
    // 记录请求开始时间
    const startTime = Date.now();

    // 请求完成时的处理
    res.on('finish', () => {
        const responseTime = Date.now() - startTime;

        // 如果响应时间超过阈值，记录为警告
        if (responseTime > 1000) { // 1秒阈值
            logger.warn(`慢请求: ${req.method} ${req.path}`, {
                responseTime: `${responseTime}ms`,
                method: req.method,
                path: req.path
            });
        }
    });

    next();
}