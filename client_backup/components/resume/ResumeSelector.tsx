'use client';

import { useState, useEffect } from 'react';
import { Select, Spin } from 'antd';
import { toast } from 'react-hot-toast';
import { fetchWithAuth } from '@/utils/fetchWithAuth';

interface ResumeSelectorProps {
    value?: string;
    onChange?: (value: string) => void;
    placeholder?: string;
    disabled?: boolean;
}

interface Resume {
    _id: string;
    title: string;
    fileName: string;
    status: string;
}

const ResumeSelector: React.FC<ResumeSelectorProps> = ({
    value,
    onChange,
    placeholder = '选择简历',
    disabled = false
}) => {
    const [resumes, setResumes] = useState<Resume[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchResumes();
    }, []);

    const fetchResumes = async () => {
        setLoading(true);
        try {
            const response = await fetchWithAuth('/api/resume');

            if (response.success) {
                setResumes(response.data);

                // 如果没有选中的简历但有简历列表，自动选择第一个
                if (!value && response.data.length > 0 && onChange) {
                    onChange(response.data[0]._id);
                }
            } else {
                toast.error('获取简历列表失败');
            }
        } catch (error) {
            console.error('获取简历列表出错:', error);
            toast.error('获取简历列表失败，请稍后再试');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Select
            className="w-full"
            value={value}
            onChange={onChange}
            placeholder={placeholder}
            disabled={disabled || loading}
            showSearch
            optionFilterProp="label"
            notFoundContent={loading ? <Spin size="small" /> : '暂无简历'}
            options={resumes.map(resume => ({
                label: resume.title || resume.fileName,
                value: resume._id
            }))}
        />
    );
};

export default ResumeSelector; 