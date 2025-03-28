import axios from 'axios';

// API响应类型
export interface ApiResponse<T = any> {
    status: string;
    message: string;
    data: T;
    request_id?: string;
    errors?: any[];
}

// 创建axios实例
const api = axios.create({
    baseURL: '/api',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    }
});

// 请求拦截器
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// 响应拦截器
api.interceptors.response.use(
    (response) => {
        return response.data;
    },
    (error) => {
        if (error.response && error.response.status === 401) {
            // 未授权，清除token并跳转到登录页
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// 简历相关API
export const resumeApi = {
    // 获取简历列表
    getResumes: (page = 1, limit = 10) => {
        return api.get<ApiResponse>(`/resumes?page=${page}&limit=${limit}`);
    },

    // 获取简历详情
    getResume: (id: string) => {
        return api.get<ApiResponse>(`/resumes/${id}`);
    },

    // 上传简历
    uploadResume: (formData: FormData) => {
        return api.post<ApiResponse>('/resumes/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },

    // 优化简历
    optimizeResume: (resumeId: string, jobDescription: string, options = {}) => {
        return api.post<ApiResponse>('/agent/optimize-resume', {
            resume_id: resumeId,
            job_description: jobDescription,
            options,
        });
    },

    // 删除简历
    deleteResume: (id: string) => {
        return api.delete<ApiResponse>(`/resumes/${id}`);
    },
};

// 职位相关API
export const jobApi = {
    // 搜索职位
    searchJobs: (data: any) => {
        return api.post<ApiResponse>('/agent/search-jobs', data);
    },

    // 获取职位详情
    getJobDetail: (id: string) => {
        return api.get<ApiResponse>(`/agent/job/${id}`);
    },

    // 职位匹配
    matchJobs: (resumeId: string, filters = {}) => {
        return api.post<ApiResponse>('/agent/match-jobs', {
            resume_id: resumeId,
            filters,
        });
    },

    // 分析简历与职位匹配度
    analyzeResume: (resumeId: string, jobId: string) => {
        return api.post<ApiResponse>('/agent/analyze-resume', {
            resume_id: resumeId,
            job_id: jobId,
        });
    },
};

// 用户认证API
export const authApi = {
    // 用户登录
    login: (email: string, password: string) => {
        return api.post<ApiResponse>('/auth/login', { email, password });
    },

    // 用户注册
    register: (userData: any) => {
        return api.post<ApiResponse>('/auth/register', userData);
    },

    // 获取当前用户信息
    getCurrentUser: () => {
        return api.get<ApiResponse>('/auth/me');
    },

    // 退出登录
    logout: () => {
        return api.post<ApiResponse>('/auth/logout');
    },
};

export default api; 