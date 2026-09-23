/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./src/**/*.{js,jsx,ts,tsx}", "./public/index.html"],
  safelist: [
    "bg-district-a",
    "bg-district-e",
    "bg-district-w",
    "bg-district-x",
    "bg-district-z",
    "bg-level-watch",
    "bg-level-alert",
    "bg-level-emergency",
    "bg-level-critical",
    "bg-level-catastrophic",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["Lalezar", "cursive"],
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        district: {
          a: "#E63946",
          e: "#4CAF3C",
          w: "#FFA055",
          x: "#F4E03A",
          z: "#6EC6E8",
          water: "#BFE3F5",
        },
        level: {
          watch: "#6B7280",
          alert: "#EAB308",
          emergency: "#F97316",
          critical: "#DC2626",
          catastrophic: "#B91C1C",
        },
      },
    },
  },
  plugins: [],
};
