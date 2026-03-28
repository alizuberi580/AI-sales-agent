/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f4ff',
          100: '#e0e9ff',
          500: '#4f7cff',
          600: '#3d6bff',
          700: '#2b5aff',
          900: '#1a3abf',
        }
      }
    }
  },
  plugins: []
}
