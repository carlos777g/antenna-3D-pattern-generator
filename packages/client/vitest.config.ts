import { defineConfig } from "vitest/config";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  test: {
    // The pure core modules need no DOM; SceneManager is not unit tested
    // because it requires a GPU.
    environment: "node",
    include: ["tests/**/*.test.ts"],
  },
});
