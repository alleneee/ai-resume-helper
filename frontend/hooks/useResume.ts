import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from '@/hooks/use-toast';
import { ResumeDetail } from '@/app/resume/[id]/types';
import { useRouter } from 'next/navigation';

export function useResume(id: string) {
    const router = useRouter();
    const queryClient = useQueryClient();

    // 获取简历数据
    const {
        data: resume,
        isLoading,
        error,
        refetch
    } = useQuery<ResumeDetail>({
        queryKey: ['resume', id],
        queryFn: async () => {
            const response = await fetch(`/api/resume/${id}`);
            if (!response.ok) {
                throw new Error("获取简历详情失败");
            }
            return response.json();
        }
    });

    // 重新分析简历
    const { mutate: reanalyzeResume, isPending: isReanalyzing } = useMutation({
        mutationFn: async () => {
            const response = await fetch(`/api/resume/${id}/analyze`, {
                method: "POST",
            });
            if (!response.ok) {
                throw new Error("重新分析失败");
            }
            return response.json();
        },
        onSuccess: () => {
            toast({
                title: "分析请求已提交",
                description: "您的简历正在重新分析中，请稍后刷新页面查看结果",
            });
            // 5秒后重新获取简历数据
            setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ['resume', id] });
            }, 5000);
        },
        onError: (error) => {
            console.error("重新分析错误:", error);
            toast({
                title: "重新分析失败",
                description: "无法提交分析请求，请稍后重试",
                variant: "destructive"
            });
        }
    });

    // 删除简历
    const { mutate: deleteResume, isPending: isDeleting } = useMutation({
        mutationFn: async () => {
            const response = await fetch(`/api/resume/${id}`, {
                method: "DELETE",
            });
            if (!response.ok) {
                throw new Error("删除简历失败");
            }
            return response.json();
        },
        onSuccess: () => {
            toast({
                title: "删除成功",
                description: "简历已成功删除",
            });

            router.push("/dashboard");
        },
        onError: (error) => {
            console.error("删除错误:", error);
            toast({
                title: "删除失败",
                description: "无法删除简历，请稍后重试",
                variant: "destructive"
            });
        }
    });

    return {
        resume,
        isLoading,
        error,
        refetch,
        reanalyzeResume,
        isReanalyzing,
        deleteResume,
        isDeleting
    };
} 