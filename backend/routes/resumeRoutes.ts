import express from 'express';
import * as resumeController from '../controllers/resumeController';
import { authenticateToken, requireAuth } from '../middleware/auth';

const router = express.Router();

// 应用验证中间件
router.use(authenticateToken);

// 上传简历
router.post('/upload', requireAuth, resumeController.uploadResume);

// 获取简历列表
router.get('/list', requireAuth, resumeController.getResumes);

// 获取简历详情
router.get('/:id', requireAuth, resumeController.getResumeById);

// 下载简历文件
router.get('/:id/download', requireAuth, resumeController.downloadResume);

// 删除简历
router.delete('/:id', requireAuth, resumeController.deleteResume);

export default router; 