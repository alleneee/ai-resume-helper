import fs from 'fs';
import path from 'path';

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface RequestInfo {
    method: string;
    path: string;
    status: number;
    responseTime: number;
    userAgent?: string;
    ip?: string;
}

class Logger {
    private logDir: string;
    private logFile: string;
    private debugMode: boolean;

    constructor() {
        this.logDir = process.env.LOG_DIR || path.join(process.cwd(), 'logs');
        this.logFile = path.join(this.logDir, 'app.log');
        this.debugMode = process.env.NODE_ENV !== 'production';

        // 确保日志目录存在
        this.ensureLogDir();
    }

    private ensureLogDir(): void {
        if (!fs.existsSync(this.logDir)) {
            fs.mkdirSync(this.logDir, { recursive: true });
        }
    }

    private formatMessage(level: LogLevel, message: string, meta?: any): string {
        const timestamp = new Date().toISOString();
        let logMessage = `[${timestamp}] [${level.toUpperCase()}] ${message}`;

        if (meta) {
            try {
                logMessage += ` ${JSON.stringify(meta)}`;
            } catch (error) {
                logMessage += ` [Meta serialization failed: ${error}]`;
            }
        }

        return logMessage;
    }

    private writeToFile(message: string): void {
        fs.appendFileSync(this.logFile, message + '\n');
    }

    debug(message: string, meta?: any): void {
        if (this.debugMode) {
            const formattedMessage = this.formatMessage('debug', message, meta);
            console.debug(formattedMessage);
            this.writeToFile(formattedMessage);
        }
    }

    info(message: string, meta?: any): void {
        const formattedMessage = this.formatMessage('info', message, meta);
        console.info(formattedMessage);
        this.writeToFile(formattedMessage);
    }

    warn(message: string, meta?: any): void {
        const formattedMessage = this.formatMessage('warn', message, meta);
        console.warn(formattedMessage);
        this.writeToFile(formattedMessage);
    }

    error(message: string, meta?: any): void {
        const formattedMessage = this.formatMessage('error', message, meta);
        console.error(formattedMessage);
        this.writeToFile(formattedMessage);
    }

    // 用于记录API请求信息
    logRequest(req: any, res: any, responseTime: number): void {
        const logData: RequestInfo = {
            method: req.method,
            path: req.path,
            status: res.statusCode,
            responseTime,
            userAgent: req.headers['user-agent'],
            ip: req.ip || req.headers['x-forwarded-for'] || req.connection.remoteAddress
        };

        this.info(`HTTP ${req.method} ${req.path} ${res.statusCode}`, logData);
    }

    // 用于记录错误请求
    logErrorRequest(req: any, error: any): void {
        const logData = {
            method: req.method,
            path: req.path,
            error: error.message,
            stack: this.debugMode ? error.stack : undefined,
            userAgent: req.headers['user-agent'],
            ip: req.ip || req.headers['x-forwarded-for'] || req.connection.remoteAddress
        };

        this.error(`HTTP ${req.method} ${req.path} 失败`, logData);
    }
}

// 导出单例
export const logger = new Logger(); 