import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import path from 'path';
import dotenv from 'dotenv';
import rateLimit from 'express-rate-limit';

import { config } from './config/app';
import { connectToDatabase } from './config/database';
import { logger } from './utils/logger';
import { errorHandler, notFoundHandler, setupUncaughtExceptionHandling } from './middleware/errorHandler';
import { requestLogger } from './middleware/requestLogger';

// 导入路由
import resumeRoutes from './routes/resumeRoutes';

// 加载环境变量
dotenv.config();

// 创建Express应用
const app = express();

// 设置全局中间件
app.use(cors(config.cors));
app.use(helmet());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// 请求日志
if (config.server.isDevelopment) {
    app.use(morgan('dev'));
}
app.use(requestLogger);

// 限制请求速率
const limiter = rateLimit({
    windowMs: config.rateLimit.windowMs,
    max: config.rateLimit.max,
    message: {
        success: false,
        error: {
            code: 'RATE_LIMIT_EXCEEDED',
            message: '请求频率过高，请稍后再试'
        }
    }
});
app.use(limiter);

// 设置静态文件目录
app.use('/static', express.static(path.join(__dirname, 'public')));

// 注册路由
app.use('/api/resume', resumeRoutes);

// 健康检查端点
app.get('/api/health', (req, res) => {
    res.json({
        success: true,
        data: {
            status: 'OK',
            timestamp: new Date(),
            uptime: process.uptime()
        }
    });
});

// 处理404错误
app.use(notFoundHandler);

// 全局错误处理
app.use(errorHandler);

// 设置未捕获异常处理
setupUncaughtExceptionHandling();

// 启动服务器
const startServer = async () => {
    try {
        // 连接到数据库
        await connectToDatabase();

        // 启动HTTP服务器
        const PORT = config.server.port;
        const HOST = config.server.host;

        app.listen(PORT, HOST, () => {
            logger.info(`服务器已启动`, {
                port: PORT,
                host: HOST,
                env: config.server.env,
                nodeVersion: process.version
            });
        });
    } catch (error) {
        logger.error('服务器启动失败', error);
        process.exit(1);
    }
};

// 如果这个文件是直接运行的（不是被导入的），则启动服务器
if (require.main === module) {
    startServer();
}

export default app; 