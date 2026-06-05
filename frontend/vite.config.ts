import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const port = Number(env.FRONTEND_PORT || 5173);

  return {
    base: env.VITE_BASE_PATH || "/ui/",
    plugins: [react()],
    server: {
      host: "0.0.0.0",
      port,
    },
    preview: {
      host: "0.0.0.0",
      port,
    },
    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: "./src/test/setup.ts",
    },
  };
});
