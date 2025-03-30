import React, { useState, useEffect } from 'react';
import { Upload, Search, FileText, BarChart3, FileCheck2, Download, ChevronLeft, ChevronRight, LogOut } from 'lucide-react';
import { Steps, Input, Select, Upload as AntUpload, Progress, Card, Tag, Button, message, Spin, Dropdown } from 'antd';
import type { UploadProps } from 'antd';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { resumeApi, authApi, ApiResponse, OptimizedResume } from './services/api';
import Login from './pages/Login';
import Register from './pages/Register';

type Step = {
  id: number;
  title: string;
  icon: React.ReactNode;
};

// 自定义上传文件类型
interface CustomFile extends File {
  name: string;
}

// API响应数据类型扩展
interface ResumeData {
  _id: string;
  raw_text?: string;
  parsed_sections?: Record<string, any>;
  title?: string;
  description?: string;
  file_name?: string;
  [key: string]: any;
}

// 定义 JobSearchCriteria 接口
interface JobSearchCriteria {
  keywords: string[];
  location?: string;
  limit?: number;
  // 根据需要添加其他字段
}

// 受保护的路由组件
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          setIsAuthenticated(false);
          setIsLoading(false);
          return;
        }

        // 验证token
        const response = await authApi.getCurrentUser();
        const responseData = response as unknown as ApiResponse<any>;

        if (responseData?.success === true) {
          setIsAuthenticated(true);
        } else {
          localStorage.removeItem('token');
          setIsAuthenticated(false);
        }
      } catch (error) {
        localStorage.removeItem('token');
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, [navigate]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
        <Spin size="large" />
      </div>
    );
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
};

