import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { config } from '../config/app';
import { logger } from '../utils/logger';
import { ApiResponse } from '../utils/apiResponse';
import User, { IUser } from '../models/User';

/**
 * JWT载荷接口
 */
interface JwtPayload {
    id: string;
    email: string;
}

/**
 * 扩展Express Request接口，添加user属性
 */
declare global {
    namespace Express {
        interface Request {
            user?: IUser & { _id: any };
        }
    }
}

/**
 * 用户认证中间件
 * 验证JWT令牌并将用户信息附加到请求对象
 */
export const authMiddleware = async (req: Request, res: Response, next: NextFunction) => {
    try {
        // 获取请求头中的Authorization字段
        const authHeader = req.headers.authorization;

        // 检查Authorization头是否存在
        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return ApiResponse.unauthorized(res, '未提供访问令牌或格式错误');
        }

        // 提取Token
        const token = authHeader.split(' ')[1];

        // 验证Token
        const decoded = jwt.verify(token, config.jwt.secret) as JwtPayload;

        // 从数据库获取用户信息
        const user = await User.findById(decoded.id).select('-password');

        // 检查用户是否存在
        if (!user) {
            return ApiResponse.unauthorized(res, '用户不存在或已被删除');
        }

        // 将用户信息附加到请求对象
        req.user = user;

        // 继续下一个中间件或路由处理器
        next();
    } catch (error: any) {
        logger.error('认证失败', { error: error.message });

        if (error.name === 'TokenExpiredError') {
            return ApiResponse.unauthorized(res, '访问令牌已过期，请重新登录');
        }

        if (error.name === 'JsonWebTokenError') {
            return ApiResponse.unauthorized(res, '无效的访问令牌');
        }

        return ApiResponse.unauthorized(res, '认证失败');
    }
}; 