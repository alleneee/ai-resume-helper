import React, { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function Home() {
    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center py-12 px-4">
            <div className="max-w-md w-full bg-white/10 backdrop-blur-lg border border-gray-700 p-8 rounded-lg shadow-2xl">
                <h1 className="text-3xl font-bold text-white mb-4">智能职位分析与简历优化系统</h1>
                <p className="text-gray-300 mb-6">欢迎使用智能职位分析与简历优化系统。登录或注册以开始使用。</p>
                <div className="flex gap-4">
                    <button
                        className="flex-1 bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded-md transition-colors"
                        onClick={() => window.location.href = '/login'}
                    >
                        登录
                    </button>
                    <button
                        className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded-md transition-colors"
                        onClick={() => window.location.href = '/register'}
                    >
                        注册
                    </button>
                </div>
            </div>
        </div>
    );
}

function Login() {
    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
            <div className="max-w-md w-full bg-white/10 backdrop-blur-lg border border-gray-700 p-8 rounded-lg shadow-2xl">
                <h2 className="text-2xl font-bold text-white mb-6">登录</h2>
                <button
                    className="w-full bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded-md transition-colors"
                    onClick={() => window.location.href = '/'}
                >
                    返回首页
                </button>
            </div>
        </div>
    );
}

function Register() {
    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
            <div className="max-w-md w-full bg-white/10 backdrop-blur-lg border border-gray-700 p-8 rounded-lg shadow-2xl">
                <h2 className="text-2xl font-bold text-white mb-6">注册</h2>
                <button
                    className="w-full bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded-md transition-colors"
                    onClick={() => window.location.href = '/'}
                >
                    返回首页
                </button>
            </div>
        </div>
    );
}

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
            </Routes>
        </BrowserRouter>
    );
}

export default App; 