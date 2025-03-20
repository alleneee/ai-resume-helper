import { Request, Response, NextFunction } from 'express';
import { createErrorResponse, ErrorCodes } from '../utils/apiResponse';
import { logger } from '../utils/logger';

// 验证规则类型定义
interface ValidationSchema {
    [key: string]: {
        type: string;
        required?: boolean;
        min?: number;
        max?: number;
        pattern?: RegExp;
        enum?: any[];
        custom?: (value: any) => boolean | { valid: boolean; message: string };
    };
}

// 验证错误格式
interface ValidationErrors {
    [key: string]: string;
}

/**
 * 请求验证中间件
 * 验证请求的参数、查询和请求体是否符合指定的Schema
 */
export function validateRequest(schema: {
    params?: ValidationSchema;
    query?: ValidationSchema;
    body?: ValidationSchema;
}) {
    return (req: Request, res: Response, next: NextFunction) => {
        // 收集所有验证错误
        const errors: ValidationErrors = {};

        // 验证URL参数
        if (schema.params) {
            const paramErrors = validate(req.params, schema.params);
            Object.assign(errors, paramErrors);
        }

        // 验证查询参数
        if (schema.query) {
            const queryErrors = validate(req.query, schema.query);
            Object.assign(errors, queryErrors);
        }

        // 验证请求体
        if (schema.body) {
            const bodyErrors = validate(req.body, schema.body);
            Object.assign(errors, bodyErrors);
        }

        // 如果有任何错误，返回错误响应
        if (Object.keys(errors).length > 0) {
            logger.warn('请求验证失败', {
                method: req.method,
                path: req.path,
                errors
            });

            return res.status(400).json(
                createErrorResponse(
                    ErrorCodes.VALIDATION_ERROR,
                    '请求参数验证失败',
                    errors
                )
            );
        }

        // 验证通过，继续处理请求
        next();
    };
}

/**
 * 验证数据是否符合指定的Schema
 * @param data 要验证的数据
 * @param schema 验证Schema
 * @returns 验证错误集合
 */
function validate(data: any, schema: ValidationSchema): ValidationErrors {
    const errors: ValidationErrors = {};

    // 遍历Schema中的每个字段
    for (const [field, rules] of Object.entries(schema)) {
        const value = data[field];

        // 检查必填字段
        if (rules.required && (value === undefined || value === null || value === '')) {
            errors[field] = `${field} 字段是必填的`;
            continue;
        }

        // 如果字段不存在且不是必填的，跳过后续验证
        if (value === undefined || value === null) {
            continue;
        }

        // 验证类型
        if (rules.type) {
            const typeValid = validateType(value, rules.type);
            if (!typeValid) {
                errors[field] = `${field} 字段类型应为 ${rules.type}`;
                continue;
            }
        }

        // 验证数值范围
        if ((rules.min !== undefined || rules.max !== undefined) &&
            (rules.type === 'number' || (typeof value === 'number'))) {
            // 最小值验证
            if (rules.min !== undefined && value < rules.min) {
                errors[field] = `${field} 不能小于 ${rules.min}`;
                continue;
            }

            // 最大值验证
            if (rules.max !== undefined && value > rules.max) {
                errors[field] = `${field} 不能大于 ${rules.max}`;
                continue;
            }
        }

        // 验证字符串长度
        if ((rules.min !== undefined || rules.max !== undefined) &&
            (rules.type === 'string' || (typeof value === 'string'))) {
            // 最小长度验证
            if (rules.min !== undefined && value.length < rules.min) {
                errors[field] = `${field} 长度不能小于 ${rules.min} 个字符`;
                continue;
            }

            // 最大长度验证
            if (rules.max !== undefined && value.length > rules.max) {
                errors[field] = `${field} 长度不能大于 ${rules.max} 个字符`;
                continue;
            }
        }

        // 正则表达式验证
        if (rules.pattern && rules.type === 'string') {
            if (!rules.pattern.test(String(value))) {
                errors[field] = `${field} 格式不正确`;
                continue;
            }
        }

        // 枚举值验证
        if (rules.enum && rules.enum.length > 0) {
            if (!rules.enum.includes(value)) {
                errors[field] = `${field} 必须是以下值之一: ${rules.enum.join(', ')}`;
                continue;
            }
        }

        // 自定义验证函数
        if (rules.custom) {
            const result = rules.custom(value);

            if (typeof result === 'boolean') {
                if (!result) {
                    errors[field] = `${field} 验证失败`;
                }
            } else if (typeof result === 'object' && !result.valid) {
                errors[field] = result.message || `${field} 验证失败`;
            }
        }
    }

    return errors;
}

/**
 * 验证值的类型是否符合预期
 * @param value 要验证的值
 * @param type 期望的类型
 * @returns 验证结果
 */
function validateType(value: any, type: string): boolean {
    switch (type) {
        case 'string':
            return typeof value === 'string';
        case 'number':
            return !isNaN(Number(value));
        case 'boolean':
            return typeof value === 'boolean' || value === 'true' || value === 'false';
        case 'array':
            return Array.isArray(value);
        case 'object':
            return typeof value === 'object' && !Array.isArray(value) && value !== null;
        default:
            return true; // 未知类型视为有效
    }
}

// 预定义的验证模式
export const ValidationPatterns = {
    email: /^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$/,
    url: /^(https?:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/,
    phone: /^1[3-9]\d{9}$/,
}; 