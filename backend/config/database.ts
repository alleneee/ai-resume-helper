import mongoose from 'mongoose';
import { logger } from '../utils/logger';

// MongoDB连接URL
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/resume-helper';

// 连接配置选项
const options = {
    useNewUrlParser: true,
    useUnifiedTopology: true,
    autoIndex: true, // 开发环境建议开启，生产环境可以考虑关闭以提高性能
    serverSelectionTimeoutMS: 5000, // 超时时间
    socketTimeoutMS: 45000, // 超时时间
};

// 连接到MongoDB
export const connectToDatabase = async (): Promise<typeof mongoose> => {
    try {
        logger.info('正在连接到MongoDB...');

        // 连接数据库
        const connection = await mongoose.connect(MONGODB_URI);

        logger.info('成功连接到MongoDB', {
            host: connection.connection.host,
            port: connection.connection.port,
            name: connection.connection.name
        });

        // 设置连接事件监听器
        setupConnectionListeners();

        return connection;
    } catch (error) {
        logger.error('连接MongoDB失败', error);
        process.exit(1); // 如果无法连接数据库，终止应用程序
    }
};

// 设置连接事件监听器
const setupConnectionListeners = () => {
    const db = mongoose.connection;

    // 处理连接错误
    db.on('error', (err) => {
        logger.error('MongoDB连接错误', err);
    });

    // 处理连接关闭
    db.on('disconnected', () => {
        logger.warn('与MongoDB的连接已断开，尝试重新连接...');
        setTimeout(() => connectToDatabase(), 5000);
    });

    // 处理进程终止
    process.on('SIGINT', async () => {
        await db.close();
        logger.info('MongoDB连接已关闭');
        process.exit(0);
    });
};

// 导出连接实例
export default { connectToDatabase }; 