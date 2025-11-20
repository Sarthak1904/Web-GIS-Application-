/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['IBM Plex Sans', 'system-ui', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace'],
      },
      colors: {
        primary: {
          50: '#e6f4f1',
          100: '#b3e0d4',
          200: '#80ccb7',
          300: '#4db89a',
          400: '#1aa47d',
          500: '#007a5e',
          600: '#00624b',
          700: '#004a38',
          800: '#003125',
          900: '#001912',
        },
        slate: {
          850: '#172033',
          950: '#0a0f1a',
        },
      },
    },
  },
  plugins: [],
}
