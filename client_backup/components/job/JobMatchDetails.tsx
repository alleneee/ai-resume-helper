'use client';

import React from 'react';
import { Card, Divider, Tag, Typography, Space } from 'antd';
import {
    BankOutlined,
    DollarOutlined,
    ClockCircleOutlined,
    BookOutlined,
    TagsOutlined,
    ApartmentOutlined
} from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;

interface JobMatchDetailsProps {
    job: {
        job_id: string;
        title: string;
        company: string;
        salary_range?: string;
        experience_requirement?: string;
        education_requirement?: string;
        job_description?: string;
        skills_required?: string[];
        tags?: string[];
        location?: string;
    };
}

const JobMatchDetails: React.FC<JobMatchDetailsProps> = ({ job }) => {
    // 格式化职位描述，处理换行
    const formatDescription = (description?: string) => {
        if (!description) return null;

        return description.split('\n').map((line, i) => (
            <Paragraph key={i}>
                {line.trim() ? line : <br />}
            </Paragraph>
        ));
    };

    return (
        <Card className="shadow-md">
            <div className="mb-6">
                <Title level={3} className="text-blue-700 mb-1">{job.title}</Title>
                <Space className="mb-4">
                    <Text className="flex items-center">
                        <BankOutlined className="mr-1" /> {job.company}
                    </Text>
                    {job.location && (
                        <Text className="flex items-center">
                            <ApartmentOutlined className="mr-1" /> {job.location}
                        </Text>
                    )}
                    {job.salary_range && (
                        <Text className="text-green-600 flex items-center">
                            <DollarOutlined className="mr-1" /> {job.salary_range}
                        </Text>
                    )}
                </Space>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                {job.experience_requirement && (
                    <div className="flex items-center">
                        <ClockCircleOutlined className="text-purple-600 mr-2" />
                        <span className="text-gray-700">
                            经验要求: <span className="font-medium">{job.experience_requirement}</span>
                        </span>
                    </div>
                )}

                {job.education_requirement && (
                    <div className="flex items-center">
                        <BookOutlined className="text-blue-600 mr-2" />
                        <span className="text-gray-700">
                            学历要求: <span className="font-medium">{job.education_requirement}</span>
                        </span>
                    </div>
                )}
            </div>

            {job.tags && job.tags.length > 0 && (
                <div className="mb-4">
                    <div className="flex items-center mb-2">
                        <TagsOutlined className="text-gray-600 mr-2" />
                        <Text strong>标签</Text>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {job.tags.map((tag, index) => (
                            <Tag key={index}>{tag}</Tag>
                        ))}
                    </div>
                </div>
            )}

            {job.skills_required && job.skills_required.length > 0 && (
                <div className="mb-4">
                    <div className="flex items-center mb-2">
                        <TagsOutlined className="text-blue-600 mr-2" />
                        <Text strong>技能要求</Text>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {job.skills_required.map((skill, index) => (
                            <Tag key={index} color="blue">{skill}</Tag>
                        ))}
                    </div>
                </div>
            )}

            {job.job_description && (
                <>
                    <Divider orientation="left">职位描述</Divider>
                    <div className="text-gray-700">{formatDescription(job.job_description)}</div>
                </>
            )}
        </Card>
    );
};

export default JobMatchDetails; 