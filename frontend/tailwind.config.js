/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'foundit-orange': '#f04e23',
        'foundit-navy': '#1a1a2e',
        'foundit-gray': '#f5f5f5',
      },
    },
  },
  plugins: [],
}
