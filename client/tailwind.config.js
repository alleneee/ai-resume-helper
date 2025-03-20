/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./app/**/*.{js,ts,jsx,tsx,mdx}",
        "./components/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    DEFAULT: "#3b82f6",
                    dark: "#2563eb",
                    light: "#60a5fa",
                },
                secondary: {
                    DEFAULT: "#a855f7",
                    dark: "#9333ea",
                    light: "#c084fc",
                },
            },
        },
    },
    plugins: [],
};
