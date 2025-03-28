export interface ResumeDetail {
    id: string;
    fileName: string;
    uploadDate: string;
    fileUrl: string;
    status: "pending" | "processed" | "analyzed" | "failed";
    score?: number;
    analysis?: ResumeAnalysis;
}

export interface ResumeAnalysis {
    overallScore: number;
    sections: ResumeSection[];
    strengths: string[];
    weaknesses: string[];
    suggestions: ResumeSuggestion[];
}

export interface ResumeSection {
    name: string;
    score: number;
    feedback: string;
}

export interface ResumeSuggestion {
    category: string;
    content: string;
    priority: "high" | "medium" | "low";
} 