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
        // Garden-themed dark mode colors
        dark: {
          bg: {
            primary: "#0f1419",    // Deep forest green
            secondary: "#1a1f2e",  // Midnight blue
            surface: "#2a3441",    // Moonlit sage
          },
          text: {
            primary: "#e6f1ff",    // Soft moonlight
            secondary: "#f0f6fc",  // Warm ivory
          },
          accent: {
            primary: "#f7cc47",    // Firefly gold
            secondary: "#c9a7eb",  // Night bloom purple
            tertiary: "#7ce38b",   // Aurora green
          }
        }
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
