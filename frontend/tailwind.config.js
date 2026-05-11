export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      keyframes: {
        slideUp: { from: { transform: 'translateY(100%)' }, to: { transform: 'translateY(0)' } },
        fadeIn:  { from: { opacity: 0 },                   to: { opacity: 1 } },
      },
      animation: {
        'slide-up': 'slideUp 0.35s ease-out',
        'fade-in':  'fadeIn 0.2s ease-out',
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
}
