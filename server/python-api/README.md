# AI简历助手 - Python API服务

这是AI简历助手系统的Python后端API服务，提供简历分析、职位搜索和匹配评估服务。

## 功能特点

- **简历解析与分析**：支持PDF、DOCX、DOC和TXT格式的简历解析，提取核心技能、经验总结、优势分析等
- **职位爬取与分析**：从招聘网站抓取职位信息，分析薪资范围、技能需求和市场趋势
- **匹配度评估**：评估简历与特定职位的匹配程度，识别匹配技能和缺失技能
- **简历优化建议**：提供针对性的简历优化建议，包括内容改进和关键词优化
- **市场趋势分析**：分析特定职位的市场需求、薪资趋势和竞争程度

## 技术架构

- 基于FastAPI框架开发的高性能异步API
- 采用Agent架构设计的智能服务组件
- 使用OpenAI API进行深度文本分析和内容生成
- 采用异步任务处理长时间运行的分析任务

## 系统要求

- Python 3.9+
- 依赖库：详见requirements.txt

## 快速开始

1. 克隆仓库
2. 安装依赖：

```bash
pip install -r server/python-api/requirements.txt
```

3. 配置环境变量：
创建.env文件，设置以下变量：

```
OPENAI_API_KEY=your_openai_api_key
FIRECRAWL_API_KEY=your_firecrawl_api_key
OPENAI_MODEL=gpt-4o
```

4. 启动服务：

```bash
cd server/python-api
python main.py
```

5. 访问API文档：<http://localhost:8000/docs>

## API接口

### 简历管理

- `POST /resume/upload` - 上传并分析简历
- `GET /resume/{resume_id}/analysis` - 获取简历分析结果
- `POST /resume/optimize` - 获取简历优化建议
- `POST /resume/match` - 评估简历与职位的匹配度

### 职位搜索

- `POST /jobs/search` - 搜索职位信息

### 市场分析

- `POST /market/trend` - 分析职位市场趋势

## 项目结构

```
server/python-api/
├── agents/                  # 智能代理组件
│   ├── __init__.py
│   ├── config.py            # 配置和数据模型
│   ├── resume_analyzer_agent.py  # 简历分析代理
│   ├── job_crawler_agent.py      # 职位爬取代理
│   └── coordinator_agent.py      # 协调代理
├── openai_agents/           # OpenAI代理基础框架
│   └── __init__.py
├── main.py                  # 主应用入口
├── requirements.txt         # 依赖库
└── README.md                # 项目文档
```
