module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/pages/**/*.md",
    "./app/static/**/*.js",
  ],
  theme: {
    // Override default colors with our garden theme
    colors: {
      // Keep transparent and current
      transparent: 'transparent',
      current: 'currentColor',
      
      // Redefine whites and blacks for our theme
      white: '#ffffff',
      black: '#2d3436',
      
      // Redefine grays with our garden palette
      gray: {
        50: '#f8f6f3',    // Our background cream
        100: '#f0ede8',   // Surface alt
        200: '#e5e1db',   // Border color
        300: '#d4c5b9',   // Light earth
        400: '#8b949e',   // Muted text
        500: '#5a6067',   // Secondary text
        600: '#4a5568',   // Slightly darker
        700: '#2d3436',   // Primary text (deep charcoal)
        800: '#1a202c',   // Even darker
        900: '#171923',   // Darkest
      },
      
      // Sage green as primary accent
      emerald: {
        50: '#f0fdf4',
        100: '#dcfce7',
        200: '#bbf7d0',
        300: '#A3B88C',   // Light sage
        400: '#6B8E6B',   // Primary sage
        500: '#6B8E6B',   // Primary sage (main)
        600: '#4a6349',   // Deep sage
        700: '#3f5a3f',
        800: '#365136',
        900: '#2d442d',
      },
      
      // Earth tones
      amber: {
        100: '#D4C5B9',   // Light earth
        200: '#c9b5a6',
        300: '#bea593',
        400: '#b39580',
        500: '#8B7355',   // Earth brown
        600: '#6b5843',   // Deep earth
        700: '#5b4a38',
        800: '#4b3c2d',
        900: '#3b2e22',
      },
      
      // Sky blue
      blue: {
        400: '#5B8FA3',   // Sky blue
        500: '#5B8FA3',
        600: '#4a7a8c',
      },
      
      // Growth stage colors
      green: {
        400: '#84cc16',   // Growing (lime)
        500: '#10b981',   // Evergreen
      },
      yellow: {
        500: '#f59e0b',   // Budding
      },
      stone: {
        400: '#9ca3af',   // Seedling
      },
      
      // Error/success states
      red: {
        500: '#ef4444',
        600: '#dc2626',
      }
    },
    extend: {
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
