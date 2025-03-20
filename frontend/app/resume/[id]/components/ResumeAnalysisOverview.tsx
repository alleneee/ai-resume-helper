"use client"

import { ResumeAnalysis } from '../types'

interface ResumeAnalysisOverviewProps {
    analysis: ResumeAnalysis;
    renderScoreBar: (score: number) => React.ReactNode;
}

export function ResumeAnalysisOverview({
    analysis,
    renderScoreBar
}: ResumeAnalysisOverviewProps) {
    return (
        <div className="flex flex-col md:flex-row justify-between gap-6 mb-8">
            <div className="flex-1">
                <h3 className="text-lg font-medium mb-4">总体评分</h3>
                <div className="flex items-center mb-6">
                    <div className="w-24 h-24 rounded-full border-4 flex items-center justify-center mr-4 relative">
                        <svg viewBox="0 0 36 36" className="w-full h-full">
                            <path
                                className="stroke-current text-muted"
                                fill="none"
                                strokeWidth="4"
                                strokeLinecap="round"
                                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            ></path>
                            <path
                                className={`stroke-current ${analysis.overallScore >= 80
                                        ? "text-green-500"
                                        : analysis.overallScore >= 60
                                            ? "text-yellow-500"
                                            : "text-red-500"
                                    }`}
                                fill="none"
                                strokeWidth="4"
                                strokeLinecap="round"
                                strokeDasharray={`${analysis.overallScore}, 100`}
                                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            ></path>
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center">
                            <span className="text-xl font-bold">{analysis.overallScore}</span>
                        </div>
                    </div>
                    <div>
                        <p className="text-lg font-medium">
                            {analysis.overallScore >= 80
                                ? "优秀"
                                : analysis.overallScore >= 60
                                    ? "良好"
                                    : "需改进"}
                        </p>
                        <p className="text-muted-foreground">
                            {analysis.overallScore >= 80
                                ? "您的简历已经达到很高水平，仍有少量改进空间"
                                : analysis.overallScore >= 60
                                    ? "您的简历基本合格，但有明显改进空间"
                                    : "您的简历需要重大改进才能有效吸引招聘者"}
                        </p>
                    </div>
                </div>

                <div className="space-y-3">
                    {analysis.sections.map((section, index) => (
                        <div key={index}>
                            <div className="flex justify-between items-center mb-1">
                                <span className="text-sm font-medium">{section.name}</span>
                                <span className="text-sm text-muted-foreground">{section.score}/100</span>
                            </div>
                            {renderScoreBar(section.score)}
                        </div>
                    ))}
                </div>
            </div>

            <div className="flex-1">
                <div className="mb-6">
                    <h3 className="text-lg font-medium mb-4">简历优势</h3>
                    <ul className="space-y-2">
                        {analysis.strengths.map((strength, index) => (
                            <li key={index} className="flex items-start">
                                <svg
                                    className="h-5 w-5 text-green-500 mr-2 mt-0.5 flex-shrink-0"
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
                                    <polyline points="20 6 9 17 4 12" />
                                </svg>
                                <span>{strength}</span>
                            </li>
                        ))}
                    </ul>
                </div>

                <div>
                    <h3 className="text-lg font-medium mb-4">需要改进</h3>
                    <ul className="space-y-2">
                        {analysis.weaknesses.map((weakness, index) => (
                            <li key={index} className="flex items-start">
                                <svg
                                    className="h-5 w-5 text-red-500 mr-2 mt-0.5 flex-shrink-0"
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
                                    <path d="M18 6 6 18" />
                                    <path d="m6 6 12 12" />
                                </svg>
                                <span>{weakness}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            </div>
        </div>
    );
} 