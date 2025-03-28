"use client"

interface ResumePdfViewerProps {
    fileUrl: string;
}

export function ResumePdfViewer({ fileUrl }: ResumePdfViewerProps) {
    return (
        <div className="mb-8 bg-card rounded-lg shadow-sm overflow-hidden">
            <div className="border-b px-4 py-3 flex justify-between items-center">
                <h2 className="font-medium">简历预览</h2>
                <a
                    href={fileUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline text-sm"
                >
                    在新窗口打开
                </a>
            </div>
            <div className="h-[600px]">
                <iframe
                    src={fileUrl}
                    className="w-full h-full"
                    title="Resume Preview"
                ></iframe>
            </div>
        </div>
    );
} 