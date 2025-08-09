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
      gridTemplateColumns: {
        'main': 'minmax(0, 2fr) minmax(300px, 1fr)',
      },
      typography: {
        DEFAULT: {
          css: {
            maxWidth: 'none',
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
