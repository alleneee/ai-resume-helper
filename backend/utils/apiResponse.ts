export interface ApiResponse<T> {
    success: boolean;
    data?: T;
    error?: {
        code: string;
        message: string;
        details?: any;
    };
    meta?: {
        version: string;
        timestamp: number;
        pagination?: {
            page: number;
            limit: number;
            total: number;
            totalPages: number;
        };
    };
}

export function createSuccessResponse<T>(data: T, meta?: Partial<ApiResponse<T>['meta']>): ApiResponse<T> {
    return {
        success: true,
        data,
        meta: {
            version: '1.0',
            timestamp: Date.now(),
            ...meta
        }
    };
}

export function createErrorResponse(
    code: string,
    message: string,
    details?: any
): ApiResponse<never> {
    return {
        success: false,
        error: {
            code,
            message,
            details
        },
        meta: {
            version: '1.0',
            timestamp: Date.now()
        }
    };
}

// 错误代码常量
export const ErrorCodes = {
    BAD_REQUEST: 'BAD_REQUEST',
    UNAUTHORIZED: 'UNAUTHORIZED',
    FORBIDDEN: 'FORBIDDEN',
    NOT_FOUND: 'NOT_FOUND',
    VALIDATION_ERROR: 'VALIDATION_ERROR',
    SERVER_ERROR: 'SERVER_ERROR',
    SERVICE_UNAVAILABLE: 'SERVICE_UNAVAILABLE',
    RESUME_NOT_FOUND: 'RESUME_NOT_FOUND',
    RESUME_UPLOAD_FAILED: 'RESUME_UPLOAD_FAILED',
    RESUME_PARSING_FAILED: 'RESUME_PARSING_FAILED',
    RESUME_ANALYSIS_FAILED: 'RESUME_ANALYSIS_FAILED',
    FILE_TOO_LARGE: 'FILE_TOO_LARGE',
    UNSUPPORTED_FILE_TYPE: 'UNSUPPORTED_FILE_TYPE',
    SUBSCRIPTION_REQUIRED: 'SUBSCRIPTION_REQUIRED',
    QUOTA_EXCEEDED: 'QUOTA_EXCEEDED'
}; 