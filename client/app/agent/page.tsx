'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { toast } from 'react-hot-toast';
import { Button, Input, Select, Card, Tabs, Table, Tag, Spin, Empty, Divider } from 'antd';
import { SearchOutlined, FileTextOutlined, SyncOutlined, RocketOutlined } from '@ant-design/icons';
import ResumeSelector from '@/components/resume/ResumeSelector';
import JobCard from '@/components/job/JobCard';
import JobMatchDetails from '@/components/job/JobMatchDetails';
import { useAuthContext } from '@/contexts/AuthContext';
import { fetchWithAuth } from '@/utils/fetchWithAuth';

// 定义Job类型接口
interface Job {
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
    url?: string;
}

// 定义分析结果接口
interface AnalysisResult {
    matchScore: number;
    strengths: string[];
    weaknesses: string[];
    missingSkills: string[];
}

// 定义优化改进项接口
interface Improvement {
    type: 'add' | 'modify' | 'delete';
    original?: string;
    optimized?: string;
    reason: string;
}

// 定义优化结果接口
interface OptimizationResult {
    summary: string;
    improvements: {
        [section: string]: Improvement[];
    };
    prioritizedActions: string[];
}

// 定义完整的优化响应接口
interface OptimizationResponse {
    analysisResult: AnalysisResult;
    optimizationResult: OptimizationResult;
}

