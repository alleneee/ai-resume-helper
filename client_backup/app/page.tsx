'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Button, Card, Typography, Row, Col, Statistic, Steps, List } from 'antd';
import {
    RocketOutlined,
    SearchOutlined,
    UploadOutlined,
    RobotOutlined,
    CheckCircleOutlined,
    FileTextOutlined,
} from '@ant-design/icons';
import { useAuthContext } from '@/contexts/AuthContext';

const { Title, Paragraph, Text } = Typography;
const { Step } = Steps;

export default function Home() {
    const { isAuthenticated } = useAuthContext();
    const [currentStep, setCurrentStep] = useState(0);

    const features = [
        {
            icon: <FileTextOutlined style={{ fontSize: '24px', color: '#1890ff' }} />,
            title: '智能简历解析',
            description: '自动解析您的简历内容，提取关键信息和技能',
        },
        {
            icon: <SearchOutlined style={{ fontSize: '24px', color: '#52c41a' }} />,
            title: '职位匹配分析',
            description: '分析简历与目标职位的匹配度，找出优势与不足',
        },
        {
            icon: <RobotOutlined style={{ fontSize: '24px', color: '#722ed1' }} />,
            title: 'AI驱动优化',
            description: '基于GPT的智能建议，针对性优化简历内容',
        },
        {
            icon: <CheckCircleOutlined style={{ fontSize: '24px', color: '#fa8c16' }} />,
            title: '简历优先排序',
            description: '提高您的简历在招聘系统中的排名，增加面试机会',
        },
    ];

    const steps = [
        {
            title: '上传简历',
            description: '上传您的PDF或Word格式简历',
            icon: <UploadOutlined />,
        },
        {
            title: '搜索职位',
            description: '输入目标职位名称和地点',
            icon: <SearchOutlined />,
        },
        {
            title: '分析匹配度',
            description: '查看简历与职位的匹配情况',
            icon: <RobotOutlined />,
        },
        {
            title: '获取优化建议',
            description: '应用AI推荐的简历优化建议',
            icon: <RocketOutlined />,
        },
    ];

    return (
        <>
            {/* 首页横幅 */}
            <div className="bg-gradient-to-r from-blue-500 to-indigo-600 py-16 text-white">
                <div className="container mx-auto px-4 text-center">
                    <Title level={1} className="text-white mb-6">
                        让AI助你成为面试率最高的候选人
                    </Title>
                    <Paragraph className="text-lg mb-8 text-white opacity-90">
                        智能分析简历与职位匹配度，获取个性化优化建议
                    </Paragraph>
                    <div className="flex justify-center gap-4">
                        <Button
                            type="primary"
                            size="large"
                            className="bg-white text-blue-600 border-white hover:bg-gray-100 hover:border-gray-100 hover:text-blue-700"
                            icon={<RocketOutlined />}
                            href={isAuthenticated ? '/agent' : '/register'}
                        >
                            {isAuthenticated ? '开始使用' : '免费注册'}
                        </Button>
                        <Button
                            size="large"
                            ghost
                            href="#how-it-works"
                            className="border-white text-white hover:text-white hover:border-gray-100 hover:opacity-80"
                        >
                            了解更多
                        </Button>
                    </div>
                </div>
            </div>

            {/* 统计数据 */}
            <div className="py-16 bg-gray-50">
                <div className="container mx-auto px-4">
                    <Row gutter={[24, 24]} justify="center">
                        <Col xs={12} sm={6}>
                            <Card className="text-center h-full shadow-sm">
                                <Statistic
                                    title="简历通过率提升"
                                    value={85}
                                    suffix="%"
                                    valueStyle={{ color: '#3f8600' }}
                                />
                            </Card>
                        </Col>
                        <Col xs={12} sm={6}>
                            <Card className="text-center h-full shadow-sm">
                                <Statistic
                                    title="面试邀请增长"
                                    value={67}
                                    suffix="%"
                                    valueStyle={{ color: '#3f8600' }}
                                />
                            </Card>
                        </Col>
                        <Col xs={12} sm={6}>
                            <Card className="text-center h-full shadow-sm">
                                <Statistic title="已优化简历数" value={10283} />
                            </Card>
                        </Col>
                        <Col xs={12} sm={6}>
                            <Card className="text-center h-full shadow-sm">
                                <Statistic title="平均匹配度提升" value={43} suffix="分" />
                            </Card>
                        </Col>
                    </Row>
                </div>
            </div>

            {/* 特点介绍 */}
            <div className="py-16">
                <div className="container mx-auto px-4">
                    <Title level={2} className="text-center mb-12">
                        为什么选择我们的AI简历助手？
                    </Title>
                    <Row gutter={[24, 24]}>
                        {features.map((feature, index) => (
                            <Col key={index} xs={24} sm={12} lg={6}>
                                <Card
                                    hoverable
                                    className="h-full text-center flex flex-col shadow-sm"
                                >
                                    <div className="flex justify-center mb-4">{feature.icon}</div>
                                    <Title level={4}>{feature.title}</Title>
                                    <Paragraph className="text-gray-600 flex-grow">
                                        {feature.description}
                                    </Paragraph>
                                </Card>
                            </Col>
                        ))}
                    </Row>
                </div>
            </div>

            {/* 使用步骤 */}
            <div id="how-it-works" className="py-16 bg-gray-50">
                <div className="container mx-auto px-4">
                    <Title level={2} className="text-center mb-12">
                        如何使用
                    </Title>
                    <Steps
                        current={currentStep}
                        onChange={setCurrentStep}
                        className="max-w-3xl mx-auto"
                        responsive
                    >
                        {steps.map((step) => (
                            <Step
                                key={step.title}
                                title={step.title}
                                description={step.description}
                                icon={step.icon}
                            />
                        ))}
                    </Steps>
                    <div className="mt-12 text-center">
                        <Button
                            type="primary"
                            size="large"
                            icon={<RocketOutlined />}
                            href={isAuthenticated ? '/agent' : '/login'}
                        >
                            {isAuthenticated ? '立即开始' : '登录使用'}
                        </Button>
                    </div>
                </div>
            </div>

            {/* CTA部分 */}
            <div className="py-16 bg-blue-50">
                <div className="container mx-auto px-4 text-center">
                    <Title level={2} className="mb-4">
                        准备好提升您的求职效率了吗？
                    </Title>
                    <Paragraph className="text-lg mb-8 max-w-2xl mx-auto">
                        加入我们的平台，利用AI技术优化您的简历，增加获得理想工作的机会。
                    </Paragraph>
                    <Button
                        type="primary"
                        size="large"
                        icon={<RocketOutlined />}
                        href={isAuthenticated ? '/agent' : '/register'}
                    >
                        {isAuthenticated ? '开始使用' : '立即注册'}
                    </Button>
                </div>
            </div>
        </>
    );
} 