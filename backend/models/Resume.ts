import mongoose, { Document, Schema } from 'mongoose';

// 简历处理状态
export enum ResumeStatus {
    UPLOADED = 'uploaded',   // 已上传，尚未处理
    PROCESSING = 'processing', // 处理中
    ANALYZED = 'analyzed',   // 分析完成
    FAILED = 'failed'        // 处理失败
}

// 简历分析结果结构
export interface ResumeAnalysis {
    skills: {
        name: string;
        level?: string;
        category?: string;
        relevance?: number;
    }[];
    experience: {
        title: string;
        company: string;
        startDate: Date;
        endDate?: Date;
        description: string;
        highlights: string[];
    }[];
    education: {
        institution: string;
        degree: string;
        field: string;
        startDate: Date;
        endDate?: Date;
        gpa?: number;
    }[];
    summary?: string;
    strengths?: string[];
    weaknesses?: string[];
    recommendations?: string[];
    keywords?: string[];
    scoreDetails?: {
        relevanceScore: number;
        completenessScore: number;
        formattingScore: number;
        languageScore: number;
        overallScore: number;
    };
    metadata?: Record<string, any>;
}

// 简历文档接口
export interface ResumeDocument extends Document {
    userId: mongoose.Types.ObjectId | string;
    fileName: string;
    originalName: string;
    mimeType: string;
    fileSize: number;
    filePath: string;
    uploadDate: Date;
    status: ResumeStatus;
    lastUpdated: Date;
    error?: string;
    jobTitle?: string;
    jobDescription?: string;
    analysis?: ResumeAnalysis;
    score?: number;
    feedback?: string[];
}

// 简历Schema定义
const ResumeSchema = new Schema<ResumeDocument>({
    userId: {
        type: Schema.Types.ObjectId,
        ref: 'User',
        required: true
    },
    fileName: {
        type: String,
        required: true
    },
    originalName: {
        type: String,
        required: true
    },
    mimeType: {
        type: String,
        required: true
    },
    fileSize: {
        type: Number,
        required: true
    },
    filePath: {
        type: String,
        required: true
    },
    uploadDate: {
        type: Date,
        default: Date.now
    },
    status: {
        type: String,
        enum: Object.values(ResumeStatus),
        default: ResumeStatus.UPLOADED
    },
    lastUpdated: {
        type: Date,
        default: Date.now
    },
    error: {
        type: String
    },
    jobTitle: {
        type: String
    },
    jobDescription: {
        type: String
    },
    analysis: {
        type: Schema.Types.Mixed
    },
    score: {
        type: Number,
        min: 0,
        max: 100
    },
    feedback: {
        type: [String]
    }
}, {
    timestamps: true,
    toJSON: {
        virtuals: true,
        transform: function (_doc, ret) {
            delete ret.__v;
            return ret;
        }
    }
});

// 创建索引
ResumeSchema.index({ userId: 1, uploadDate: -1 });
ResumeSchema.index({ status: 1 });

// 导出模型
const Resume = mongoose.model<ResumeDocument>('Resume', ResumeSchema);

export default Resume; 