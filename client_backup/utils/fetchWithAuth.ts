/**
 * 带认证的API请求工具函数
 * 自动处理认证头部和刷新token逻辑
 */

// API基础URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

// 请求选项类型
type RequestOptions = RequestInit & {
    isFormData?: boolean;
};

/**
 * 从localStorage获取token
 */
const getToken = (): string | null => {
    if (typeof window === 'undefined') return null;

    return localStorage.getItem('token');
};

/**
 * 带认证的API请求函数
 * @param endpoint API端点
 * @param options 请求选项
 * @returns 请求结果
 */
export const fetchWithAuth = async <T = any>(
    endpoint: string,
    options: RequestOptions = {}
): Promise<T> => {
    const token = getToken();
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;

    // 构建请求选项
    const headers: HeadersInit = {};

    // 如果有token则添加Authorization请求头
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // 如果不是FormData则设置Content-Type为application/json
    if (!options.isFormData && !options.body?.toString().includes('FormData')) {
        headers['Content-Type'] = 'application/json';
    }

    // 合并请求头
    const requestOptions: RequestInit = {
        ...options,
        headers: {
            ...headers,
            ...options.headers
        }
    };

    try {
        const response = await fetch(url, requestOptions);

        // 检查是否是401错误（未授权）
        if (response.status === 401) {
            // 尝试刷新token或重定向到登录页面
            if (typeof window !== 'undefined') {
                // 清理本地存储的token
                localStorage.removeItem('token');

                // 重定向到登录页面
                window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
                return Promise.reject('未授权，请重新登录');
            }
        }

        // 解析响应JSON
        const data = await response.json();

        // 返回API响应
        return data;
    } catch (error) {
        console.error('API请求失败:', error);
        throw error;
    }
};

export default fetchWithAuth; 