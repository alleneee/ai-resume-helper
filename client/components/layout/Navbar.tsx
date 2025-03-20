'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { Button, Dropdown, Avatar, Divider } from 'antd';
import type { MenuProps } from 'antd';
import {
    UserOutlined,
    FileTextOutlined,
    LogoutOutlined,
    SettingOutlined,
    RocketOutlined,
    LoginOutlined,
    HomeOutlined,
    MenuOutlined,
} from '@ant-design/icons';
import { useAuthContext } from '@/contexts/AuthContext';
import { toast } from 'react-hot-toast';

type MenuItem = Required<MenuProps>['items'][number];

const Navbar = () => {
    const router = useRouter();
    const pathname = usePathname();
    const { user, isAuthenticated, logout } = useAuthContext();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    const handleLogout = () => {
        logout();
        toast.success('已退出登录');
        router.push('/login');
    };

    const userMenuItems: MenuItem[] = [
        {
            key: 'profile',
            label: '个人资料',
            icon: <UserOutlined />,
            onClick: () => router.push('/profile'),
        },
        {
            key: 'settings',
            label: '设置',
            icon: <SettingOutlined />,
            onClick: () => router.push('/settings'),
        },
        {
            key: 'divider',
            type: 'divider',
        },
        {
            key: 'logout',
            label: '退出登录',
            icon: <LogoutOutlined />,
            onClick: handleLogout,
        },
    ];

    const navLinks = [
        {
            key: 'home',
            label: '首页',
            path: '/',
            icon: <HomeOutlined />,
        },
        {
            key: 'resumes',
            label: '我的简历',
            path: '/resume',
            icon: <FileTextOutlined />,
            requireAuth: true,
        },
        {
            key: 'agent',
            label: 'AI助手',
            path: '/agent',
            icon: <RocketOutlined />,
            requireAuth: true,
        },
    ];

    // 过滤出当前应该显示的导航链接
    const filteredNavLinks = navLinks.filter(
        (link) => !link.requireAuth || isAuthenticated
    );

    return (
        <nav className="bg-white shadow-sm border-b border-gray-200">
            <div className="container mx-auto px-4">
                <div className="flex items-center justify-between h-16">
                    {/* Logo */}
                    <div className="flex-shrink-0 flex items-center">
                        <Link href="/" className="flex items-center">
                            <RocketOutlined className="text-xl text-blue-600 mr-2" />
                            <span className="text-lg font-bold">AI简历助手</span>
                        </Link>
                    </div>

                    {/* Desktop Navigation */}
                    <div className="hidden md:block">
                        <div className="ml-10 flex items-center space-x-4">
                            {filteredNavLinks.map((link) => (
                                <Link
                                    key={link.key}
                                    href={link.path}
                                    className={`px-3 py-2 rounded-md text-sm font-medium flex items-center ${pathname === link.path
                                        ? 'text-blue-600 bg-blue-50'
                                        : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
                                        }`}
                                >
                                    {link.icon && <span className="mr-1">{link.icon}</span>}
                                    {link.label}
                                </Link>
                            ))}
                        </div>
                    </div>

                    {/* Authentication */}
                    <div className="hidden md:block">
                        {isAuthenticated ? (
                            <Dropdown
                                menu={{ items: userMenuItems }}
                                placement="bottomRight"
                                arrow
                            >
                                <div className="flex items-center cursor-pointer">
                                    <Avatar
                                        size="small"
                                        icon={<UserOutlined />}
                                        className="bg-blue-600"
                                    />
                                    <span className="ml-2 text-sm font-medium text-gray-700">
                                        {user?.name || user?.email || '用户'}
                                    </span>
                                </div>
                            </Dropdown>
                        ) : (
                            <div className="flex space-x-3">
                                <Button
                                    type="text"
                                    icon={<LoginOutlined />}
                                    onClick={() => router.push('/login')}
                                >
                                    登录
                                </Button>
                                <Button
                                    type="primary"
                                    onClick={() => router.push('/register')}
                                >
                                    注册
                                </Button>
                            </div>
                        )}
                    </div>

                    {/* Mobile menu button */}
                    <div className="md:hidden">
                        <Button
                            type="text"
                            icon={<MenuOutlined />}
                            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                            className="inline-flex items-center justify-center"
                        />
                    </div>
                </div>
            </div>

            {/* Mobile Menu */}
            {mobileMenuOpen && (
                <div className="md:hidden">
                    <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
                        {filteredNavLinks.map((link) => (
                            <Link
                                key={link.key}
                                href={link.path}
                                className={`block px-3 py-2 rounded-md text-base font-medium flex items-center ${pathname === link.path
                                    ? 'text-blue-600 bg-blue-50'
                                    : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
                                    }`}
                                onClick={() => setMobileMenuOpen(false)}
                            >
                                {link.icon && <span className="mr-2">{link.icon}</span>}
                                {link.label}
                            </Link>
                        ))}

                        <Divider className="my-2" />

                        {isAuthenticated ? (
                            <>
                                <Link
                                    href="/profile"
                                    className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-blue-600 hover:bg-gray-50 flex items-center"
                                    onClick={() => setMobileMenuOpen(false)}
                                >
                                    <UserOutlined className="mr-2" />
                                    个人资料
                                </Link>
                                <Link
                                    href="/settings"
                                    className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-blue-600 hover:bg-gray-50 flex items-center"
                                    onClick={() => setMobileMenuOpen(false)}
                                >
                                    <SettingOutlined className="mr-2" />
                                    设置
                                </Link>
                                <button
                                    onClick={() => {
                                        handleLogout();
                                        setMobileMenuOpen(false);
                                    }}
                                    className="w-full text-left block px-3 py-2 rounded-md text-base font-medium text-gray-700 hover:text-blue-600 hover:bg-gray-50 flex items-center"
                                >
                                    <LogoutOutlined className="mr-2" />
                                    退出登录
                                </button>
                            </>
                        ) : (
                            <div className="flex flex-col space-y-2 px-3 py-2">
                                <Button
                                    type="primary"
                                    icon={<LoginOutlined />}
                                    onClick={() => {
                                        router.push('/login');
                                        setMobileMenuOpen(false);
                                    }}
                                    block
                                >
                                    登录
                                </Button>
                                <Button
                                    onClick={() => {
                                        router.push('/register');
                                        setMobileMenuOpen(false);
                                    }}
                                    block
                                >
                                    注册
                                </Button>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </nav>
    );
};

export default Navbar;