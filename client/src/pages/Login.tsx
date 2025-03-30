import React, { useState } from 'react';
import { Form, Input, Button, Card, message } from 'antd';
import { LockKeyhole, Mail } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { authApi, ApiResponse } from '../services/api';

// 定义认证响应数据类型
interface AuthData {
    token: string;
    user?: any;
}

const Login: React.FC = () => {
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const onFinish = async (values: { email: string; password: string }) => {
        try {
            setLoading(true);
            const response = await authApi.login(values.email, values.password);
            const responseData = response as unknown as ApiResponse<AuthData>;

            if (responseData?.success === true && responseData.data?.token) {
                localStorage.setItem('token', responseData.data.token);
                message.success('登录成功');
                navigate('/');
            } else {
                message.error(responseData?.message || '登录失败，请检查邮箱和密码');
            }
        } catch (error: any) {
            console.error('登录错误:', error);
            message.error(error.response?.data?.message || '登录失败，请检查邮箱和密码');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
            <Card className="w-full max-w-md backdrop-blur-xl bg-white/10 border border-gray-700 shadow-2xl">
                <div className="text-center mb-8">
                    <h2 className="text-3xl font-bold text-white">欢迎登录</h2>
                    <p className="mt-2 text-gray-400">智能职位分析与简历优化系统</p>
                </div>

                <Form
                    name="login"
                    initialValues={{ remember: true }}
                    onFinish={onFinish}
                    layout="vertical"
                >
                    <Form.Item
                        name="email"
                        rules={[
                            { required: true, message: '请输入邮箱' },
                            { type: 'email', message: '请输入有效的邮箱地址' }
                        ]}
                        label={<span className="text-gray-300">邮箱</span>}
                    >
                        <Input
                            prefix={<Mail className="text-gray-400 mr-2" size={16} />}
                            placeholder="请输入邮箱"
                            className="bg-white/5 border-gray-700 text-white"
                        />
                    </Form.Item>

                    <Form.Item
                        name="password"
                        rules={[{ required: true, message: '请输入密码' }]}
                        label={<span className="text-gray-300">密码</span>}
                    >
                        <Input.Password
                            prefix={<LockKeyhole className="text-gray-400 mr-2" size={16} />}
                            placeholder="请输入密码"
                            className="bg-white/5 border-gray-700 text-white"
                        />
                    </Form.Item>

                    <Form.Item className="mt-6">
                        <Button
                            type="primary"
                            htmlType="submit"
                            className="w-full h-auto py-2 flex items-center justify-center bg-gradient-to-r from-blue-500 to-blue-600"
                            loading={loading}
                        >
                            登录
                        </Button>
                    </Form.Item>

                    <div className="text-center mt-4 text-gray-400">
                        还没有账号？
                        <Button
                            type="link"
                            onClick={() => navigate('/register')}
                            className="text-blue-400 hover:text-blue-300 p-0 h-auto"
                        >
                            立即注册
                        </Button>
                    </div>
                </Form>
            </Card>
        </div>
    );
};

export default Login; 