/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#FDF2F4',
          100: '#FCE4E8',
          200: '#F9C5CE',
          300: '#F39DAE',
          400: '#E8637D',
          500: '#D63B55',
          600: '#B91C3A',
          700: '#9B1830',
          800: '#7C1426',
          900: '#5C0F1E',
        },
        warmgray: {
          50:  '#FAF9F7',
          100: '#F3F1EE',
          200: '#E8E5E0',
          300: '#D4CFC8',
          400: '#A39E96',
          500: '#78736C',
          600: '#5C5750',
          700: '#3D3935',
          800: '#252320',
          900: '#1A1816',
        },
        sidebar: {
          bg:     '#1A0A10',
          border: '#2D1520',
          hover:  '#3D1F2E',
          active: '#8B1A2B',
        },
      }
    }
  },
  plugins: [],
}
