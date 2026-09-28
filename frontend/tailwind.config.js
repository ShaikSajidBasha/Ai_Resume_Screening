/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: '#0F1B2D',
          800: '#16233A',
          700: '#1D2E48',
        },
        paper: '#F7F5F0',
        signal: {
          DEFAULT: '#E8A33D',
          dark: '#C77F1F',
        },
        teal: {
          DEFAULT: '#0E7C7B',
          light: '#DCEFEE',
        },
        slate: {
          650: '#4B5768',
        },
        danger: '#B3452C',
      },
      fontFamily: {
        display: ['"Fraunces"', 'Georgia', 'serif'],
        sans: ['"Inter"', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        sm: '4px',
        md: '8px',
      },
    },
  },
  plugins: [],
}
