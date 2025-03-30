#!/usr/bin/env node

// 这个脚本用来启动开发服务器，绕过 File 属性冲突问题
import { createServer } from 'vite';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 设置环境变量
process.env.NODE_OPTIONS = '--no-experimental-global-webcrypto';
// 禁用 Babel 的全局属性重定义
process.env.BABEL_DISABLE_CACHE = '1';

async function startServer() {
    try {
        // 创建 Vite 服务器
        const server = await createServer({
            // 强制使用配置文件
            configFile: resolve(__dirname, 'vite.config.ts'),
            root: __dirname,
            server: {
                port: 3000
            }
        });

        // 启动服务器
        await server.listen();

        // 输出服务器地址
        server.printUrls();
    } catch (err) {
        console.error('Error starting Vite server:', err);
        process.exit(1);
    }
}

startServer(); 