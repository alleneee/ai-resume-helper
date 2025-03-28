import React, { useState, useEffect } from 'react';
import { Upload, Search, FileText, BarChart3, FileCheck2, Download, ChevronLeft, ChevronRight, LogOut } from 'lucide-react';
import { Steps, Input, Select, Upload as AntUpload, Progress, Card, Tag, Button, message, Spin, Dropdown } from 'antd';
import type { UploadProps } from 'antd';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { resumeApi, authApi, ApiResponse } from './services/api';
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
  [key: string]: any;
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

        if (responseData?.status === 'success') {
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
  const [isUploading, setIsUploading] = useState(false);
  const navigate = useNavigate();

  const steps: Step[] = [
    { id: 1, title: '筛选条件', icon: <Search className="w-6 h-6" /> },
    { id: 2, title: '上传简历', icon: <Upload className="w-6 h-6" /> },
    { id: 3, title: '职位分析', icon: <BarChart3 className="w-6 h-6" /> },
    { id: 4, title: '简历优化', icon: <FileText className="w-6 h-6" /> },
    { id: 5, title: '下载结果', icon: <Download className="w-6 h-6" /> }
  ];

  const handleNext = () => {
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
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
    customRequest: async ({ file, onSuccess, onError }) => {
      try {
        setIsUploading(true);
        const formData = new FormData();

        // 确保file是File类型并有name属性
        const uploadFile = file as CustomFile;

        formData.append('resume_file', uploadFile);
        formData.append('title', '我的简历');
        formData.append('description', '通过系统上传的简历');

        const response = await resumeApi.uploadResume(formData);

        // 类型断言帮助TypeScript理解数据结构
        const responseData = response as unknown as ApiResponse<ResumeData>;

        if (responseData?.status === 'success') {
          setResumeId(responseData.data._id);
          onSuccess?.(response);
          message.success(`${uploadFile.name} 上传成功`);
        } else {
          onError?.(new Error('上传失败'));
          message.error(`${uploadFile.name} 上传失败`);
        }
      } catch (error) {
        const uploadFile = file as CustomFile;
        onError?.(error as Error);
        message.error(`${uploadFile.name} 上传失败`);
      } finally {
        setIsUploading(false);
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <header className="bg-black/30 backdrop-blur-lg border-b border-gray-700">
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
            icon: <div className="flex items-center justify-center">{step.icon}</div>
          }))}
          className="custom-steps"
        />
      </div>

      {/* Main Content */}
      <div className="max-w-3xl mx-auto mt-12 px-4 sm:px-6 lg:px-8">
        <Card className="backdrop-blur-xl bg-white/10 border border-gray-700 shadow-2xl">
          {currentStep === 1 && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-white">设置职位筛选条件</h2>
              <div className="grid grid-cols-1 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-300">职位名称</label>
                  <Input
                    placeholder="例如：前端开发工程师"
                    value={filters.position}
                    onChange={(e) => setFilters({ ...filters, position: e.target.value })}
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300">工作地点</label>
                  <Input
                    placeholder="例如：上海"
                    value={filters.location}
                    onChange={(e) => setFilters({ ...filters, location: e.target.value })}
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300">工作经验</label>
                  <Select
                    className="w-full mt-1"
                    value={filters.experience}
                    onChange={(value) => setFilters({ ...filters, experience: value })}
                    options={[
                      { value: '', label: '不限' },
                      { value: '0-3', label: '0-3年' },
                      { value: '3-5', label: '3-5年' },
                      { value: '5-10', label: '5-10年' },
                      { value: '10+', label: '10年以上' },
                    ]}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300">薪资范围</label>
                  <Select
                    className="w-full mt-1"
                    value={filters.salary}
                    onChange={(value) => setFilters({ ...filters, salary: value })}
                    options={[
                      { value: '', label: '不限' },
                      { value: '0-10', label: '0-10k' },
                      { value: '10-20', label: '10-20k' },
                      { value: '20-35', label: '20-35k' },
                      { value: '35-50', label: '35-50k' },
                      { value: '50+', label: '50k以上' },
                    ]}
                  />
                </div>
              </div>
            </div>
          )}

          {currentStep === 2 && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-white">上传个人简历</h2>
              <AntUpload.Dragger {...uploadProps} className="bg-white/5 border-gray-700 hover:bg-white/10">
                <p className="text-4xl text-blue-400">
                  <Upload className="mx-auto" />
                </p>
                <p className="text-gray-300">点击或拖拽文件到此处上传</p>
                <p className="text-gray-400 text-sm">支持 PDF、Word 格式</p>
              </AntUpload.Dragger>
            </div>
          )}

          {currentStep === 3 && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-white">职位分析报告</h2>
              <div className="space-y-4">
                <Card className="bg-white/5 border-gray-700">
                  <h3 className="font-medium text-white mb-4">技能需求分析</h3>
                  <div className="space-y-6">
                    <div>
                      <div className="flex justify-between text-gray-300 mb-2">
                        <span>React</span>
                        <span>85%</span>
                      </div>
                      <Progress percent={85} strokeColor={{ from: '#108ee9', to: '#87d068' }} />
                    </div>
                    <div>
                      <div className="flex justify-between text-gray-300 mb-2">
                        <span>TypeScript</span>
                        <span>75%</span>
                      </div>
                      <Progress percent={75} strokeColor={{ from: '#108ee9', to: '#87d068' }} />
                    </div>
                  </div>
                </Card>
              </div>
            </div>
          )}

          {currentStep === 4 && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-white">简历优化建议</h2>
              <div className="space-y-4">
                <Card className="bg-green-900/20 border-green-700">
                  <h3 className="font-medium text-green-400">匹配优势</h3>
                  <div className="mt-4 space-y-2">
                    <Tag color="success">React 技术栈经验丰富</Tag>
                    <Tag color="success">具备前端工程化经验</Tag>
                  </div>
                </Card>
                <Card className="bg-yellow-900/20 border-yellow-700">
                  <h3 className="font-medium text-yellow-400">建议提升</h3>
                  <div className="mt-4 space-y-2">
                    <Tag color="warning">补充 TypeScript 项目经验</Tag>
                    <Tag color="warning">增加性能优化相关内容</Tag>
                  </div>
                </Card>
              </div>
            </div>
          )}

          {currentStep === 5 && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-white">下载优化结果</h2>
              <div className="space-y-4">
                <Button
                  type="primary"
                  icon={<FileText className="w-5 h-5" />}
                  className="w-full h-auto py-2 flex items-center justify-center bg-gradient-to-r from-blue-500 to-blue-600"
                >
                  下载职位分析报告
                </Button>
                <Button
                  type="primary"
                  icon={<Download className="w-5 h-5" />}
                  className="w-full h-auto py-2 flex items-center justify-center bg-gradient-to-r from-green-500 to-green-600"
                >
                  下载优化后的简历
                </Button>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="mt-8 flex justify-between">
            <Button
              onClick={handlePrevious}
              disabled={currentStep === 1}
              icon={<ChevronLeft className="w-4 h-4" />}
              className={`${currentStep === 1 ? 'opacity-50' : ''}`}
            >
              上一步
            </Button>
            <Button
              onClick={handleNext}
              disabled={currentStep === steps.length}
              type="primary"
              className={`${currentStep === steps.length ? 'opacity-50' : ''}`}
            >
              {currentStep === steps.length ? '完成' : (
                <span className="flex items-center">
                  下一步
                  <ChevronRight className="w-4 h-4" />
                </span>
              )}
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
};

// 应用路由
function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainApp />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

export default App;