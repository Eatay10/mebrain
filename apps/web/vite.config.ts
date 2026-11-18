import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // Yerel API; paralel çalışma için CTH_API_PROXY ile değiştirilebilir (örn. http://localhost:8100).
    proxy: { "/api": { target: process.env.CTH_API_PROXY ?? "http://localhost:8000", changeOrigin: false } },
  },
  build: { sourcemap: false, chunkSizeWarningLimit: 900 },
});
