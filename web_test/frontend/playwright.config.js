import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  outputDir: "../output/playwright/test-results",
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:5173",
    headless: true,
    launchOptions: {
      slowMo: process.env.DEMO_MODE ? 900 : 0,
    },
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "python3 ../backend/app.py",
      url: "http://127.0.0.1:5000/api/health",
      reuseExistingServer: true,
    },
    {
      command: "npm run dev",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: true,
    },
  ],
});
