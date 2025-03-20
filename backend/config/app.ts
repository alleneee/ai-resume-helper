import path from 'path';
import dotenv from 'dotenv';

// 加载环境变量
dotenv.config();

// 应用配置
export const config = {
    // 服务器配置
    server: {
        port: parseInt(process.env.PORT || '4000', 10),
        host: process.env.HOST || '0.0.0.0',
        env: process.env.NODE_ENV || 'development',
        isProduction: process.env.NODE_ENV === 'production',
        isDevelopment: process.env.NODE_ENV === 'development',
        isTest: process.env.NODE_ENV === 'test',
    },

    // 文件上传配置
    upload: {
        directory: process.env.UPLOAD_DIR || path.join(process.cwd(), 'uploads'),
        maxFileSize: parseInt(process.env.MAX_FILE_SIZE || '10485760', 10), // 10MB
        allowedMimeTypes: [
            'application/pdf', // PDF
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // DOCX
            'application/msword', // DOC
            'text/plain', // TXT
            'image/jpeg', // JPG/JPEG
            'image/png', // PNG
        ],
    },

    // 数据库配置
    database: {
        uri: process.env.MONGODB_URI || 'mongodb://localhost:27017/resume-helper',
        options: {
            useNewUrlParser: true,
            useUnifiedTopology: true,
            autoIndex: true,
        },
    },

    // Redis配置（用于队列和缓存）
    redis: {
        host: process.env.REDIS_HOST || 'localhost',
        port: parseInt(process.env.REDIS_PORT || '6379', 10),
        password: process.env.REDIS_PASSWORD || '',
        db: parseInt(process.env.REDIS_DB || '0', 10),
    },

    // JWT配置
    jwt: {
        secret: process.env.JWT_SECRET || 'your-secret-key-should-be-long-and-secure',
        expiresIn: process.env.JWT_EXPIRES_IN || '24h',
    },

    // 邮件配置
    email: {
        host: process.env.EMAIL_HOST || '',
        port: parseInt(process.env.EMAIL_PORT || '587', 10),
        secure: process.env.EMAIL_SECURE === 'true',
        auth: {
            user: process.env.EMAIL_USER || '',
            pass: process.env.EMAIL_PASS || '',
        },
        from: process.env.EMAIL_FROM || 'noreply@resume-helper.com',
    },

    // API限流配置
    rateLimit: {
        windowMs: parseInt(process.env.RATE_LIMIT_WINDOW || '900000', 10), // 15分钟
        max: parseInt(process.env.RATE_LIMIT_MAX || '100', 10), // 每IP 15分钟内最多100个请求
    },

    // 日志配置
    logging: {
        directory: process.env.LOG_DIR || path.join(process.cwd(), 'logs'),
        level: process.env.LOG_LEVEL || 'info',
    },

    // AI服务配置
    ai: {
        provider: process.env.AI_PROVIDER || 'openai',
        apiKey: process.env.AI_API_KEY || '',
        model: process.env.AI_MODEL || 'gpt-4',
        maxTokens: parseInt(process.env.AI_MAX_TOKENS || '4000', 10),
        temperature: parseFloat(process.env.AI_TEMPERATURE || '0.7'),
    },

    // 前端配置
    client: {
        url: process.env.CLIENT_URL || 'http://localhost:3000',
    },

    // CORS配置
    cors: {
        origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
        credentials: true,
    }
};

export default config; 