import React, { useState } from 'react';
import { Form, Input, Button, Card, message } from 'antd';
import { LockKeyhole, Mail, User } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { authApi, ApiResponse } from '../services/api';

const Register: React.FC = () => {
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const onFinish = async (values: { name: string; email: string; password: string; confirm: string }) => {
        try {
            setLoading(true);
            const response = await authApi.register({
                name: values.name,
                email: values.email,
                password: values.password
            });

            const responseData = response as unknown as ApiResponse<any>;

            if (responseData?.status === 'success') {
                message.success('注册成功，请登录');
                navigate('/login');
            } else {
                message.error(responseData?.message || '注册失败，请稍后再试');
            }
        } catch (error: any) {
            message.error(error.response?.data?.message || '注册失败，请稍后再试');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
            <Card className="w-full max-w-md backdrop-blur-xl bg-white/10 border border-gray-700 shadow-2xl">
                <div className="text-center mb-8">
                    <h2 className="text-3xl font-bold text-white">创建账号</h2>
                    <p className="mt-2 text-gray-400">注册智能职位分析与简历优化系统</p>
                </div>

                <Form
                    name="register"
                    initialValues={{ remember: true }}
                    onFinish={onFinish}
                    layout="vertical"
                >
                    <Form.Item
                        name="name"
                        rules={[{ required: true, message: '请输入姓名' }]}
                        label={<span className="text-gray-300">姓名</span>}
                    >
                        <Input
                            prefix={<User className="text-gray-400 mr-2" size={16} />}
                            placeholder="请输入姓名"
                            className="bg-white/5 border-gray-700 text-white"
                        />
                    </Form.Item>

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
                        rules={[
                            { required: true, message: '请输入密码' },
                            { min: 6, message: '密码长度不能少于6个字符' }
                        ]}
                        label={<span className="text-gray-300">密码</span>}
                    >
                        <Input.Password
                            prefix={<LockKeyhole className="text-gray-400 mr-2" size={16} />}
                            placeholder="请输入密码"
                            className="bg-white/5 border-gray-700 text-white"
                        />
                    </Form.Item>

                    <Form.Item
                        name="confirm"
                        dependencies={['password']}
                        rules={[
                            { required: true, message: '请确认密码' },
                            ({ getFieldValue }) => ({
                                validator(_, value) {
                                    if (!value || getFieldValue('password') === value) {
                                        return Promise.resolve();
                                    }
                                    return Promise.reject(new Error('两次输入的密码不一致'));
                                },
                            }),
                        ]}
                        label={<span className="text-gray-300">确认密码</span>}
                    >
                        <Input.Password
                            prefix={<LockKeyhole className="text-gray-400 mr-2" size={16} />}
                            placeholder="请确认密码"
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
                            注册
                        </Button>
                    </Form.Item>

                    <div className="text-center mt-4 text-gray-400">
                        已有账号？
                        <Button
                            type="link"
                            onClick={() => navigate('/login')}
                            className="text-blue-400 hover:text-blue-300 p-0 h-auto"
                        >
                            立即登录
                        </Button>
                    </div>
                </Form>
            </Card>
        </div>
    );
};

export default Register; 