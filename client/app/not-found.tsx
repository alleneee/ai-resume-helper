'use client';

import Link from "next/link";
import { Button, Result, Typography } from "antd";
import { HomeOutlined } from "@ant-design/icons";

export default function NotFound() {
    return (
        <div className="min-h-[calc(100vh-120px)] flex items-center justify-center p-4">
            <Result
                status="404"
                title="404"
                subTitle="抱歉，您访问的页面不存在"
                extra={
                    <Link href="/" passHref>
                        <Button type="primary" icon={<HomeOutlined />}>
                            返回首页
                        </Button>
                    </Link>
                }
            />
        </div>
    );
} 