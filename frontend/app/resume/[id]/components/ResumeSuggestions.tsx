"use client"

import { ResumeAnalysis, ResumeSuggestion } from '../types'

interface ResumeSuggestionsProps {
    analysis: ResumeAnalysis
    renderPriorityBadge: (priority: "high" | "medium" | "low") => React.ReactNode
}

export function ResumeSuggestions({
    analysis,
    renderPriorityBadge
}: ResumeSuggestionsProps) {
    return (
        <div>
            <h3 className="text-lg font-medium mb-4">优化建议</h3>

            <div className="space-y-4">
                {analysis.suggestions.map((suggestion, index) => (
                    <div key={index} className="border rounded-lg p-4">
                        <div className="flex justify-between items-start mb-3">
                            <div className="flex items-center">
                                <span className="font-medium mr-2">{suggestion.category}</span>
                                {renderPriorityBadge(suggestion.priority)}
                            </div>
                        </div>
                        <p className="text-muted-foreground">{suggestion.content}</p>
                    </div>
                ))}
            </div>
        </div>
    )
} 