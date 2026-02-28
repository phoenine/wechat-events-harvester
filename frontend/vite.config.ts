import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";

function getDevProxyTarget(rawValue: string | undefined): string {
  const value = (rawValue || "").trim();
  if (!value) {
    throw new Error(
      "[vite] Missing DEV_PROXY_TARGET. Please set it in frontend/.env.development, e.g. DEV_PROXY_TARGET=http://localhost:38001"
    );
  }
  try {
    return new URL(value).toString();
  } catch {
    throw new Error(
      `[vite] Invalid DEV_PROXY_TARGET: "${value}". Expected a full URL like http://localhost:38001`
    );
  }
}

export default defineConfig(({ command, mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd(), "");
  const devProxyTarget =
    command === "serve" ? getDevProxyTarget(env.DEV_PROXY_TARGET) : "http://localhost:38001";

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
    // 基础路径配置
    base: command === "serve" ? "/" : "/",
    // 开发服务器配置
    // 构建配置
    build: {
      outDir: "dist",
      emptyOutDir: true,
      assetsDir: "assets",
      // 确保资源路径使用相对路径，适合 Flutter WebView 加载
      rollupOptions: {
        output: {
          manualChunks: undefined,
        },
      },
    },
    server: {
      host: "0.0.0.0",
      port: 3000,
      proxy: {
        "/static": {
          target: devProxyTarget,
          changeOrigin: true,
        },
        "/files": {
          target: devProxyTarget,
          changeOrigin: true,
        },
        "/rss": {
          target: devProxyTarget,
          changeOrigin: true,
        },
        "/feed": {
          target: devProxyTarget,
          changeOrigin: true,
        },
        "/api": {
          target: devProxyTarget,
          changeOrigin: true,
        },
      },
    },
  };
});
