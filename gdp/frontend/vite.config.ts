import react from "@vitejs/plugin-react";
import fs from "fs";
import path from "path";
import { defineConfig, loadEnv } from "vite";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiUrl = env.VITE_API_URL || "http://localhost:8000";
  const katexVersion = (() => {
    try {
      const katexPkgPath = path.resolve(__dirname, "node_modules/katex/package.json");
      const katexPkg = JSON.parse(fs.readFileSync(katexPkgPath, "utf-8")) as {
        version?: string;
      };
      return katexPkg.version || "0.16.22";
    } catch {
      return "0.16.22";
    }
  })();
  const versionDefine = JSON.stringify(katexVersion);

  return {
    plugins: [react()],
    assetsInclude: ["**/*.csv"],
    define: {
      __VERSION__: versionDefine,
    },
    css: {
      modules: {
        localsConvention: "camelCase",
        generateScopedName: "[name]__[local]__[hash:base64:5]",
      },
      preprocessorOptions: {
        scss: {
          additionalData: `@import "./src/styles/variables.scss";`,
        },
      },
    },
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      host: "0.0.0.0",
      port: 5173,
      proxy: {
        "/api": {
          target: apiUrl,
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path,
        },
      },
    },
    optimizeDeps: {
      include: [
        "diff",
        "@lezer/highlight",
        "@copilotkit/shared",
        "@rc-component/util",
      ],
      esbuildOptions: {
        define: {
          __VERSION__: versionDefine,
        },
      },
    },
  };
});
