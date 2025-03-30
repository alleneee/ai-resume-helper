flowchart TB
    subgraph User["用户操作"]
        A[用户上传简历] --> B[获取职位筛选条件]
    end

    subgraph CacheSystem["缓存系统"]
        C[接收筛选条件] --> D{缓存中是否有匹配数据?}
        D -->|是| E[读取缓存数据]
        D -->|否| F[触发实时爬取]
    end

    subgraph Scraper["爬虫代理"]
        F --> G[使用Playwright访问招聘网站]
        G --> H[应用筛选条件]
        H --> I[爬取职位信息]
        I --> J[数据清洗与结构化]
        J --> K[存储到缓存]
    end

    subgraph Analyzer["分析代理"]
        L[分析用户简历内容] --> M[提取简历关键要素]
        E --> N[分析岗位要求]
        K --> N
        N --> O[对比简历与岗位要求]
        M --> O
        O --> P[生成定制化修改建议]
    end

    subgraph ResumeOptimizer["简历优化代理"]
        P --> Q[根据岗位要求修改简历]
        Q --> R[保持个人风格与特色]
        R --> S[生成优化后的简历]
    end

    subgraph Output["输出结果"]
        S --> T[提供简历预览]
        T --> U[提供下载功能]
    end

    B --> C
    E --> L
    K --> L
    U --> V[收集用户反馈以改进系统]
