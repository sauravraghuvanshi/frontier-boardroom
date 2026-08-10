import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

const backendTarget = process.env.BACKEND_PROXY_TARGET;
const proxy = backendTarget
  ? {
      "/api": { target: backendTarget, changeOrigin: true, secure: true },
      "/dev": { target: backendTarget, changeOrigin: true, secure: true },
      "/health": { target: backendTarget, changeOrigin: true, secure: true },
      "/ws": {
        target: backendTarget,
        changeOrigin: true,
        secure: true,
        ws: true,
      },
    }
  : undefined;

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  server: { host: "0.0.0.0", port: 5173, proxy },
  preview: {
    host: "0.0.0.0",
    port: 5173,
    allowedHosts: [".azurewebsites.net", "localhost"],
    proxy,
  },
});
