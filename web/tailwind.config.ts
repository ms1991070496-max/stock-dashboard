import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        red: { DEFAULT: "#ef4444" },
        green: { DEFAULT: "#22c55e" },
      },
    },
  },
  plugins: [],
};

export default config;
