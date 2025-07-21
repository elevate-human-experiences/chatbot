/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: ["./src/**/*.{js,ts,jsx,tsx}", "./index.html"],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#78716c", // stone-500
          foreground: "#f5f5f4", // stone-100
        },
        background: {
          DEFAULT: "#f5f5f4", // stone-100
        },
        border: {
          DEFAULT: "#d6d3d1", // stone-300
        },
        accent: {
          DEFAULT: "#a8a29e", // stone-400
        },
      },
    },
  },
  plugins: [],
};
