import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: {
      "@site-config": fileURLToPath(new URL("./site.config.ts", import.meta.url)),
      "@": fileURLToPath(new URL("./src", import.meta.url)),
      // Los módulos "server-only" se pueden testear en Node.
      "server-only": fileURLToPath(new URL("./src/test/server-only-stub.ts", import.meta.url)),
    },
  },
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
