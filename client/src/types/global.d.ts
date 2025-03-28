// 防止File接口冲突
interface CustomFile extends File {
    // 扩展File接口
}

// 防止其他类型重定义
export { }; 