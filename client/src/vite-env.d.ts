/// <reference types="vite/client" />

// 防止File接口冲突
interface CustomFile extends File {
    // 扩展File接口，不重新定义原始File
}

// React组件声明
declare namespace JSX {
    interface IntrinsicElements {
        [elemName: string]: any;
    }
}
