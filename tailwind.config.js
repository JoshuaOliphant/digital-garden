// tailwind.config.js

module.exports = {
  darkMode: "class", // Enables class-based dark mode
  content: [
    "./app/templates/**/*.html",
    "./app/pages/**/*.md",
    "./app/static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#1a202c",
        secondary: "#2d3748",
        accent: "#38b2ac",
        // Additional custom colors can be added here
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        serif: ["Merriweather", "serif"],
      },
      // Additional customizations like spacing, borders, etc.
    },
  },
  plugins: [
    require("@tailwindcss/typography"),
    // Add other plugins if needed
  ],
};