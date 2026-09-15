/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef4ff',
          100: '#dfeaff',
          200: '#c4d9ff',
          300: '#9bbcff',
          400: '#6c95ff',
          500: '#4d74f2',
          600: '#3558d3',
          700: '#2f47a7',
          800: '#2a3f89',
          900: '#263a73',
        },
        ink: '#0f172a',
        slateSoft: '#f8fafc',
      },
      boxShadow: {
        soft: '0 20px 50px rgba(15, 23, 42, 0.08)',
      },
      borderRadius: {
        xl2: '1.125rem',
      },
    },
  },
  plugins: [],
}
