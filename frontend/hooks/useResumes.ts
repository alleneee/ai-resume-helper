import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from '@/hooks/use-toast';

export interface Resume {
    id: string;
    fileName: string;
    uploadDate: string;
    status: "pending" | "processed" | "analyzed" | "failed";
    score?: number;
}

export function useResumes() {
    const queryClient = useQueryClient();

    // 获取简历列表
    const {
        data: resumes,
        isLoading,
        error,
        refetch
    } = useQuery<Resume[]>({
        queryKey: ['resumes'],
        queryFn: async () => {
            const response = await fetch('/api/resume/list');
            if (!response.ok) {
                throw new Error("获取简历列表失败");
            }
            return response.json();
        }
    });

    // 删除简历
    const { mutate: deleteResume, isPending: isDeleting } = useMutation({
        mutationFn: async (id: string) => {
            const response = await fetch(`/api/resume/${id}`, {
                method: "DELETE",
            });
            if (!response.ok) {
                throw new Error("删除简历失败");
            }
            return response.json();
        },
        onSuccess: (_, id) => {
            toast({
                title: "删除成功",
                description: "简历已成功删除",
            });

            // 更新缓存
            queryClient.setQueryData<Resume[]>(
                ['resumes'],
                (old) => old ? old.filter(resume => resume.id !== id) : []
            );
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
        resumes,
        isLoading,
        error,
        refetch,
        deleteResume,
        isDeleting
    };
} 