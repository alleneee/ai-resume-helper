'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { toast } from 'react-hot-toast';
import { fetchWithAuth } from '@/utils/fetchWithAuth';

// 用户类型
interface User {
    _id: string;
    email: string;
    name?: string;
    role: 'user' | 'admin';
}

// 认证上下文类型
interface AuthContextType {
    user: User | null;
    loading: boolean;
    login: (email: string, password: string) => Promise<boolean>;
    register: (email: string, password: string, name: string) => Promise<boolean>;
    logout: () => void;
    isAuthenticated: boolean;
}

// 创建认证上下文
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// 认证上下文提供者
export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState<boolean>(true);

    // 初始化时检查认证状态
    useEffect(() => {
        const checkAuthStatus = async () => {
            try {
                // 检查是否有token
                const token = localStorage.getItem('token');
                if (!token) {
                    setLoading(false);
                    return;
                }

                // 获取当前用户信息
                const response = await fetchWithAuth('/api/auth/me');

                if (response.success) {
                    setUser(response.data);
                } else {
                    // 如果获取用户信息失败，清除token
                    localStorage.removeItem('token');
                }
            } catch (error) {
                console.error('认证检查失败:', error);
                // 出错时清除token
                localStorage.removeItem('token');
            } finally {
                setLoading(false);
            }
        };

        checkAuthStatus();
    }, []);

    // 登录
    const login = async (email: string, password: string): Promise<boolean> => {
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'}/api/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (data.success) {
                localStorage.setItem('token', data.data.token);
                setUser(data.data.user);
                toast.success('登录成功');
                return true;
            } else {
                toast.error(data.message || '登录失败');
                return false;
            }
        } catch (error) {
            console.error('登录请求失败:', error);
            toast.error('登录请求失败，请稍后再试');
            return false;
        }
    };

    // 注册
    const register = async (email: string, password: string, name: string): Promise<boolean> => {
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'}/api/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password, name })
            });

            const data = await response.json();

            if (data.success) {
                localStorage.setItem('token', data.data.token);
                setUser(data.data.user);
                toast.success('注册成功');
                return true;
            } else {
                toast.error(data.message || '注册失败');
                return false;
            }
        } catch (error) {
            console.error('注册请求失败:', error);
            toast.error('注册请求失败，请稍后再试');
            return false;
        }
    };

    // 登出
    const logout = () => {
        localStorage.removeItem('token');
        setUser(null);
        toast.success('已退出登录');
    };

    // 计算是否已认证
    const isAuthenticated = !!user;

    // 提供上下文
    const value = {
        user,
        loading,
        login,
        register,
        logout,
        isAuthenticated
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// 自定义hook，用于在组件中访问上下文
export const useAuthContext = (): AuthContextType => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuthContext必须在AuthProvider内部使用');
    }
    return context;
}; 