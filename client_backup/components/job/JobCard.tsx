'use client';

import React from 'react';
import { Card, Tag, Tooltip } from 'antd';
import { BuildOutlined, EnvironmentOutlined, DollarOutlined, ReadOutlined } from '@ant-design/icons';

interface JobCardProps {
    job: {
        job_id: string;
        title: string;
        company: string;
        salary_range?: string;
        experience_requirement?: string;
        education_requirement?: string;
        skills_required?: string[];
        location?: string;
    };
    isSelected?: boolean;
    onClick?: () => void;
}

const JobCard: React.FC<JobCardProps> = ({ job, isSelected = false, onClick }) => {
    return (
        <Card
            hoverable
            className={`job-card ${isSelected ? 'border-blue-500 border-2' : ''}`}
            onClick={onClick}
        >
            <div className="flex justify-between items-start">
                <div>
                    <h3 className="text-lg font-bold text-blue-700">{job.title}</h3>
                    <p className="text-gray-700 font-medium">{job.company}</p>
                </div>
                {job.salary_range && (
                    <div className="text-green-600 font-semibold flex items-center">
                        <DollarOutlined className="mr-1" /> {job.salary_range}
                    </div>
                )}
            </div>

            <div className="flex flex-wrap gap-2 mt-3">
                {job.location && (
                    <Tag icon={<EnvironmentOutlined />} color="blue">
                        {job.location}
                    </Tag>
                )}

                {job.experience_requirement && (
                    <Tag icon={<BuildOutlined />} color="purple">
                        {job.experience_requirement}
                    </Tag>
                )}

                {job.education_requirement && (
                    <Tag icon={<ReadOutlined />} color="cyan">
                        {job.education_requirement}
                    </Tag>
                )}
            </div>

            {job.skills_required && job.skills_required.length > 0 && (
                <div className="mt-3">
                    <div className="text-xs text-gray-500 mb-1">技能要求</div>
                    <div className="flex flex-wrap gap-1">
                        {job.skills_required.slice(0, 5).map((skill, index) => (
                            <Tag key={index} className="text-xs">{skill}</Tag>
                        ))}
                        {job.skills_required.length > 5 && (
                            <Tooltip title={job.skills_required.slice(5).join(', ')}>
                                <Tag className="text-xs">+{job.skills_required.length - 5}</Tag>
                            </Tooltip>
                        )}
                    </div>
                </div>
            )}
        </Card>
    );
};

export default JobCard; 