import { defineConfig } from "vite";
import { resolve } from "path";
import react from "@vitejs/plugin-react"; 

export default defineConfig({
    root: resolve("./app/static/src"),
    base: "/static/",
    plugins: [
        react({
            fastRefresh: false,
            jsxImportSource: 'react'
        })
    ],
    resolve: {
        alias: {
            '@': resolve('./app/static/src')
        }
    },
    server: {
        hmr: false
    },
    build: {
        outDir: resolve("./app/static/dist"),
        assetsDir: "",
        manifest: "manifest.json",
        emptyOutDir: true,
        rollupOptions: {
            input: resolve("./app/static/src/main.jsx"),
        },
    },
    css: {
        postcss: './postcss.config.js',
    }
});