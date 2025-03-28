"use client"

import Link from 'next/link'
import { ResumeDetail } from '../types'

interface ResumeHeaderProps {
    resume: ResumeDetail
    onDelete: () => void
    onReanalyze: () => void
    togglePdfView: () => void
    showPdf: boolean
}

export function ResumeHeader({
    resume,
    onDelete,
    onReanalyze,
    togglePdfView,
    showPdf
}: ResumeHeaderProps) {
    return (
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
            <div>
                <div className="flex items-center gap-2 mb-2">
                    <Link
                        href="/dashboard"
                        className="text-muted-foreground hover:text-foreground transition-colors"
                    >
                        <svg
                            className="h-5 w-5"
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
                            <path d="m15 18-6-6 6-6" />
                        </svg>
                    </Link>
                    <h1 className="text-2xl font-bold truncate max-w-md">{resume.fileName}</h1>
                </div>
                <p className="text-muted-foreground">
                    上传于 {new Date(resume.uploadDate).toLocaleString("zh-CN")}
                </p>
                {resume.status === "pending" && (
                    <div className="flex items-center mt-2 text-yellow-500">
                        <svg
                            className="h-4 w-4 mr-2 animate-spin"
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
                            <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                        </svg>
                        <span>正在处理中...</span>
                    </div>
                )}
            </div>

            <div className="flex gap-3">
                <button
                    className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90 transition-colors"
                    onClick={togglePdfView}
                >
                    {showPdf ? "隐藏预览" : "查看简历"}
                </button>

                {resume.status === "analyzed" && (
                    <button
                        className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/90 transition-colors"
                        onClick={onReanalyze}
                    >
                        重新分析
                    </button>
                )}

                <button
                    className="px-4 py-2 border border-red-500 text-red-500 rounded-md hover:bg-red-50 dark:hover:bg-red-950/20 transition-colors"
                    onClick={onDelete}
                >
                    删除简历
                </button>
            </div>
        </div>
    )
} 