import "./globals.css";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ThemeProvider } from "@/components/shared/theme-provider";
import { Providers } from "@/components/providers";
import dynamic from "next/dynamic";

const Navbar = dynamic(() => import("@/components/layout/Navbar"), { ssr: false });

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "AI简历助手",
    description: "智能简历分析与优化工具，帮助您提升简历质量，提高求职成功率",
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="zh-CN" suppressHydrationWarning>
            <body className={inter.className}>
                <ThemeProvider
                    attribute="class"
                    defaultTheme="system"
                    enableSystem
                    disableTransitionOnChange
                >
                    <Providers>
                        <div className="flex flex-col min-h-screen">
                            <Navbar />
                            <main className="flex-grow">
                                {children}
                            </main>
                        </div>
                    </Providers>
                </ThemeProvider>
            </body>
        </html>
    );
} 