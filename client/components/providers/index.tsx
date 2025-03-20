"use client"

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ReactQueryDevtools } from "@tanstack/react-query-devtools"
import { useState } from "react"
import { Toaster } from "@/components/ui/toaster"
import { AuthProvider } from "@/contexts/AuthContext"
import { Toaster as HotToaster } from 'react-hot-toast'

interface ProvidersProps {
    children: React.ReactNode
}

export function Providers({ children }: ProvidersProps) {
    const [queryClient] = useState(() => new QueryClient({
        defaultOptions: {
            queries: {
                staleTime: 60 * 1000, // 1分钟
                refetchOnWindowFocus: false,
            },
        },
    }))

    return (
        <QueryClientProvider client={queryClient}>
            <AuthProvider>
                {children}
                {process.env.NODE_ENV === "development" && <ReactQueryDevtools initialIsOpen={false} />}
                <Toaster />
                <HotToaster position="top-center" />
            </AuthProvider>
        </QueryClientProvider>
    )
} 