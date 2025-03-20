"use client"

import { Button } from "@/components/ui/button";
import { Loader2, AlertTriangle, RefreshCw } from "lucide-react";

export function LoadingState() {
    return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
            <Loader2 className="h-10 w-10 text-primary animate-spin mb-4" />
            <h3 className="text-lg font-medium">正在加载简历详情...</h3>
            <p className="text-sm text-muted-foreground mt-2">请稍候片刻</p>
        </div>
    );
}

export function NotFoundState() {
    return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center">
            <AlertTriangle className="h-10 w-10 text-yellow-500 mb-4" />
            <h3 className="text-lg font-medium">找不到简历</h3>
            <p className="text-sm text-muted-foreground mt-2 max-w-md">
                无法找到请求的简历。它可能已被删除或链接无效。
            </p>
            <Button
                variant="outline"
                className="mt-4"
                onClick={() => window.history.back()}
            >
                返回上一页
            </Button>
        </div>
    );
}

export function ErrorState({ message }: { message: string }) {
    return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center">
            <AlertTriangle className="h-10 w-10 text-destructive mb-4" />
            <h3 className="text-lg font-medium">出现错误</h3>
            <p className="text-sm text-muted-foreground mt-2 max-w-md">
                {message || "加载简历时发生错误，请稍后重试。"}
            </p>
            <Button
                variant="outline"
                className="mt-4"
                onClick={() => window.location.reload()}
            >
                重试
            </Button>
            <Button
                variant="ghost"
                className="mt-2"
                onClick={() => window.history.back()}
            >
                返回上一页
            </Button>
        </div>
    );
}

export function ProcessingState({ onRefresh }: { onRefresh: () => void }) {
    return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center">
            <div className="flex items-center justify-center mb-4 relative">
                <div className="absolute inset-0 border-t-2 border-primary rounded-full animate-spin"></div>
                <RefreshCw className="h-10 w-10 text-primary" />
            </div>
            <h3 className="text-lg font-medium">正在处理您的简历</h3>
            <p className="text-sm text-muted-foreground mt-2 max-w-md">
                AI 正在分析您的简历。这个过程可能需要几分钟时间，请稍候片刻。
            </p>
            <Button variant="outline" className="mt-4" onClick={onRefresh}>
                刷新状态
            </Button>
        </div>
    );
}

export function FailedState({ onRetry }: { onRetry: () => void }) {
    return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center">
            <AlertTriangle className="h-10 w-10 text-destructive mb-4" />
            <h3 className="text-lg font-medium">分析失败</h3>
            <p className="text-sm text-muted-foreground mt-2 max-w-md">
                很抱歉，我们无法成功分析您的简历。这可能是由于文件格式问题或其他技术原因。
            </p>
            <Button variant="outline" className="mt-4" onClick={onRetry}>
                重新分析
            </Button>
        </div>
    );
} 