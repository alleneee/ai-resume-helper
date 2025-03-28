"use client"

import { useState } from "react"
import Link from "next/link"
import { useResumes, Resume } from "@/hooks/useResumes"
import { toast } from "@/hooks/use-toast"

export default function DashboardPage() {
    const { resumes, isLoading, deleteResume } = useResumes()

    // 处理删除简历
    const handleDelete = (id: string) => {
        if (window.confirm("确定要删除这份简历吗？此操作不可撤销。")) {
            deleteResume(id)
        }
    }

    // 获取状态文本
    const getStatusText = (status: Resume["status"]) => {
        switch (status) {
            case "pending":
                return "处理中"
            case "processed":
                return "已处理"
            case "analyzed":
                return "已分析"
            case "failed":
                return "失败"
            default:
                return "未知"
        }
    }

    // 获取状态颜色
    const getStatusColor = (status: Resume["status"]) => {
        switch (status) {
            case "pending":
                return "text-yellow-500 bg-yellow-50 dark:bg-yellow-900/20"
            case "processed":
                return "text-blue-500 bg-blue-50 dark:bg-blue-900/20"
            case "analyzed":
                return "text-green-500 bg-green-50 dark:bg-green-900/20"
            case "failed":
                return "text-red-500 bg-red-50 dark:bg-red-900/20"
            default:
                return "text-gray-500 bg-gray-50 dark:bg-gray-800"
        }
    }

    return (
        <div className="container mx-auto px-4 py-8 page-transition">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold">我的简历</h1>
                <Link
                    href="/upload"
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                >
                    上传新简历
                </Link>
            </div>

            {isLoading ? (
                <div className="bg-card rounded-lg shadow">
                    <div className="p-4 border-b">
                        <div className="h-6 w-1/3 skeleton"></div>
                    </div>
                    <div className="divide-y">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="p-4 flex items-center justify-between">
                                <div className="flex-1">
                                    <div className="h-5 w-1/3 skeleton mb-2"></div>
                                    <div className="h-4 w-1/4 skeleton"></div>
                                </div>
                                <div className="flex items-center space-x-3">
                                    <div className="h-8 w-20 skeleton"></div>
                                    <div className="h-8 w-20 skeleton"></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            ) : resumes && resumes.length > 0 ? (
                <div className="bg-card rounded-lg shadow">
                    <div className="grid grid-cols-4 gap-4 p-4 font-medium text-muted-foreground border-b">
                        <div className="col-span-2">简历名称</div>
                        <div>状态</div>
                        <div className="text-right">操作</div>
                    </div>
                    <div className="divide-y">
                        {resumes.map((resume) => (
                            <div key={resume.id} className="grid grid-cols-4 gap-4 p-4 items-center">
                                <div className="col-span-2">
                                    <p className="font-medium">{resume.fileName}</p>
                                    <p className="text-sm text-muted-foreground">
                                        上传于 {new Date(resume.uploadDate).toLocaleString("zh-CN")}
                                    </p>
                                </div>
                                <div>
                                    <span
                                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                                            resume.status
                                        )}`}
                                    >
                                        {getStatusText(resume.status)}
                                    </span>
                                    {resume.score && (
                                        <span className="ml-2 text-sm font-medium">
                                            得分: {resume.score}
                                        </span>
                                    )}
                                </div>
                                <div className="flex justify-end space-x-2">
                                    <Link
                                        href={`/resume/${resume.id}`}
                                        className="px-3 py-1.5 bg-secondary text-secondary-foreground rounded hover:bg-secondary/80 transition-colors text-sm"
                                    >
                                        查看
                                    </Link>
                                    <button
                                        onClick={() => handleDelete(resume.id)}
                                        className="px-3 py-1.5 border border-destructive text-destructive rounded hover:bg-destructive/10 transition-colors text-sm"
                                    >
                                        删除
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            ) : (
                <div className="bg-card rounded-lg shadow-sm p-12 text-center">
                    <div className="flex justify-center mb-4">
                        <svg
                            className="h-16 w-16 text-muted-foreground"
                            fill="none"
                            height="24"
                            stroke="currentColor"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                            viewBox="0 0 24 24"
                            width="24"
                            xmlns="http://www.w3.org/2000/svg"
                        >
                            <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
                            <path d="M13 2v7h7" />
                        </svg>
                    </div>
                    <h3 className="text-xl font-medium mb-2">没有找到简历</h3>
                    <p className="text-muted-foreground mb-6">
                        您还没有上传任何简历，点击"上传新简历"按钮开始使用AI简历助手
                    </p>
                    <Link
                        href="/upload"
                        className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                    >
                        上传新简历
                    </Link>
                </div>
            )}
        </div>
    )
} 