const AgentPage = () => {
    const router = useRouter();
    const { user } = useAuthContext();
    const searchParams = useSearchParams();

    // 状态
    const [activeTab, setActiveTab] = useState('search');
    const [jobTitle, setJobTitle] = useState('');
    const [location, setLocation] = useState('');
    const [selectedResumeId, setSelectedResumeId] = useState('');
    const [loading, setLoading] = useState(false);
    const [jobs, setJobs] = useState<Job[]>([]);
    const [selectedJob, setSelectedJob] = useState<Job | null>(null);
    const [optimizationResult, setOptimizationResult] = useState<OptimizationResponse | null>(null);
    const [optimizationLoading, setOptimizationLoading] = useState(false);

    // 从URL获取参数
    useEffect(() => {
        const title = searchParams.get('jobTitle');
        const loc = searchParams.get('location');
        if (title) setJobTitle(title);
        if (loc) setLocation(loc);
    }, [searchParams]);

    // 搜索职位方法
    const searchJobs = async () => {
        if (!jobTitle.trim()) {
            toast.error('请输入职位名称');
            return;
        }

        setLoading(true);
        try {
            const response = await fetchWithAuth(`/api/agent/jobs?jobTitle=${encodeURIComponent(jobTitle)}&location=${encodeURIComponent(location || '')}`);

            if (response.success) {
                setJobs(response.data);
                if (response.data.length === 0) {
                    toast.error('未找到匹配的职位');
                }
            } else {
                toast.error(response.message || '搜索职位失败');
            }
        } catch (error) {
            console.error('搜索职位出错:', error);
            toast.error('搜索职位失败，请稍后再试');
        } finally {
            setLoading(false);
        }
    };

    // 获取职位详情方法
    const getJobDetails = async (jobId: string) => {
        setLoading(true);
        try {
            const response = await fetchWithAuth(`/api/agent/jobs/${jobId}`);

            if (response.success) {
                setSelectedJob(response.data);
            } else {
                toast.error(response.message || '获取职位详情失败');
            }
        } catch (error) {
            console.error('获取职位详情出错:', error);
            toast.error('获取职位详情失败，请稍后再试');
        } finally {
            setLoading(false);
        }
    };

    // 优化简历方法
    const optimizeResume = async () => {
        if (!selectedResumeId) {
            toast.error('请选择一个简历');
            return;
        }

        if (!selectedJob) {
            toast.error('请先选择一个职位');
            return;
        }

        setOptimizationLoading(true);
        try {
            const response = await fetchWithAuth('/api/agent/optimize-resume', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    resumeId: selectedResumeId,
                    jobTitle: selectedJob.title,
                    location: selectedJob.location || location,
                }),
            });

            if (response.success) {
                setOptimizationResult(response.data);
                toast.success('简历优化成功');
                setActiveTab('optimization');
            } else {
                toast.error(response.message || '简历优化失败');
            }
        } catch (error) {
            console.error('简历优化出错:', error);
            toast.error('简历优化失败，请稍后再试');
        } finally {
            setOptimizationLoading(false);
        }
    };

    // 分析简历与职位匹配度方法
    const analyzeResume = async () => {
        if (!selectedResumeId) {
            toast.error('请选择一个简历');
            return;
        }

        if (!selectedJob) {
            toast.error('请先选择一个职位');
            return;
        }

        setOptimizationLoading(true);
        try {
            const response = await fetchWithAuth('/api/agent/analyze-resume', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    resumeId: selectedResumeId,
                    jobId: selectedJob.job_id,
                }),
            });

            if (response.success) {
                setOptimizationResult(response.data);
                toast.success('简历分析成功');
                setActiveTab('optimization');
            } else {
                toast.error(response.message || '简历分析失败');
            }
        } catch (error) {
            console.error('简历分析出错:', error);
            toast.error('简历分析失败，请稍后再试');
        } finally {
            setOptimizationLoading(false);
        }
    };

    // 渲染函数
    const renderJobList = () => {
        if (loading) {
            return <div className="flex justify-center my-8"><Spin size="large" /></div>;
        }

        if (jobs.length === 0) {
            return (
                <Empty
                    description="暂无职位数据"
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    className="my-8"
                />
            );
        }

        return (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-4">
                {jobs.map((job) => (
                    <JobCard
                        key={job.job_id}
                        job={job}
                        isSelected={selectedJob ? selectedJob.job_id === job.job_id : false}
                        onClick={() => getJobDetails(job.job_id)}
                    />
                ))}
            </div>
        );
    };

    const renderOptimizationResult = () => {
        if (!optimizationResult) {
            return (
                <Empty
                    description="请先进行简历优化"
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    className="my-8"
                />
            );
        }

        const { analysisResult, optimizationResult: optimResult } = optimizationResult;

        return (
            <div className="space-y-6 my-4">
                <Card title="匹配度分析" className="shadow-md">
                    <div className="flex items-center mb-4">
                        <div className="text-3xl font-bold text-blue-600">{analysisResult.matchScore}/100</div>
                        <div className="ml-4">
                            <div className="text-gray-600">与目标职位的匹配程度</div>
                        </div>
                    </div>

                    <Divider />

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                        <div>
                            <h3 className="text-lg font-semibold text-green-600 mb-2">优势</h3>
                            <ul className="list-disc list-inside space-y-1">
                                {analysisResult.strengths.map((item, index) => (
                                    <li key={index}>{item}</li>
                                ))}
                            </ul>
                        </div>

                        <div>
                            <h3 className="text-lg font-semibold text-red-600 mb-2">不足</h3>
                            <ul className="list-disc list-inside space-y-1">
                                {analysisResult.weaknesses.map((item, index) => (
                                    <li key={index}>{item}</li>
                                ))}
                            </ul>
                        </div>
                    </div>

                    <div className="mt-4">
                        <h3 className="text-lg font-semibold text-orange-600 mb-2">缺失的关键技能</h3>
                        <div className="flex flex-wrap gap-2">
                            {analysisResult.missingSkills.map((skill, index) => (
                                <Tag key={index} color="orange">{skill}</Tag>
                            ))}
                        </div>
                    </div>
                </Card>

                <Card title="改进建议" className="shadow-md">
                    <div className="mb-4">
                        <h3 className="text-lg font-semibold mb-2">整体建议</h3>
                        <p>{optimResult.summary}</p>
                    </div>

                    <Divider />

                    <Tabs defaultActiveKey="experience">
                        {Object.entries(optimResult.improvements).map(([section, improvements]) => (
                            <Tabs.TabPane tab={getTabName(section)} key={section}>
                                <ul className="space-y-4">
                                    {improvements.map((improvement, index) => (
                                        <li key={index} className="border-l-4 border-blue-500 pl-4 pb-2">
                                            <div className="font-semibold">{improvement.type === 'add' ? '建议添加' : (improvement.type === 'modify' ? '建议修改' : '建议删除')}</div>
                                            {improvement.original && (
                                                <div className="mt-1 p-2 bg-gray-100 rounded">
                                                    <div className="text-sm text-gray-500">原内容:</div>
                                                    <div>{improvement.original}</div>
                                                </div>
                                            )}
                                            {improvement.optimized && (
                                                <div className="mt-2 p-2 bg-green-50 rounded">
                                                    <div className="text-sm text-green-600">优化内容:</div>
                                                    <div>{improvement.optimized}</div>
                                                </div>
                                            )}
                                            <div className="mt-2 text-sm text-gray-600">
                                                <span className="font-semibold">原因:</span> {improvement.reason}
                                            </div>
                                        </li>
                                    ))}
                                </ul>
                            </Tabs.TabPane>
                        ))}
                    </Tabs>
                </Card>

                <Card title="优先行动" className="shadow-md">
                    <ul className="list-decimal list-inside space-y-2">
                        {optimResult.prioritizedActions.map((action, index) => (
                            <li key={index} className="text-blue-600">{action}</li>
                        ))}
                    </ul>
                </Card>
            </div>
        );
    };

    // 辅助函数
    const getTabName = (section: string): string => {
        const nameMap: Record<string, string> = {
            contactInfo: '联系信息',
            experience: '工作经验',
            skills: '技能',
            education: '教育背景',
            projects: '项目经验'
        };
        return nameMap[section] || section;
    };

    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-2xl font-bold mb-6">AI简历优化助手</h1>

            <Card className="mb-6 shadow-md">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="col-span-1 md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 mb-1">选择简历</label>
                        <ResumeSelector
                            value={selectedResumeId}
                            onChange={setSelectedResumeId}
                        />
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">职位名称</label>
                        <Input
                            placeholder="例如: 前端工程师"
                            value={jobTitle}
                            onChange={(e) => setJobTitle(e.target.value)}
                            prefix={<FileTextOutlined />}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">地点</label>
                        <Input
                            placeholder="例如: 北京"
                            value={location}
                            onChange={(e) => setLocation(e.target.value)}
                            prefix={<SearchOutlined />}
                        />
                    </div>
                    <div className="flex items-end">
                        <Button
                            type="primary"
                            icon={<SearchOutlined />}
                            onClick={searchJobs}
                            loading={loading}
                            className="w-full"
                        >
                            搜索职位
                        </Button>
                    </div>
                </div>
            </Card>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-1">
                    <Card title="职位列表" className="shadow-md">
                        {renderJobList()}
                    </Card>
                </div>

                <div className="lg:col-span-2">
                    <Tabs activeKey={activeTab} onChange={setActiveTab}>
                        <Tabs.TabPane tab="职位详情" key="details">
                            {selectedJob ? (
                                <JobMatchDetails job={selectedJob} />
                            ) : (
                                <Empty
                                    description="请选择一个职位查看详情"
                                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                                    className="my-8"
                                />
                            )}

                            {selectedJob && selectedResumeId && (
                                <div className="flex gap-4 mt-6">
                                    <Button
                                        type="primary"
                                        icon={<SyncOutlined />}
                                        onClick={analyzeResume}
                                        loading={optimizationLoading}
                                    >
                                        分析匹配度
                                    </Button>

                                    <Button
                                        type="primary"
                                        icon={<RocketOutlined />}
                                        onClick={optimizeResume}
                                        loading={optimizationLoading}
                                    >
                                        优化简历
                                    </Button>
                                </div>
                            )}
                        </Tabs.TabPane>

                        <Tabs.TabPane tab="优化结果" key="optimization">
                            {renderOptimizationResult()}
                        </Tabs.TabPane>
                    </Tabs>
                </div>
            </div>
        </div>
    );
};

export default AgentPage; 