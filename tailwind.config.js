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
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        serif: ["Merriweather", "serif"],
      },
      typography: {
        DEFAULT: {
          css: {
            blockquote: {
              borderLeftWidth: "4px",
              borderLeftColor: "#cccccc",
              paddingLeft: "1rem",
              fontStyle: "italic",
              color: "#555555",
            },
          },
        },
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
