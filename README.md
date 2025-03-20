# AI简历助手

AI简历助手是一个智能简历上传与优化系统，帮助求职者分析和优化简历，提高求职成功率。

## 功能特点

- **智能解析**：自动提取简历中的关键信息，包括技能、经验、教育背景等
- **深入分析**：针对简历内容进行全面评估，找出优势和不足
- **优化建议**：提供专业的改进建议，帮助打造更具竞争力的简历
- **多种格式支持**：支持PDF、Word、图片等多种格式的简历文件
- **数据安全**：严格的隐私保护措施，确保个人信息安全

## 技术栈

### 前端

- Next.js 14 (App Router)
- React
- TypeScript
- Tailwind CSS
- Shadcn/UI 组件库

### 后端

- Express.js
- TypeScript
- MongoDB
- Mongoose
- JWT认证
- Multer文件上传

### AI/ML

- OpenAI GPT模型
- 自然语言处理
- 文本提取和解析

## 项目结构

```
ai-resume-helper/
├── frontend/            # 前端代码
│   ├── app/             # Next.js应用路由
│   ├── components/      # React组件
│   ├── hooks/           # 自定义Hooks
│   ├── lib/             # 工具函数和库
│   └── public/          # 静态资源
│
├── backend/             # 后端代码
│   ├── config/          # 配置文件
│   ├── controllers/     # 控制器
│   ├── middleware/      # 中间件
│   ├── models/          # 数据模型
│   ├── routes/          # 路由
│   ├── services/        # 服务层
│   └── utils/           # 工具函数
│
└── uploads/             # 上传文件存储目录
```

## 快速开始

### 前端

```bash
cd frontend
npm install
npm run dev
```

### 后端

```bash
cd backend
npm install
# 创建.env文件（可以复制.env.example并修改）
cp .env.example .env
npm run dev
```

## API文档

### 简历API

| 端点                     | 方法   | 描述              | 权限     |
|--------------------------|--------|-------------------|----------|
| `/api/resume/upload`     | POST   | 上传简历          | 用户     |
| `/api/resume/list`       | GET    | 获取简历列表      | 用户     |
| `/api/resume/:id`        | GET    | 获取简历详情      | 用户     |
| `/api/resume/:id/download`| GET   | 下载简历文件      | 用户     |
| `/api/resume/:id`        | DELETE | 删除简历          | 用户     |

## 贡献指南

欢迎贡献代码、提交问题或建议。请遵循以下步骤：

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 许可证

[MIT](LICENSE)

## 联系方式

项目维护者 - [您的名字](mailto:your.email@example.com)
