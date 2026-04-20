/** @type {import('postcss-load-config').Config} */
export default {
  plugins: {
    // TailwindCSS is loaded as a PostCSS plugin
    tailwindcss: {},
    // Autoprefixer adds vendor prefixes (e.g., -webkit-, -moz-) for cross-browser compatibility
    autoprefixer: {},
  },
};