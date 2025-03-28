'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Form, Input, Button, Typography, Card, Divider, message, Checkbox } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, GoogleOutlined } from '@ant-design/icons';
import Link from 'next/link';
import { useAuthContext } from '@/contexts/AuthContext';

const { Title, Paragraph, Text } = Typography;

interface RegisterFormValues {
    name: string;
    email: string;
    password: string;
    confirmPassword: string;
    agreeToTerms: boolean;
}

export default function RegisterPage() {
    const router = useRouter();
    const { register } = useAuthContext();
    const [loading, setLoading] = useState(false);

    const onFinish = async (values: RegisterFormValues) => {
        if (values.password !== values.confirmPassword) {
            message.error('两次输入的密码不一致');
            return;
        }

        setLoading(true);
        try {
            await register(values.name, values.email, values.password);
            message.success('注册成功');
            router.push('/agent');
        } catch (error: any) {
            message.error(error?.message || '注册失败，请重试');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-[calc(100vh-120px)] flex items-center justify-center p-4">
            <Card className="w-full max-w-md shadow-md rounded-lg">
                <div className="text-center mb-6">
                    <Title level={2}>创建账户</Title>
                    <Paragraph type="secondary">
                        注册以使用AI简历助手，提升您的求职竞争力
                    </Paragraph>
                </div>

                <Form
                    name="register"
                    initialValues={{ agreeToTerms: false }}
                    onFinish={onFinish}
                    layout="vertical"
                    size="large"
                >
                    <Form.Item
                        name="name"
                        label="姓名"
                        rules={[{ required: true, message: '请输入您的姓名' }]}
                    >
                        <Input
                            prefix={<UserOutlined className="text-gray-400" />}
                            placeholder="您的姓名"
                        />
                    </Form.Item>

                    <Form.Item
                        name="email"
                        label="电子邮箱"
                        rules={[
                            { required: true, message: '请输入您的电子邮箱' },
                            { type: 'email', message: '请输入有效的电子邮箱地址' }
                        ]}
                    >
                        <Input
                            prefix={<MailOutlined className="text-gray-400" />}
                            placeholder="your@email.com"
                        />
                    </Form.Item>

                    <Form.Item
                        name="password"
                        label="密码"
                        rules={[
                            { required: true, message: '请输入密码' },
                            { min: 8, message: '密码长度至少为8个字符' }
                        ]}
                    >
                        <Input.Password
                            prefix={<LockOutlined className="text-gray-400" />}
                            placeholder="密码（至少8个字符）"
                        />
                    </Form.Item>

                    <Form.Item
                        name="confirmPassword"
                        label="确认密码"
                        rules={[
                            { required: true, message: '请确认您的密码' },
                            ({ getFieldValue }) => ({
                                validator(_, value) {
                                    if (!value || getFieldValue('password') === value) {
                                        return Promise.resolve();
                                    }
                                    return Promise.reject(new Error('两次输入的密码不一致'));
                                },
                            }),
                        ]}
                    >
                        <Input.Password
                            prefix={<LockOutlined className="text-gray-400" />}
                            placeholder="再次输入密码"
                        />
                    </Form.Item>

                    <Form.Item
                        name="agreeToTerms"
                        valuePropName="checked"
                        rules={[
                            {
                                validator: (_, value) =>
                                    value
                                        ? Promise.resolve()
                                        : Promise.reject(new Error('请阅读并同意服务条款和隐私政策')),
                            },
                        ]}
                    >
                        <Checkbox>
                            我已阅读并同意 <Link href="/terms" className="text-blue-500 hover:text-blue-600">服务条款</Link> 和
                            <Link href="/privacy" className="text-blue-500 hover:text-blue-600"> 隐私政策</Link>
                        </Checkbox>
                    </Form.Item>

                    <Form.Item>
                        <Button
                            type="primary"
                            htmlType="submit"
                            className="w-full"
                            loading={loading}
                        >
                            注册
                        </Button>
                    </Form.Item>
                </Form>

                <Divider plain>或者</Divider>

                <Button
                    icon={<GoogleOutlined />}
                    block
                    className="mb-4 flex items-center justify-center"
                >
                    使用Google账号注册
                </Button>

                <div className="text-center mt-4">
                    <Text type="secondary">
                        已有账号? <Link href="/login" className="text-blue-500 hover:text-blue-600">登录</Link>
                    </Text>
                </div>
            </Card>
        </div>
    );
} 