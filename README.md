# AI简历优化与职位匹配系统

基于人工智能的简历优化与职位匹配系统，帮助求职者提升简历质量并高效找到合适职位。

## 项目功能

1. **智能简历分析**：利用OpenAI API实时解析简历内容，评估质量和有效性
2. **简历优化建议**：基于大模型生成针对性的优化建议，提升简历质量
3. **职位匹配**：实时分析简历与职位匹配度，找出优势和不足
4. **职位搜索**：智能搜索合适的职位并推荐
5. **求职信生成**：基于简历和职位自动生成定制化求职信
6. **申请跟踪**：集中管理所有投递申请状态

## 技术栈

### 前端

- React + TypeScript
- Vite
- Ant Design
- TailwindCSS
- Axios
- Lucide React (图标库)

### 后端

- Python + FastAPI
- Pydantic v2
- MongoDB (使用Motor异步驱动)
- JWT认证
- Firecrawl API: 高效网页爬取和内容提取

### AI/ML

- OpenAI API (GPT-4o)
- OpenAI Agents SDK
- 自然语言处理
- 文档解析技术

## 项目结构

```
ai-resume-helper/
├── client/                      # 前端代码（React + Vite应用）
│   ├── src/                     # 源代码
│   │   ├── components/          # 组件
│   │   ├── pages/               # 页面
│   │   ├── services/            # API服务
│   │   ├── utils/               # 工具函数
│   │   ├── App.tsx              # 应用入口
│   │   └── main.tsx             # 主入口
│   ├── public/                  # 静态资源
│   ├── package.json             # 依赖配置
│   └── vite.config.ts           # Vite配置
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
│   │   ├── agent_service.py     # AI代理服务
│   │   └── agents/              # AI代理实现
│   │       ├── resume_agent.py  # 简历分析和优化代理
│   │       └── job_agent.py     # 职位分析和匹配代理
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
- Node.js 18+
- MongoDB
- OpenAI API密钥
- Firecrawl API密钥

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

3. 配置后端环境变量

创建`.env`文件并设置以下变量：

```makefile
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=ai_resume_helper
SECRET_KEY=your_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=30
OPENAI_API_KEY=your_openai_api_key  # OpenAI API密钥
AI_MODEL=gpt-4o  # 使用的OpenAI模型
JOB_SEARCH_API_KEY=your_job_search_api_key
FIRECRAWL_API_KEY=fc-your_firecrawl_api_key  # 用于网页爬取的Firecrawl API密钥
```

4. 安装前端依赖

```bash
cd client
npm install
```

5. 配置前端环境变量

创建`.env`文件并设置以下变量：

```makefile
VITE_API_BASE_URL=http://localhost:8000/api
VITE_APP_TITLE=智能职位分析与简历优化系统
```

6. 启动服务

**启动后端:**

```bash
cd server
uvicorn main:app --reload --port 8000
```

**启动前端:**

```bash
cd client
npm run dev
```

7. 访问应用

打开浏览器，访问 [http://localhost:3000](http://localhost:3000)

## 获取API密钥

### OpenAI API密钥

1. 访问 [OpenAI平台](https://platform.openai.com/)
2. 注册或登录账号
3. 在API部分创建新的API密钥

### Firecrawl API密钥

1. 访问 [Firecrawl官网](https://firecrawl.dev)
2. 注册或登录账号
3. 在开发者控制台创建新的API密钥
4. 密钥格式应为"fc-"开头

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

- **实时AI处理**：使用OpenAI API进行实时简历分析和优化
- **异步API**：使用FastAPI的异步特性，提高并发性能
- **强类型验证**：使用Pydantic v2进行请求和响应验证
- **标准化响应**：统一的API响应格式
- **依赖注入**：使用FastAPI的依赖注入系统
- **JWT认证**：安全的基于令牌的认证
- **异常处理**：全局异常处理和详细错误信息
- **OpenAPI文档**：自动生成的API文档
- **Firecrawl集成**：高效网页爬取和内容提取
- **现代UI设计**：深色主题，渐变色，响应式设计

## 安全性

本项目重视安全性，定期更新依赖项以修复已知的安全漏洞。最近的安全更新包括：

- 更新了python-multipart到0.0.7+版本
- 更新了bcrypt到4.1.0+版本
- 更新了PyJWT到2.8.0+版本
- 更新了OpenAI SDK到1.0.0+版本
- 更新了Pillow到10.0.0+版本

如果发现任何安全问题，请通过创建Issue报告。

## 贡献指南

欢迎贡献代码、报告问题或提出改进建议。请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交变更 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

MIT License
