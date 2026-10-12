import { defineConfig } from "@playwright/test";
const productionProxy = Boolean(process.env.OCTODIG_TEST_NGINX_BIN);

export default defineConfig({
  testDir: "./tests",
  workers: 1,
  projects: [
    { name: "desktop", use: { viewport: { width: 1280, height: 900 } } },
    { name: "mobile", use: { viewport: { width: 390, height: 844 }, isMobile: true } },
  ],
  use: { baseURL: "http://127.0.0.1:5175", browserName: "chromium" },
  webServer: [
    { command: "uv run python ../tests/browser_server.py", url: "http://127.0.0.1:8801/health/live",
      env: { OCTODIG_CORS_ORIGINS: "http://127.0.0.1:5175", OCTODIG_JWT_SECRET: "offline-browser-fixture-secret-32-bytes" }, timeout: 60000 },
    { command: productionProxy ? "uv run python ../tests/proxy_server.py" : "npm run dev -- --host 127.0.0.1 --port 5175 --strictPort",
      url: "http://127.0.0.1:5175", env: { VITE_API_URL: "http://127.0.0.1:8801" }, timeout: 60000 },
  ],
});
