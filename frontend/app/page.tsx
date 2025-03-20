import Link from "next/link"
import Image from "next/image"

export default function Home() {
    return (
        <main className="flex min-h-screen flex-col items-center justify-between p-4 md:p-24">
            <div className="z-10 max-w-5xl w-full flex flex-col items-center justify-center text-center">
                <h1 className="text-4xl font-bold tracking-tight sm:text-6xl mb-6">
                    AI简历助手
                    <span className="text-primary">智能简历分析与优化</span>
                </h1>

                <p className="mt-6 text-lg leading-8 text-muted-foreground max-w-2xl mx-auto">
                    上传您的简历，获取专业分析和优化建议，提升求职竞争力。
                    我们的AI会帮助您识别简历中的优势和不足，并提供针对性的改进建议。
                </p>

                <div className="mt-10 flex items-center justify-center gap-x-6">
                    <Link
                        href="/upload"
                        className="rounded-md bg-primary px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-primary/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                    >
                        上传简历
                    </Link>
                    <Link
                        href="/dashboard"
                        className="text-sm font-semibold leading-6 text-foreground"
                    >
                        查看历史简历 <span aria-hidden="true">→</span>
                    </Link>
                </div>

                <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
                    <div className="flex flex-col items-center p-6 bg-card rounded-lg shadow-sm">
                        <div className="rounded-full bg-primary/10 p-4 mb-4">
                            <svg
                                className="h-6 w-6 text-primary"
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
                                <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
                                <polyline points="14 2 14 8 20 8" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-medium">智能解析</h3>
                        <p className="text-sm text-muted-foreground mt-2 text-center">
                            自动提取简历信息，包括个人信息、教育背景、工作经历和技能等
                        </p>
                    </div>

                    <div className="flex flex-col items-center p-6 bg-card rounded-lg shadow-sm">
                        <div className="rounded-full bg-primary/10 p-4 mb-4">
                            <svg
                                className="h-6 w-6 text-primary"
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
                                <path d="M2 12h20" />
                                <path d="M6 12a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z" />
                                <path d="M18 12a2 2 0 1 0 0 4 2 2 0 0 0 0-4Z" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-medium">深入分析</h3>
                        <p className="text-sm text-muted-foreground mt-2 text-center">
                            AI评估您的简历，提供关于内容、结构和表达方式的详细评价
                        </p>
                    </div>

                    <div className="flex flex-col items-center p-6 bg-card rounded-lg shadow-sm">
                        <div className="rounded-full bg-primary/10 p-4 mb-4">
                            <svg
                                className="h-6 w-6 text-primary"
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
                                <path d="m9 12 2 2 4-4" />
                                <path d="M12 3c-1.2 0-2.4.6-3 1.7A3.6 3.6 0 0 0 4.6 9c-1 .6-1.7 1.8-1.7 3a4 4 0 0 0 4 4h.3" />
                                <path d="M16 19h.9a4 4 0 0 0 3.1-7c-.3-1-1-1.9-2-2.3" />
                                <path d="M12 19v3" />
                                <path d="M8 19v3" />
                                <path d="M16 19v3" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-medium">优化建议</h3>
                        <p className="text-sm text-muted-foreground mt-2 text-center">
                            根据分析结果，提供有针对性的改进建议，帮助您打造出色的简历
                        </p>
                    </div>
                </div>
            </div>
        </main>
    )
} 