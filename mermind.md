flowchart TB
    subgraph User["用户操作"]
        A[用户输入筛选条件] --> B[上传个人简历]
    end

    subgraph Scraper["爬虫代理"]
        C[接收用户输入] --> D[构建查询参数]
        D --> E[使用Playwright访问BOSS直聘]
        E --> F[应用筛选条件]
        F --> G[爬取职位列表]
        G --> H[爬取职位详情]
        H --> I[数据清洗与结构化]
        I --> J[存储到MongoDB]
    end

    subgraph Analyzer["分析代理"]
        K[读取爬取的职位数据] --> L[提取职位要求共通点]
        L --> M[关键词频率分析]
        M --> N[技能要求分析]
        N --> O[生成岗位需求报告]
    end

    subgraph ResumeOptimizer["简历优化代理"]
        P[读取用户简历] --> Q[分析简历内容]
        Q --> R[与岗位需求对比]
        O --> R
        R --> S[识别匹配点与差距]
        S --> T[生成优化建议]
        T --> U[自动更新简历内容]
    end

    subgraph Output["输出结果"]
        V[展示岗位分析报告] --> W[提供优化后的简历]
        W --> X[提供下载链接]
    end

    B --> C
    J --> K
    P --> Q
    U --> V