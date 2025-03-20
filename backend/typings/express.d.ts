import 'express';

declare global {
    namespace Express {
        export interface Request {
            user?: {
                id: string;
                email: string;
                role: string;
                [key: string]: any;
            };
            startTime?: number;
        }
    }
} 