# 智能职位分析与简历优化系统 - 前端

这是智能职位分析与简历优化系统的前端部分，基于React + Vite + TypeScript开发。

## 技术栈

- React 18
- TypeScript
- Vite
- Ant Design
- TailwindCSS
- Axios
- React Router

## 功能特性

- 用户认证（登录/注册）
- 简历上传和管理
- 职位筛选和搜索
- 简历与职位匹配分析
- 简历优化建议
- 下载优化后的简历

## 安装与运行

### 前提条件

- Node.js (推荐使用v18+)
- npm或yarn

### 安装步骤

1. 克隆仓库（如果尚未克隆）：

   ```
   git clone <repository-url>
   cd Ai-Resume-Helper/client
   ```

2. 安装依赖：

   ```
   npm install
   # 或者
   yarn
   ```

3. 创建环境变量文件：

   ```
   cp .env.example .env
   ```

   并根据需要编辑.env文件。

4. 启动开发服务器：

   ```
   npm run dev
   # 或者
   yarn dev
   ```

5. 访问应用：
   打开浏览器，访问 [http://localhost:3000](http://localhost:3000)

## 构建生产版本

```
npm run build
# 或者
yarn build
```

构建后的文件将位于`dist`目录中。

## 与后端集成

前端应用默认会将/api路径的请求代理到后端服务器。确保在开发时后端服务器运行在正确的端口上（默认为8000）。

## 联系方式

如有问题或建议，请联系项目维护者。
