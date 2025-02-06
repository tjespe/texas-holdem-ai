import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 80,
    host: true,
    allowedHosts: ["tords-m1.local"],
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, ""), // Optional path rewrite
      },
      "/ws": {
        target: "ws://127.0.0.1:8000",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
