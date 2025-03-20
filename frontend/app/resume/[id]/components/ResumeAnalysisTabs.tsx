"use client"

import { ResumeAnalysis } from '../types'
import { ResumeAnalysisOverview } from './ResumeAnalysisOverview'
import { ResumeAnalysisDetail } from './ResumeAnalysisDetail'
import { ResumeSuggestions } from './ResumeSuggestions'

interface ResumeAnalysisTabsProps {
    analysis: ResumeAnalysis
    activeTab: "overview" | "analysis" | "suggestions"
    onTabChange: (tab: "overview" | "analysis" | "suggestions") => void
    renderScoreBar: (score: number) => React.ReactNode
    renderPriorityBadge: (priority: "high" | "medium" | "low") => React.ReactNode
}

export function ResumeAnalysisTabs({
    analysis,
    activeTab,
    onTabChange,
    renderScoreBar,
    renderPriorityBadge
}: ResumeAnalysisTabsProps) {
    return (
        <div className="bg-card rounded-lg shadow-sm mb-8">
            <div className="border-b border-border">
                <nav className="flex">
                    <button
                        className={`px-4 py-3 font-medium text-sm relative ${activeTab === "overview"
                                ? "text-primary"
                                : "text-muted-foreground hover:text-foreground"
                            }`}
                        onClick={() => onTabChange("overview")}
                    >
                        总览
                        {activeTab === "overview" && (
                            <span className="absolute bottom-0 left-0 w-full h-0.5 bg-primary"></span>
                        )}
                    </button>
                    <button
                        className={`px-4 py-3 font-medium text-sm relative ${activeTab === "analysis"
                                ? "text-primary"
                                : "text-muted-foreground hover:text-foreground"
                            }`}
                        onClick={() => onTabChange("analysis")}
                    >
                        详细分析
                        {activeTab === "analysis" && (
                            <span className="absolute bottom-0 left-0 w-full h-0.5 bg-primary"></span>
                        )}
                    </button>
                    <button
                        className={`px-4 py-3 font-medium text-sm relative ${activeTab === "suggestions"
                                ? "text-primary"
                                : "text-muted-foreground hover:text-foreground"
                            }`}
                        onClick={() => onTabChange("suggestions")}
                    >
                        优化建议
                        {activeTab === "suggestions" && (
                            <span className="absolute bottom-0 left-0 w-full h-0.5 bg-primary"></span>
                        )}
                    </button>
                </nav>
            </div>

            <div className="p-6">
                {activeTab === "overview" && (
                    <ResumeAnalysisOverview
                        analysis={analysis}
                        renderScoreBar={renderScoreBar}
                    />
                )}

                {activeTab === "analysis" && (
                    <ResumeAnalysisDetail
                        analysis={analysis}
                        renderScoreBar={renderScoreBar}
                    />
                )}

                {activeTab === "suggestions" && (
                    <ResumeSuggestions
                        analysis={analysis}
                        renderPriorityBadge={renderPriorityBadge}
                    />
                )}
            </div>
        </div>
    )
} 