# AI简历优化与一键投递系统

基于人工智能的简历优化与职位匹配系统，帮助求职者提升简历质量并高效找到合适职位。

## 项目功能

- **智能简历分析**：自动解析简历内容，评估质量和有效性
- **简历优化建议**：AI生成针对性的优化建议，提升简历质量
- **职位匹配**：分析简历与职位匹配度，找出优势和不足
- **职位搜索**：智能搜索合适的职位并推荐
- **一键投递**：简化投递流程，提高求职效率
- **申请跟踪**：集中管理所有投递申请状态

## 技术栈

### 前端

- React + TypeScript
- Next.js
- Ant Design
- TailwindCSS

### 后端

- Node.js + Express
- Python + FastAPI
- MongoDB
- Redis

### AI/ML

- OpenAI API
- 自然语言处理
- 文档解析技术

## 项目结构

```
ai-resume-helper/
├── client/                      # 前端代码（Next.js应用）
├── server/                      # 后端代码
│   ├── node-api/                # Node.js/Express API
│   └── python-api/              # Python/FastAPI API
├── uploads/                     # 上传文件存储
├── docker-compose.yml           # Docker Compose配置
└── README.md                    # 项目说明
```

## 安装与运行

### 使用Docker

1. 克隆仓库

```bash
git clone https://github.com/yourusername/ai-resume-helper.git
cd ai-resume-helper
```

2. 构建并启动所有服务

```bash
docker-compose up -d
```

3. 访问应用

- 前端: <http://localhost:3000>
- Node.js API: <http://localhost:5000>
- Python API: <http://localhost:8000/docs>

### 手动安装

#### 前端

```bash
cd client
npm install
npm run dev
```

#### Node.js 后端

```bash
cd server/node-api
npm install
npm run dev
```

#### Python 后端

```bash
cd server/python-api
pip install -r requirements.txt
uvicorn main:app --reload
```

## 贡献指南

欢迎贡献代码、报告问题或提出改进建议。请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交变更 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

MIT License