// 主应用组件
const MainApp = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [filters, setFilters] = useState({
    position: '',
    location: '',
    experience: '',
    salary: ''
  });
  const [resumeId, setResumeId] = useState<string | null>(null);
  const [uploadedResumeData, setUploadedResumeData] = useState<ResumeData | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizedResult, setOptimizedResult] = useState<OptimizedResume | null>(null);
  const navigate = useNavigate();

  const steps: Step[] = [
    { id: 1, title: '筛选条件', icon: <Search className="w-6 h-6" /> },
    { id: 2, title: '上传简历', icon: <Upload className="w-6 h-6" /> },
    { id: 3, title: '职位分析', icon: <BarChart3 className="w-6 h-6" /> },
    { id: 4, title: '简历优化', icon: <FileText className="w-6 h-6" /> },
    { id: 5, title: '下载结果', icon: <Download className="w-6 h-6" /> }
  ];

  const handleNext = async () => {
    if (currentStep < steps.length) {
      if (currentStep === 2 && uploadedResumeData && filters.position) {
        setIsOptimizing(true);
        try {
          const resumeDataForApi: { raw_text: string, parsed_sections?: Record<string, any> } = {
            raw_text: uploadedResumeData.raw_text || "",
            parsed_sections: uploadedResumeData.parsed_sections,
          };

          const searchCriteriaForApi: JobSearchCriteria = {
            keywords: filters.position.split(' ').filter(k => k.trim() !== ''),
            location: filters.location || undefined,
            limit: 10,
          };

          console.log("Calling optimizeResumeApi with:", { resume_data: resumeDataForApi, search_criteria: searchCriteriaForApi });

          const response = await resumeApi.optimizeResumeApi(resumeDataForApi, searchCriteriaForApi);

          if (response && typeof response.success === 'boolean') {
            if (response.success) {
              setOptimizedResult(response.data);
              message.success('简历优化成功！');
              setCurrentStep(currentStep + 1);
            } else {
              message.error(response.message || '简历优化失败，请查看后端日志');
            }
          } else {
            console.error('Unexpected API response format:', response);
            message.error('优化请求失败，响应格式错误');
          }
        } catch (error: any) {
          console.error("优化 API 调用错误:", error);
          const errorMsg = error.response?.data?.message || error.message || '优化过程中发生未知网络或服务器错误';
          message.error(errorMsg);
        } finally {
          setIsOptimizing(false);
        }
      } else if (currentStep === 2 && (!uploadedResumeData || !filters.position)) {
        message.warning('请先上传简历并填写职位名称');
      } else {
        setCurrentStep(currentStep + 1);
      }
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('token');
      navigate('/login');
    }
  };

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    showUploadList: false,
    customRequest: async ({ file, onSuccess, onError }) => {
      setIsUploading(true);
      const formData = new FormData();
      const uploadFile = file as CustomFile;
      formData.append('resume_file', uploadFile);
      formData.append('title', uploadFile.name || 'Uploaded Resume');
      formData.append('description', `Uploaded: ${new Date().toLocaleString()}`);

      try {
        const response = await resumeApi.uploadResume(formData);

        if (response && response.success === true && response.data?.id) {
          setResumeId(response.data.id);
          setUploadedResumeData(response.data);
          onSuccess?.(response.data, {} as XMLHttpRequest);
          message.success(`${uploadFile.name} 上传成功`);
        } else {
          const errorMsg = response?.message || '上传失败，响应无效';
          onError?.(new Error(errorMsg));
          message.error(`${uploadFile.name} 上传失败: ${errorMsg}`);
        }
      } catch (error: any) {
        const uploadFile = file as CustomFile;
        const errorMsg = error.response?.data?.message || error.message || '上传时发生网络或服务器错误';
        onError?.(error as Error);
        message.error(`${uploadFile.name} 上传失败: ${errorMsg}`);
      } finally {
        setIsUploading(false);
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-gray-200">
      {/* Header */}
      <header className="bg-black/30 backdrop-blur-lg border-b border-gray-700 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <FileCheck2 className="w-8 h-8 text-blue-400" />
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
              智能职位分析与简历优化系统
            </span>
          </h1>
          <Dropdown
            menu={{
              items: [
                { key: 'logout', label: '退出登录', onClick: handleLogout }
              ]
            }}
            placement="bottomRight"
          >
            <Button
              type="text"
              icon={<LogOut className="w-5 h-5 text-gray-400" />}
              className="text-gray-400 hover:text-white"
            >
              退出
            </Button>
          </Dropdown>
        </div>
      </header>

      {/* Progress Steps */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
        <Steps
          current={currentStep - 1}
          items={steps.map(step => ({
            title: step.title,
            icon: <div className="flex items-center justify-center w-8 h-8">{step.icon}</div>
          }))}
          className="custom-steps"
        />
      </div>

      {/* Main Content */}
      <div className="max-w-3xl mx-auto mt-12 px-4 sm:px-6 lg:px-8 pb-12">
        <Card className="backdrop-blur-xl bg-white/10 border border-gray-700 shadow-2xl">
          <Spin spinning={isOptimizing || isUploading} tip={isUploading ? "正在上传..." : "正在优化简历..."}>
            {/* 步骤 1: 筛选条件 */}
            {currentStep === 1 && (
              <div className="space-y-6 p-6">
                <h2 className="text-xl font-semibold text-white">1. 设置职位筛选条件</h2>
                <div className="grid grid-cols-1 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">职位名称 (关键词)</label>
                    <Input
                      placeholder="例如：前端开发工程师 React"
                      value={filters.position}
                      onChange={(e) => setFilters({ ...filters, position: e.target.value })}
                      className="bg-white/5 border-gray-600 text-white placeholder:text-gray-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">工作地点</label>
                    <Input
                      placeholder="例如：上海 (可选)"
                      value={filters.location}
                      onChange={(e) => setFilters({ ...filters, location: e.target.value })}
                      className="bg-white/5 border-gray-600 text-white placeholder:text-gray-500"
                    />
                  </div>
                  {/* 可以添加更多筛选器，如经验、薪资 */}
                </div>
              </div>
            )}

            {/* 步骤 2: 上传简历 */}
            {currentStep === 2 && (
              <div className="space-y-6 p-6">
                <h2 className="text-xl font-semibold text-white">2. 上传个人简历</h2>
                <AntUpload.Dragger {...uploadProps} className="bg-white/5 border-gray-600 hover:border-blue-500 transition-colors">
                  <div className="p-8 text-center">
                    <p className="text-4xl text-blue-400 mb-4">
                      <Upload className="mx-auto" />
                    </p>
                    <p className="text-gray-300">点击或拖拽文件到此处上传</p>
                    <p className="text-gray-400 text-sm mt-1">支持 PDF, Word (.doc, .docx) 格式</p>
                  </div>
                </AntUpload.Dragger>
                {resumeId && (
                  <div className="text-center text-green-400 mt-4">
                    简历上传成功！ID: {resumeId}
                  </div>
                )}
              </div>
            )}

            {/* 步骤 3: 职位分析 */}
            {currentStep === 3 && (
              <div className="space-y-6 p-6">
                <h2 className="text-xl font-semibold text-white">3. 职位分析报告</h2>
                {isOptimizing && <p className="text-gray-400 text-center">正在分析职位和您的简历...</p>}
                {!optimizedResult && !isOptimizing && (
                  <p className="text-gray-400 text-center">请先完成上一步以生成分析报告。</p>
                )}
                {optimizedResult?.analysis_summary && (
                  <Card className="bg-white/5 border-gray-700 mt-4">
                    <h3 className="font-medium text-white mb-4">分析摘要</h3>
                    <pre className="text-gray-300 bg-gray-800 p-4 rounded text-xs overflow-auto">
                      {JSON.stringify(optimizedResult.analysis_summary, null, 2)}
                    </pre>
                  </Card>
                )}
                {/* 在这里添加更多用于显示分析结果的 UI */}
              </div>
            )}

            {/* 步骤 4: 简历优化 */}
            {currentStep === 4 && (
              <div className="space-y-6 p-6">
                <h2 className="text-xl font-semibold text-white">4. 简历优化建议</h2>
                {isOptimizing && <p className="text-gray-400 text-center">正在生成优化建议...</p>}
                {!optimizedResult && !isOptimizing && (
                  <p className="text-gray-400 text-center">请先完成上一步以生成优化建议。</p>
                )}
                {optimizedResult?.optimized_text && (
                  <Card className="bg-white/5 border-gray-700 mt-4">
                    <h3 className="font-medium text-white mb-4">优化后的简历文本</h3>
                    <p className="text-gray-300 whitespace-pre-wrap text-sm bg-gray-800 p-4 rounded">
                      {optimizedResult.optimized_text}
                    </p>
                  </Card>
                )}
                {/* 可以在这里添加显示其他优化建议的 UI，例如技能匹配度等 */}
              </div>
            )}

            {/* 步骤 5: 下载结果 */}
            {currentStep === 5 && (
              <div className="space-y-6 p-6">
                <h2 className="text-xl font-semibold text-white">5. 下载优化结果</h2>
                {!optimizedResult && (
                  <p className="text-gray-400 text-center">优化结果尚未生成。</p>
                )}
                {optimizedResult && (
                  <div className="space-y-4">
                    {/* 实际下载功能需要后端支持 */}
                    <Button
                      type="primary"
                      icon={<FileText className="w-5 h-5" />}
                      className="w-full h-auto py-2 flex items-center justify-center bg-gradient-to-r from-blue-500 to-blue-600"
                      onClick={() => message.info('下载分析报告功能待实现')}
                    >
                      下载职位分析报告 (待实现)
                    </Button>
                    <Button
                      type="primary"
                      icon={<Download className="w-5 h-5" />}
                      className="w-full h-auto py-2 flex items-center justify-center bg-gradient-to-r from-green-500 to-green-600"
                      onClick={() => message.info('下载优化简历功能待实现')}
                    >
                      下载优化后的简历 (待实现)
                    </Button>
                  </div>
                )}
              </div>
            )}
          </Spin>

          {/* Navigation Buttons */}
          <div className="mt-8 px-6 pb-6 flex justify-between border-t border-gray-700 pt-6">
            <Button
              onClick={handlePrevious}
              disabled={currentStep === 1 || isOptimizing || isUploading}
              icon={<ChevronLeft className="w-4 h-4" />}
              className={`${currentStep === 1 ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              上一步
            </Button>
            <Button
              onClick={handleNext}
              disabled={currentStep === steps.length || isOptimizing || isUploading || (currentStep === 2 && !resumeId)}
              type="primary"
              loading={isOptimizing && currentStep === 2}
              className={`${currentStep === steps.length ? 'opacity-50 cursor-not-allowed' : ''} ${currentStep === 2 && !resumeId ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              {currentStep === steps.length ? '完成' : (
                <span className="flex items-center">
                  {currentStep === 2 ? '分析与优化' : '下一步'}
                  <ChevronRight className="w-4 h-4 ml-1" />
                </span>
              )}
            </Button>
          </div>
        </Card>
      </div>

      {/* Footer or other elements can go here */}
    </div>
  );
};

// App Router Setup
const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<ProtectedRoute><MainApp /></ProtectedRoute>} />
      </Routes>
    </Router>
  );
};

export default App;