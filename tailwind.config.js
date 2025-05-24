/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/static/src/**/*.{js,jsx,ts,tsx}",
    "./app/templates/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        // Healthcare color palette
        primary: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          500: '#14b8a6', // teal-500
          600: '#0d9488', // teal-600
          700: '#0f766e', // teal-700
        },
        success: {
          50: '#f0fdf4',
          500: '#22c55e',
          600: '#16a34a',
        },
        warning: {
          50: '#fffbeb',
          500: '#f59e0b',
          600: '#d97706',
        },
        error: {
          50: '#fef2f2',
          500: '#ef4444',
          600: '#dc2626',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'soft': '0 2px 15px -3px rgba(0, 0, 0, 0.07), 0 10px 20px -2px rgba(0, 0, 0, 0.04)',
      }
    },
  },
  plugins: [],
}