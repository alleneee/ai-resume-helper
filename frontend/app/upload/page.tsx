"use client"

import { useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { toast } from "@/hooks/use-toast"

export default function UploadPage() {
    const router = useRouter()
    const [isDragging, setIsDragging] = useState(false)
    const [file, setFile] = useState<File | null>(null)
    const [isUploading, setIsUploading] = useState(false)

    const onDrop = useCallback((acceptedFiles: File[]) => {
        if (acceptedFiles.length > 0) {
            const file = acceptedFiles[0]
            // 检查文件类型
            const validFileTypes = [
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "image/jpeg",
                "image/png"
            ]

            if (!validFileTypes.includes(file.type)) {
                toast({
                    title: "文件类型不支持",
                    description: "请上传PDF、DOCX、JPG或PNG格式的文件",
                    variant: "destructive"
                })
                return
            }

            // 检查文件大小（限制为10MB）
            if (file.size > 10 * 1024 * 1024) {
                toast({
                    title: "文件过大",
                    description: "文件大小不能超过10MB",
                    variant: "destructive"
                })
                return
            }

            setFile(file)
        }
    }, [])

    const handleDragEnter = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        setIsDragging(true)
    }, [])

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        setIsDragging(false)
    }, [])

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        if (!isDragging) {
            setIsDragging(true)
        }
    }, [isDragging])

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        e.stopPropagation()
        setIsDragging(false)

        const dt = e.dataTransfer
        const files = dt.files
        const filesArray = Array.from(files)

        onDrop(filesArray)
    }, [onDrop])

    const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            const filesArray = Array.from(e.target.files)
            onDrop(filesArray)
        }
    }, [onDrop])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!file) {
            toast({
                title: "请先上传文件",
                description: "请选择一个简历文件进行上传",
                variant: "destructive"
            })
            return
        }

        setIsUploading(true)

        try {
            const formData = new FormData()
            formData.append("file", file)

            const response = await fetch("/api/resume/upload", {
                method: "POST",
                body: formData,
            })

            if (!response.ok) {
                throw new Error("上传失败")
            }

            const data = await response.json()

            toast({
                title: "上传成功",
                description: "您的简历已成功上传",
            })

            // 上传成功后跳转到简历详情页
            router.push(`/resume/${data.resumeId}`)
        } catch (error) {
            console.error("上传错误:", error)
            toast({
                title: "上传失败",
                description: "上传简历时出错，请稍后重试",
                variant: "destructive"
            })
        } finally {
            setIsUploading(false)
        }
    }

    return (
        <div className="container mx-auto px-4 py-8 max-w-4xl">
            <h1 className="text-3xl font-bold mb-8 text-center">上传您的简历</h1>

            <div className="bg-card rounded-lg shadow-sm p-6">
                <form onSubmit={handleSubmit}>
                    <div
                        className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors ${isDragging
                                ? "border-primary bg-primary/5"
                                : file
                                    ? "border-green-500 bg-green-50/10"
                                    : "border-border hover:border-primary/50 hover:bg-muted/50"
                            }`}
                        onDragEnter={handleDragEnter}
                        onDragLeave={handleDragLeave}
                        onDragOver={handleDragOver}
                        onDrop={handleDrop}
                        onClick={() => document.getElementById("file-input")?.click()}
                    >
                        <input
                            id="file-input"
                            type="file"
                            className="hidden"
                            accept=".pdf,.docx,.doc,.jpg,.jpeg,.png"
                            onChange={handleFileChange}
                        />

                        {file ? (
                            <div className="space-y-2">
                                <div className="flex items-center justify-center">
                                    <svg
                                        className="h-8 w-8 text-green-500"
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
                                        <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
                                        <path d="m9 12 2 2 4-4" />
                                    </svg>
                                </div>
                                <p className="text-lg font-medium">{file.name}</p>
                                <p className="text-sm text-muted-foreground">
                                    {(file.size / 1024 / 1024).toFixed(2)} MB
                                </p>
                                <p className="text-sm text-blue-500 underline cursor-pointer" onClick={(e) => {
                                    e.stopPropagation()
                                    setFile(null)
                                }}>
                                    更换文件
                                </p>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                <div className="flex justify-center">
                                    <svg
                                        className="h-10 w-10 text-muted-foreground"
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
                                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                                        <polyline points="17 8 12 3 7 8" />
                                        <line x1="12" x2="12" y1="3" y2="15" />
                                    </svg>
                                </div>
                                <div>
                                    <p className="text-lg font-medium">
                                        拖放您的简历至此处或点击上传
                                    </p>
                                    <p className="text-sm text-muted-foreground mt-1">
                                        支持PDF、DOCX、JPG和PNG格式，文件大小不超过10MB
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="mt-6 flex justify-end">
                        <button
                            type="submit"
                            className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90 transition-colors"
                            disabled={!file || isUploading}
                        >
                            {isUploading ? (
                                <span className="flex items-center">
                                    <svg
                                        className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                                        xmlns="http://www.w3.org/2000/svg"
                                        fill="none"
                                        viewBox="0 0 24 24"
                                    >
                                        <circle
                                            className="opacity-25"
                                            cx="12"
                                            cy="12"
                                            r="10"
                                            stroke="currentColor"
                                            strokeWidth="4"
                                        ></circle>
                                        <path
                                            className="opacity-75"
                                            fill="currentColor"
                                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                        ></path>
                                    </svg>
                                    正在上传...
                                </span>
                            ) : (
                                "上传并分析"
                            )}
                        </button>
                    </div>
                </form>
            </div>

            <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-card rounded-lg p-4 shadow-sm">
                    <h3 className="font-medium text-lg mb-2">支持多种文件格式</h3>
                    <p className="text-sm text-muted-foreground">
                        系统支持PDF、DOCX、JPG和PNG格式的简历文件，确保您的信息能够准确提取
                    </p>
                </div>

                <div className="bg-card rounded-lg p-4 shadow-sm">
                    <h3 className="font-medium text-lg mb-2">保护隐私安全</h3>
                    <p className="text-sm text-muted-foreground">
                        我们重视用户隐私，所有上传的简历数据均被安全加密存储，不会用于其他用途
                    </p>
                </div>

                <div className="bg-card rounded-lg p-4 shadow-sm">
                    <h3 className="font-medium text-lg mb-2">高效智能分析</h3>
                    <p className="text-sm text-muted-foreground">
                        先进的AI技术快速分析您的简历，提供专业的评估结果和优化建议
                    </p>
                </div>
            </div>
        </div>
    )
} 