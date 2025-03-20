import express from 'express';
import { agentController } from '../controllers/agentController';
import { authMiddleware } from '../middleware/authMiddleware';

const router = express.Router();

/**
 * @route   POST /api/agent/optimize-resume
 * @desc    优化简历
 * @access  Private
 */
router.post('/optimize-resume', authMiddleware, agentController.optimizeResume);

/**
 * @route   GET /api/agent/jobs
 * @desc    搜索职位列表
 * @access  Private
 */
router.get('/jobs', authMiddleware, agentController.searchJobs);

/**
 * @route   GET /api/agent/jobs/:jobId
 * @desc    获取职位详情
 * @access  Private
 */
router.get('/jobs/:jobId', authMiddleware, agentController.getJobDetails);

/**
 * @route   POST /api/agent/analyze-resume
 * @desc    分析简历与职位匹配度
 * @access  Private
 */
router.post('/analyze-resume', authMiddleware, agentController.analyzeResume);

export default router; 