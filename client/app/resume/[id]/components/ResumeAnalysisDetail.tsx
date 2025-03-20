"use client"

import { ResumeAnalysis } from '../types'

interface ResumeAnalysisDetailProps {
    analysis: ResumeAnalysis
    renderScoreBar: (score: number) => React.ReactNode
}

export function ResumeAnalysisDetail({
    analysis,
    renderScoreBar
}: ResumeAnalysisDetailProps) {
    return (
        <div>
            {analysis.sections.map((section, index) => (
                <div key={index} className="mb-6 pb-6 border-b last:border-b-0 last:mb-0 last:pb-0">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-lg font-medium">{section.name}</h3>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${section.score >= 80
                            ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300"
                            : section.score >= 60
                                ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300"
                                : "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300"
                            }`}>
                            {section.score}/100
                        </span>
                    </div>

                    <p className="text-muted-foreground mb-3">{section.feedback}</p>

                    {renderScoreBar(section.score)}
                </div>
            ))}
        </div>
    )
} 