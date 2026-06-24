/** @type {import('tailwindcss').Config} */
export default {
  // The 'content' array tells Tailwind where your classes are used (crucial for tree-shaking/optimization)
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // You can add custom colors, fonts, spacing, etc., here later
    },
  },
  // Ensure we use the shadcn/ui approach for custom animations and components
  plugins: [],
}