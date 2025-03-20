import dotenv from 'dotenv';

// 加载环境变量
dotenv.config();

const config = {
    // 服务器配置
    port: process.env.PORT || 5000,
    nodeEnv: process.env.NODE_ENV || 'development',

    // 数据库配置
    dbUri: process.env.MONGODB_URI || 'mongodb://localhost:27017/resume-helper',

    // JWT配置
    jwtSecret: process.env.JWT_SECRET || 'your_jwt_secret',
    jwtExpiresIn: process.env.JWT_EXPIRES_IN || '7d',

    // 上传文件配置
    uploadDir: process.env.UPLOAD_DIR || 'uploads/',
    maxFileSize: parseInt(process.env.MAX_FILE_SIZE || '5242880', 10), // 默认5MB

    // API配置
    apiVersion: process.env.API_VERSION || 'v1',
    apiPrefix: process.env.API_PREFIX || '/api',

    // AI服务配置
    pythonApiUrl: process.env.PYTHON_API_URL || 'http://localhost:8000',

    // CORS配置
    corsOrigin: process.env.CORS_ORIGIN || '*',
};

export default config; 