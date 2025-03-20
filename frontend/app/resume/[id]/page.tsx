import { Metadata } from "next";
import ResumeDetailClient from "./ResumeDetailClient";

export const metadata: Metadata = {
    title: "简历详情 | AI简历助手",
    description: "查看详细的简历分析和改进建议",
};

export default function ResumeDetailPage({
    params,
}: {
    params: { id: string };
}) {
    return <ResumeDetailClient id={params.id} />;
} 