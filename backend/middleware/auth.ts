import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { createErrorResponse, ErrorCodes } from '../utils/apiResponse';
import { logger } from '../utils/logger';

// 从环境变量中获取JWT密钥
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key-should-be-long-and-secure';

// 定义角色权限级别
const ROLES = {
    GUEST: 0,
    USER: 1,
    PREMIUM: 2,
    ADMIN: 3
};

/**
 * 验证JWT令牌并将用户信息附加到请求对象
 */
export function authenticateToken(req: Request, res: Response, next: NextFunction) {
    // 从请求头获取令牌
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN格式

    // 如果没有令牌，不阻止请求，但不附加用户信息
    if (!token) {
        return next();
    }

    // 验证令牌
    jwt.verify(token, JWT_SECRET, (err: any, decoded: any) => {
        if (err) {
            logger.warn('无效的令牌', { error: err.message });
            return next(); // 令牌无效，但不阻止请求
        }

        // 将用户信息附加到请求
        req.user = decoded;
        next();
    });
}

/**
 * 要求用户必须登录
 */
export function requireAuth(req: Request, res: Response, next: NextFunction) {
    // 验证用户是否已登录
    if (!req.user) {
        return res.status(401).json(
            createErrorResponse(
                ErrorCodes.UNAUTHORIZED,
                '需要登录才能访问此资源'
            )
        );
    }

    next();
}

/**
 * 检查用户是否具有所需角色
 * @param requiredRole 所需的最低角色级别
 */
export function checkRole(requiredRole: keyof typeof ROLES) {
    return (req: Request, res: Response, next: NextFunction) => {
        // 首先确保用户已登录
        if (!req.user) {
            return res.status(401).json(
                createErrorResponse(
                    ErrorCodes.UNAUTHORIZED,
                    '需要登录才能访问此资源'
                )
            );
        }

        // 获取用户角色
        const userRole = req.user.role;
        const userRoleLevel = ROLES[userRole as keyof typeof ROLES] || ROLES.GUEST;
        const requiredRoleLevel = ROLES[requiredRole];

        // 检查用户是否有足够权限
        if (userRoleLevel < requiredRoleLevel) {
            return res.status(403).json(
                createErrorResponse(
                    ErrorCodes.FORBIDDEN,
                    '权限不足，无法访问此资源'
                )
            );
        }

        next();
    };
}

/**
 * 生成JWT令牌
 */
export function generateToken(user: { id: string, email: string, role: string }) {
    // 设置令牌有效期为24小时
    return jwt.sign(user, JWT_SECRET, { expiresIn: '24h' });
}

/**
 * 刷新JWT令牌
 */
export function refreshToken(req: Request, res: Response) {
    // 确保用户已登录
    if (!req.user) {
        return res.status(401).json(
            createErrorResponse(
                ErrorCodes.UNAUTHORIZED,
                '需要登录才能刷新令牌'
            )
        );
    }

    // 生成新令牌
    const newToken = generateToken({
        id: req.user.id,
        email: req.user.email,
        role: req.user.role
    });

    return res.json({
        success: true,
        data: {
            token: newToken,
            expiresIn: 24 * 60 * 60 // 24小时，单位为秒
        }
    });
} 