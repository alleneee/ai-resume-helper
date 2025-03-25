# AI简历优化与职位匹配系统

基于人工智能的简历优化与职位匹配系统，帮助求职者提升简历质量并高效找到合适职位。

## 项目功能

1. **智能简历分析**：自动解析简历内容，评估质量和有效性
2. **简历优化建议**：AI生成针对性的优化建议，提升简历质量
3. **职位匹配**：分析简历与职位匹配度，找出优势和不足
4. **职位搜索**：智能搜索合适的职位并推荐
5. **求职信生成**：基于简历和职位自动生成定制化求职信
6. **申请跟踪**：集中管理所有投递申请状态

## 技术栈

### 前端

- React + TypeScript
- Next.js
- Ant Design
- TailwindCSS

### 后端

- Python + FastAPI
- Pydantic v2
- MongoDB (使用Motor异步驱动)
- JWT认证

### AI/ML

- OpenAI API (GPT-4)
- 自然语言处理
- 文档解析技术

## 项目结构

```
ai-resume-helper/
├── client/                      # 前端代码（Next.js应用）
├── server/                      # 后端代码（FastAPI应用）
│   ├── api/                     # API路由
│   │   ├── auth.py              # 认证相关API
│   │   ├── resume.py            # 简历管理API
│   │   └── agent.py             # AI代理功能API
│   ├── models/                  # 数据模型
│   │   ├── user.py              # 用户模型
│   │   ├── resume.py            # 简历模型
│   │   ├── agent.py             # 代理模型
│   │   └── database.py          # 数据库连接
│   ├── services/                # 业务逻辑
│   │   └── agent_service.py     # AI代理服务
│   ├── middleware/              # 中间件
│   │   └── auth.py              # 认证中间件
│   ├── utils/                   # 工具函数
│   │   └── response.py          # 响应格式化
│   └── main.py                  # 应用入口
├── uploads/                     # 上传文件存储
├── .env                         # 环境变量
└── README.md                    # 项目说明
```

## 安装与运行

### 前提条件

- Python 3.9+
- MongoDB
- OpenAI API密钥

### 安装步骤

1. 克隆仓库

```bash
git clone https://github.com/yourusername/ai-resume-helper.git
cd ai-resume-helper
```

2. 安装后端依赖

```bash
cd server
pip install -r requirements.txt
```

3. 配置环境变量

创建`.env`文件并设置以下变量：

```makefile
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=ai_resume_helper
SECRET_KEY=your_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=30
AI_API_KEY=your_openai_api_key
AI_MODEL=gpt-4
JOB_SEARCH_API_KEY=your_job_search_api_key
```

4. 启动后端服务

```bash
cd server
uvicorn main:app --reload --port 8000
```

5. 安装并启动前端（可选）

```bash
cd client
npm install
npm run dev
```

## API文档

启动服务后，可以通过以下URL访问API文档：

- Swagger UI: <http://localhost:8000/api/docs>
- ReDoc: <http://localhost:8000/api/redoc>

## 主要API端点

### 认证API

1. `POST /api/register` - 用户注册
2. `POST /api/login` - 用户登录
3. `GET /api/users/me` - 获取当前用户信息

### 简历API

1. `POST /api/resumes` - 上传简历
2. `GET /api/resumes` - 获取用户所有简历
3. `GET /api/resumes/{resume_id}` - 获取特定简历
4. `PUT /api/resumes/{resume_id}` - 更新简历
5. `DELETE /api/resumes/{resume_id}` - 删除简历

### 代理API

1. `POST /api/agent/optimize-resume` - 优化简历
2. `POST /api/agent/match-job` - 职位匹配分析
3. `POST /api/agent/generate-cover-letter` - 生成求职信
4. `POST /api/agent/search-jobs` - 搜索职位

## 技术特点

- **异步API**：使用FastAPI的异步特性，提高并发性能
- **强类型验证**：使用Pydantic v2进行请求和响应验证
- **标准化响应**：统一的API响应格式
- **依赖注入**：使用FastAPI的依赖注入系统
- **JWT认证**：安全的基于令牌的认证
- **异常处理**：全局异常处理和详细错误信息
- **OpenAPI文档**：自动生成的API文档

## 贡献指南

欢迎贡献代码、报告问题或提出改进建议。请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交变更 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

MIT License
