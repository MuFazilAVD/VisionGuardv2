/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#121826",
        muted: "#5f6f86",
        line: "#cfd8e6",
        panel: "#fbfcfe",
        canvas: "#edf2f7",
        action: "#2457d6",
        info: "#0f6fae",
        success: "#157347",
        warning: "#b65f00",
        danger: "#bd1e2c",
        accent: "#0f766e"
      },
      boxShadow: {
        soft: "0 8px 22px rgba(18, 24, 38, 0.08)",
        panel: "0 1px 2px rgba(18, 24, 38, 0.07), 0 12px 28px rgba(18, 24, 38, 0.09)",
        lift: "0 14px 34px rgba(18, 24, 38, 0.14)"
      }
    }
  },
  plugins: []
};
