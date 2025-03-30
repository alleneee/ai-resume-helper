import axios from 'axios';

// Placeholder types - Ideally, define these in a separate types file (e.g., src/types/resume.ts)
// based on your backend Pydantic models
interface ResumeData {
    raw_text: string;
    parsed_sections?: Record<string, any>; // Adjust as per your model
}

interface JobSearchCriteria {
    keywords: string[];
    location?: string;
    limit?: number;
    other_filters?: Record<string, any>; // Adjust as per your model
}

export interface OptimizedResume {
    optimized_text: string;
    original_resume?: ResumeData;
    analysis_summary?: any; // Adjust based on AnalysisResult model
    // Add other fields from your OptimizedResume Pydantic model
}

// API响应类型
export interface ApiResponse<T = any> {
    success: boolean;
    message: string;
    data: T;
    request_id?: string;
    errors?: any[];
    timestamp?: string;
}

// 创建axios实例
const api = axios.create({
    baseURL: '/api',
    timeout: 60000,
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
        // Add a unique request ID for tracing (optional but good practice)
        // config.headers['X-Request-ID'] = generateUUID(); 
        return config;
    },
    (error) => {
        console.error("Request interceptor error:", error);
        return Promise.reject(error);
    }
);

// 响应拦截器
api.interceptors.response.use(
    (response) => {
        // 直接返回 AxiosResponse，让调用者处理
        return response;
    },
    (error): Promise<any> => { // 错误处理可以保持，或者简化为只 reject error
        console.error("Response interceptor error:", error.response || error.message);
        if (error.response && error.response.status === 401) {
            console.log("Unauthorized access. Redirecting to login.");
            localStorage.removeItem('token');
            window.location.href = '/login';
            // 返回一个更明确的错误
            return Promise.reject(new Error('Unauthorized'));
        }
        // 返回原始错误或者包含更多信息的错误对象
        const errorData = error.response?.data || { message: error.message };
        return Promise.reject(errorData);
    }
);

// 简历相关API
export const resumeApi = {
    // 获取简历列表
    getResumes: async (page = 1, limit = 10): Promise<ApiResponse<any>> => {
        const response = await api.get<ApiResponse>(`/resumes?page=${page}&limit=${limit}`);
        return response.data; // 在函数内部提取 .data
    },

    // 获取简历详情
    getResume: async (id: string): Promise<ApiResponse<any>> => {
        const response = await api.get<ApiResponse>(`/resumes/${id}`);
        return response.data;
    },

    // 上传简历
    uploadResume: async (formData: FormData): Promise<ApiResponse<any>> => {
        const response = await api.post<ApiResponse>('/resumes/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    // 优化简历
    optimizeResume: (resumeId: string, jobDescription: string, options = {}) => {
        return api.post<ApiResponse>('/agent/optimize-resume', {
            resume_id: resumeId,
            job_description: jobDescription,
            options,
        });
    },

    // 优化简历
    optimizeResumeApi: async (
        resumeData: ResumeData,
        searchCriteria: JobSearchCriteria
    ): Promise<ApiResponse<OptimizedResume>> => {
        const requestBody = {
            resume_data: resumeData,
            search_criteria: searchCriteria,
        };
        const response = await api.post<ApiResponse<OptimizedResume>>('/resumes/optimize', requestBody);
        return response.data;
    },

    // 删除简历
    deleteResume: async (id: string): Promise<ApiResponse<any>> => {
        const response = await api.delete<ApiResponse>(`/resumes/${id}`);
        return response.data;
    },
};

// 职位相关API
export const jobApi = {
    // 搜索职位
    searchJobs: async (data: any): Promise<ApiResponse<any>> => {
        const response = await api.post<ApiResponse>('/agent/search-jobs', data);
        return response.data;
    },

    // 获取职位详情
    getJobDetail: async (id: string): Promise<ApiResponse<any>> => {
        const response = await api.get<ApiResponse>(`/agent/job/${id}`);
        return response.data;
    },

    // 职位匹配
    matchJobs: async (resumeId: string, filters = {}): Promise<ApiResponse<any>> => {
        const response = await api.post<ApiResponse>('/agent/match-jobs', {
            resume_id: resumeId,
            filters,
        });
        return response.data;
    },

    // 分析简历与职位匹配度
    analyzeResume: async (resumeId: string, jobId: string): Promise<ApiResponse<any>> => {
        const response = await api.post<ApiResponse>('/agent/analyze-resume', {
            resume_id: resumeId,
            job_id: jobId,
        });
        return response.data;
    },
};

// 用户认证API
export const authApi = {
    // 用户登录
    login: async (email: string, password: string): Promise<ApiResponse<any>> => {
        const response = await api.post<ApiResponse>('/auth/login', { email, password });
        return response.data;
    },

    // 用户注册
    register: async (userData: any): Promise<ApiResponse<any>> => {
        const response = await api.post<ApiResponse>('/auth/register', userData);
        return response.data;
    },

    // 获取当前用户信息
    getCurrentUser: async (): Promise<ApiResponse<any>> => {
        const response = await api.get<ApiResponse>('/auth/me');
        return response.data;
    },

    // 退出登录
    logout: async (): Promise<ApiResponse<any>> => {
        const response = await api.post<ApiResponse>('/auth/logout');
        return response.data;
    },
};

export default api; 