"use client"

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { LoadingState, ErrorState } from './components/ResumeStates'
import { useToast } from '@/hooks/use-toast'
import { cn } from '@/lib/utils'

interface ResumeDetailProps {
    id: string
}

interface ResumeDetail {
    id: string
    fileName: string
    originalName: string
    uploadDate: string
    status: string
    score?: number
    analysis?: {
        skills: Array<{
            name: string
            level?: string
            category?: string
            relevance?: number
        }>
        experience: Array<{
            title: string
            company: string
            startDate: string
            endDate?: string
            description: string
            highlights: string[]
        }>
        education: Array<{
            institution: string
            degree: string
            field: string
            startDate: string
            endDate?: string
            gpa?: number
        }>
        summary?: string
        strengths?: string[]
        weaknesses?: string[]
        recommendations?: string[]
        keywords?: string[]
        scoreDetails?: {
            relevanceScore: number
            completenessScore: number
            formattingScore: number
            languageScore: number
            overallScore: number
        }
    }
}

export default function ResumeDetailClient({ id }: ResumeDetailProps) {
    const router = useRouter()
    const { toast } = useToast()
    const [resume, setResume] = useState<ResumeDetail | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [activeTab, setActiveTab] = useState<'overview' | 'analysis' | 'suggestions'>('overview')

    useEffect(() => {
        const fetchResumeDetail = async () => {
            try {
                setLoading(true)
                const response = await fetch(`/api/resume/${id}`)

                if (!response.ok) {
                    throw new Error('简历获取失败')
                }

                const data = await response.json()
                setResume(data.data)
                setLoading(false)
            } catch (err: any) {
                setError(err.message || '发生错误，无法加载简历详情')
                setLoading(false)
                toast({
                    title: '加载失败',
                    description: '无法加载简历详情，请稍后重试',
                    variant: 'destructive'
                })
            }
        }

        fetchResumeDetail()
    }, [id, toast])

    const handleDelete = async () => {
        if (!window.confirm('确定要删除这份简历吗？此操作无法撤销。')) {
            return
        }

        try {
            const response = await fetch(`/api/resume/${id}`, {
                method: 'DELETE'
            })

            if (!response.ok) {
                throw new Error('删除失败')
            }

            toast({
                title: '删除成功',
                description: '简历已成功删除'
            })

            router.push('/dashboard')
        } catch (err) {
            toast({
                title: '操作失败',
                description: '无法删除简历，请稍后重试',
                variant: 'destructive'
            })
        }
    }

    if (loading) {
        return <LoadingState />
    }

    if (error || !resume) {
        return <ErrorState message={error || '无法加载简历详情'} />
    }

    const getScoreColor = (score?: number) => {
        if (!score) return 'text-gray-500'
        if (score >= 80) return 'text-green-500'
        if (score >= 60) return 'text-yellow-500'
        return 'text-red-500'
    }

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'uploaded':
                return <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300">已上传</span>
            case 'processing':
                return <span className="px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300">处理中</span>
            case 'analyzed':
                return <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300">已分析</span>
            case 'failed':
                return <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300">处理失败</span>
            default:
                return <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">{status}</span>
        }
    }

    return (
        <div className="container mx-auto px-4 py-8 max-w-6xl page-transition">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
                <div>
                    <h1 className="text-2xl font-bold">{resume.originalName}</h1>
                    <p className="text-sm text-muted-foreground">
                        上传于 {new Date(resume.uploadDate).toLocaleString('zh-CN')} {getStatusBadge(resume.status)}
                    </p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={() => router.push(`/resume/${id}/download`)}
                        className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
                    >
                        下载
                    </button>
                    <button
                        onClick={handleDelete}
                        className="px-4 py-2 bg-destructive text-destructive-foreground rounded hover:bg-destructive/90"
                    >
                        删除
                    </button>
                </div>
            </div>

            <div className="bg-card rounded-lg shadow-sm mb-8">
                <div className="border-b border-border">
                    <div className="flex">
                        <button
                            onClick={() => setActiveTab('overview')}
                            className={cn(
                                "px-4 py-3 border-b-2 font-medium",
                                activeTab === 'overview'
                                    ? "border-primary text-primary"
                                    : "border-transparent hover:text-primary/80 hover:border-primary/30"
                            )}
                        >
                            概览
                        </button>
                        <button
                            onClick={() => setActiveTab('analysis')}
                            className={cn(
                                "px-4 py-3 border-b-2 font-medium",
                                activeTab === 'analysis'
                                    ? "border-primary text-primary"
                                    : "border-transparent hover:text-primary/80 hover:border-primary/30"
                            )}
                        >
                            详细分析
                        </button>
                        <button
                            onClick={() => setActiveTab('suggestions')}
                            className={cn(
                                "px-4 py-3 border-b-2 font-medium",
                                activeTab === 'suggestions'
                                    ? "border-primary text-primary"
                                    : "border-transparent hover:text-primary/80 hover:border-primary/30"
                            )}
                        >
                            改进建议
                        </button>
                    </div>
                </div>

                <div className="p-6">
                    {activeTab === 'overview' && (
                        <div className="flex flex-col md:flex-row justify-between gap-6">
                            <div className="flex-1">
                                <h2 className="text-xl font-semibold mb-4">简历总结</h2>
                                {resume.analysis?.summary ? (
                                    <p className="text-sm mb-6 leading-relaxed">{resume.analysis.summary}</p>
                                ) : (
                                    <p className="text-sm text-muted-foreground italic">暂无总结信息</p>
                                )}

                                {resume.analysis?.scoreDetails && (
                                    <div className="space-y-3">
                                        <h3 className="text-lg font-medium mb-2">评分详情</h3>
                                        <div>
                                            <div className="flex justify-between items-center mb-1">
                                                <span className="text-sm">相关性</span>
                                                <span className="text-sm">{resume.analysis.scoreDetails.relevanceScore}/100</span>
                                            </div>
                                            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden dark:bg-gray-700">
                                                <div className="bg-primary h-full" style={{ width: `${resume.analysis.scoreDetails.relevanceScore}%` }}></div>
                                            </div>
                                        </div>
                                        <div>
                                            <div className="flex justify-between items-center mb-1">
                                                <span className="text-sm">完整性</span>
                                                <span className="text-sm">{resume.analysis.scoreDetails.completenessScore}/100</span>
                                            </div>
                                            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden dark:bg-gray-700">
                                                <div className="bg-primary h-full" style={{ width: `${resume.analysis.scoreDetails.completenessScore}%` }}></div>
                                            </div>
                                        </div>
                                        <div>
                                            <div className="flex justify-between items-center mb-1">
                                                <span className="text-sm">格式</span>
                                                <span className="text-sm">{resume.analysis.scoreDetails.formattingScore}/100</span>
                                            </div>
                                            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden dark:bg-gray-700">
                                                <div className="bg-primary h-full" style={{ width: `${resume.analysis.scoreDetails.formattingScore}%` }}></div>
                                            </div>
                                        </div>
                                        <div>
                                            <div className="flex justify-between items-center mb-1">
                                                <span className="text-sm">语言表达</span>
                                                <span className="text-sm">{resume.analysis.scoreDetails.languageScore}/100</span>
                                            </div>
                                            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden dark:bg-gray-700">
                                                <div className="bg-primary h-full" style={{ width: `${resume.analysis.scoreDetails.languageScore}%` }}></div>
                                            </div>
                                        </div>
                                        <div className="mt-4">
                                            <div className="flex justify-between items-center mb-1">
                                                <span className="font-medium">总体评分</span>
                                                <span className={cn("font-bold text-lg", getScoreColor(resume.score))}>
                                                    {resume.score || resume.analysis.scoreDetails.overallScore || '无评分'}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className="flex-1">
                                <h2 className="text-xl font-semibold mb-4">优势</h2>
                                {resume.analysis?.strengths && resume.analysis.strengths.length > 0 ? (
                                    <ul className="list-disc list-inside space-y-2 mb-6">
                                        {resume.analysis.strengths.map((strength, index) => (
                                            <li key={index} className="text-sm">{strength}</li>
                                        ))}
                                    </ul>
                                ) : (
                                    <p className="text-sm text-muted-foreground italic mb-6">暂无优势信息</p>
                                )}

                                <h2 className="text-xl font-semibold mb-4">不足</h2>
                                {resume.analysis?.weaknesses && resume.analysis.weaknesses.length > 0 ? (
                                    <ul className="list-disc list-inside space-y-2">
                                        {resume.analysis.weaknesses.map((weakness, index) => (
                                            <li key={index} className="text-sm">{weakness}</li>
                                        ))}
                                    </ul>
                                ) : (
                                    <p className="text-sm text-muted-foreground italic">暂无不足信息</p>
                                )}
                            </div>
                        </div>
                    )}

                    {activeTab === 'analysis' && (
                        <div>
                            {resume.analysis ? (
                                <div className="space-y-8">
                                    <div>
                                        <h2 className="text-xl font-semibold mb-4">技能分析</h2>
                                        {resume.analysis.skills && resume.analysis.skills.length > 0 ? (
                                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                                {resume.analysis.skills.map((skill, index) => (
                                                    <div key={index} className="p-3 border rounded-lg">
                                                        <div className="font-medium">{skill.name}</div>
                                                        {skill.level && <div className="text-sm text-muted-foreground">水平: {skill.level}</div>}
                                                        {skill.category && <div className="text-sm text-muted-foreground">类别: {skill.category}</div>}
                                                        {skill.relevance !== undefined && (
                                                            <div className="mt-2">
                                                                <div className="text-xs text-muted-foreground mb-1">相关性: {skill.relevance}%</div>
                                                                <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden dark:bg-gray-700">
                                                                    <div className="bg-primary h-full" style={{ width: `${skill.relevance}%` }}></div>
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <p className="text-sm text-muted-foreground italic">暂无技能分析</p>
                                        )}
                                    </div>

                                    <div>
                                        <h2 className="text-xl font-semibold mb-4">工作经历分析</h2>
                                        {resume.analysis.experience && resume.analysis.experience.length > 0 ? (
                                            <div className="space-y-4">
                                                {resume.analysis.experience.map((exp, index) => (
                                                    <div key={index} className="p-4 border rounded-lg">
                                                        <div className="flex flex-col md:flex-row md:justify-between md:items-center mb-2">
                                                            <div className="font-medium text-lg">{exp.title}</div>
                                                            <div className="text-sm text-muted-foreground">
                                                                {new Date(exp.startDate).toLocaleDateString('zh-CN')} -
                                                                {exp.endDate ? new Date(exp.endDate).toLocaleDateString('zh-CN') : '至今'}
                                                            </div>
                                                        </div>
                                                        <div className="text-muted-foreground mb-3">{exp.company}</div>
                                                        <div className="text-sm mb-3">{exp.description}</div>
                                                        {exp.highlights && exp.highlights.length > 0 && (
                                                            <div>
                                                                <div className="font-medium text-sm mb-1">亮点:</div>
                                                                <ul className="list-disc list-inside text-sm space-y-1">
                                                                    {exp.highlights.map((highlight, idx) => (
                                                                        <li key={idx}>{highlight}</li>
                                                                    ))}
                                                                </ul>
                                                            </div>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <p className="text-sm text-muted-foreground italic">暂无工作经历分析</p>
                                        )}
                                    </div>

                                    <div>
                                        <h2 className="text-xl font-semibold mb-4">教育背景分析</h2>
                                        {resume.analysis.education && resume.analysis.education.length > 0 ? (
                                            <div className="space-y-4">
                                                {resume.analysis.education.map((edu, index) => (
                                                    <div key={index} className="p-4 border rounded-lg">
                                                        <div className="flex flex-col md:flex-row md:justify-between md:items-center mb-2">
                                                            <div className="font-medium text-lg">{edu.institution}</div>
                                                            <div className="text-sm text-muted-foreground">
                                                                {new Date(edu.startDate).toLocaleDateString('zh-CN')} -
                                                                {edu.endDate ? new Date(edu.endDate).toLocaleDateString('zh-CN') : '至今'}
                                                            </div>
                                                        </div>
                                                        <div className="text-muted-foreground mb-2">{edu.degree} - {edu.field}</div>
                                                        {edu.gpa && <div className="text-sm">GPA: {edu.gpa}</div>}
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <p className="text-sm text-muted-foreground italic">暂无教育背景分析</p>
                                        )}
                                    </div>

                                    {resume.analysis.keywords && resume.analysis.keywords.length > 0 && (
                                        <div>
                                            <h2 className="text-xl font-semibold mb-4">关键词分析</h2>
                                            <div className="flex flex-wrap gap-2">
                                                {resume.analysis.keywords.map((keyword, index) => (
                                                    <span key={index} className="px-3 py-1 bg-background border rounded-full text-sm">
                                                        {keyword}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="text-center py-10">
                                    <p className="text-muted-foreground">简历尚未分析或分析失败</p>
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'suggestions' && (
                        <div>
                            <h2 className="text-xl font-semibold mb-6">改进建议</h2>
                            {resume.analysis?.recommendations && resume.analysis.recommendations.length > 0 ? (
                                <div className="space-y-4">
                                    {resume.analysis.recommendations.map((recommendation, index) => (
                                        <div key={index} className="p-4 border-l-4 border-primary bg-primary/5 rounded-r-lg">
                                            <p className="text-sm">{recommendation}</p>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-sm text-muted-foreground italic">暂无改进建议</p>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
} 