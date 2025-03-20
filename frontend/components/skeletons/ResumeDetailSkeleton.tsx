export function ResumeDetailSkeleton() {
    return (
        <div className="container mx-auto px-4 py-8 max-w-6xl animate-pulse">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
                <div>
                    <div className="h-8 w-64 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
                    <div className="h-4 w-48 bg-gray-200 dark:bg-gray-700 rounded"></div>
                </div>
                <div className="flex gap-3">
                    <div className="h-10 w-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
                    <div className="h-10 w-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
                </div>
            </div>

            <div className="bg-card rounded-lg shadow-sm mb-8">
                <div className="border-b border-border">
                    <div className="flex">
                        <div className="h-10 w-20 bg-gray-200 dark:bg-gray-700 rounded m-2"></div>
                        <div className="h-10 w-20 bg-gray-200 dark:bg-gray-700 rounded m-2"></div>
                        <div className="h-10 w-20 bg-gray-200 dark:bg-gray-700 rounded m-2"></div>
                    </div>
                </div>

                <div className="p-6">
                    <div className="flex flex-col md:flex-row justify-between gap-6 mb-8">
                        <div className="flex-1">
                            <div className="h-6 w-32 bg-gray-200 dark:bg-gray-700 rounded mb-4"></div>
                            <div className="h-24 w-full bg-gray-200 dark:bg-gray-700 rounded mb-6"></div>

                            <div className="space-y-3">
                                {[1, 2, 3, 4].map((i) => (
                                    <div key={i}>
                                        <div className="flex justify-between items-center mb-1">
                                            <div className="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
                                            <div className="h-4 w-12 bg-gray-200 dark:bg-gray-700 rounded"></div>
                                        </div>
                                        <div className="h-2 w-full bg-gray-200 dark:bg-gray-700 rounded"></div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="flex-1">
                            <div className="h-6 w-32 bg-gray-200 dark:bg-gray-700 rounded mb-4"></div>
                            {[1, 2, 3].map((i) => (
                                <div key={i} className="h-6 w-full bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
                            ))}

                            <div className="h-6 w-32 bg-gray-200 dark:bg-gray-700 rounded my-4"></div>
                            {[1, 2, 3].map((i) => (
                                <div key={i} className="h-6 w-full bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
} 